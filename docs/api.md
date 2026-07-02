# StunAssure HTTP API

The API is an **optional** service tier over the zero-dependency core. Install and run it only where
you need HTTP (a dashboard, a certifier export, fleet aggregation). The core itself never needs it.

```bash
pip install 'stunassure[api]'
uvicorn stunassure.api:app --port 8000
# Web dashboard:          http://localhost:8000/ui/   (/ redirects here)
# Interactive OpenAPI UI: http://localhost:8000/docs
```

The API is a **transport, not a second decision path** — it calls the same core and cannot weaken
the fail-safe contract.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness probe → `{"status":"ok","version":"…"}` |
| `GET` | `/species` | List the cited species threshold library |
| `GET` | `/species/{key}` | One species profile (incl. sources); `404` if unknown |
| `POST` | `/verify` | Verify a single stun event → `PASS` / `UNCERTAIN` / `FAIL` |
| `POST` | `/reports` | Verify a batch sample + certify the lot → signed report |
| `POST` | `/reports/verify` | Check a report's SHA-256 signature (tamper detection) |
| `POST` | `/demo` | Simulate + verify + certify a batch → signed report (mirrors the CLI demo) |
| `GET` | `/ui/` | The web dashboard (see below); `/` redirects here |

## Web dashboard

Once the API is running, open **<http://localhost:8000/ui/>** (or just `/`, which redirects) for a
zero-build, single-file dashboard that talks to the endpoints above:

- **Verify one event** — a form that shows the fail-safe verdict and every layer's reason,
  colour-coded PASS / UNCERTAIN / FAIL.
- **Certify a batch** — pick a species, lot size, and injected failure rate; it calls `/demo`,
  shows the certification banner + verdict counts, then lets you **verify the signature**, run a
  **tamper test**, and **download the signed JSON**.
- **Species library** — the cited threshold table, flagging species with no published spec.

The dashboard is a client only — it cannot bypass or weaken the verdict, which is always computed
by the core.

## Examples

### Verify one event
```bash
curl -s localhost:8000/verify -H 'content-type: application/json' -d '{
  "species_key": "atlantic_salmon",
  "field_strength_v_per_cm": 2.0,
  "stun_duration_s": 2.0,
  "stun_to_bleed_s": 5.0,
  "evoked_response_suppressed": true
}'
```
```json
{
  "verdict": "PASS",
  "findings": [
    {"layer": "dose", "verdict": "PASS", "reason": "field strength and duration within species spec"},
    {"layer": "recovery_clock", "verdict": "PASS", "reason": "stun→bleed 5s within 15s"},
    {"layer": "evoked_response", "verdict": "PASS", "reason": "no evoked response detected (Echo-Stun)"}
  ]
}
```

A missing field yields `UNCERTAIN` (never a silent pass); an over-long `stun_to_bleed_s` yields
`FAIL`; a species with no published spec (e.g. `gilthead_sea_bream`) yields `UNCERTAIN` on the dose
layer.

### Certify a lot
```bash
curl -s localhost:8000/reports -H 'content-type: application/json' -d '{
  "species_key": "atlantic_salmon",
  "lot_size": 50000,
  "aql": 0.065,
  "target_confidence": 0.95,
  "generated_at": "2026-06-19T12:00:00Z",
  "sample": [ { "species_key": "atlantic_salmon", "field_strength_v_per_cm": 2.0,
               "stun_duration_s": 2.0, "stun_to_bleed_s": 5.0, "sample_id": "S-1" } ]
}'
```
Returns the full signed report. `generated_at` is passed in (never read from the wall clock) so the
signature is reproducible.

### Verify a report signature
```bash
curl -s localhost:8000/reports/verify -H 'content-type: application/json' -d @report.json
# {"valid": true}   — any later edit to the report flips this to false
```
