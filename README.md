# StunAssure

> **Prove, cheaply and fail-safe, that each batch of fish was rendered insensible and stayed
> insensible until death.** `simulate → verify → certify → report`.

StunAssure is a **verification stack** for humane fish stunning and slaughter. Instead of "monitor
and report with a camera," it does something falsifiable: **measure the stun physically → verify
insensibility → enforce the recovery window → certify the batch statistically** — and emits a
signed, tamper-evident audit record for each batch.

The verification **core has zero runtime dependencies** (pure Python standard library), so it runs
anywhere — including offline, on the poorest vessel. An optional HTTP API and a cloud reference
architecture are provided for aggregation, dashboards, and certifier exports.

> ⚠️ StunAssure flags welfare **risk** and verifies **process delivery**. It does **not** determine
> consciousness or guarantee humane slaughter. Any `UNCERTAIN` result routes to manual/expert review.

---

## Why this is not "another AI camera"

The dangerous error in welfare is a **false "safe."** The engine never certifies on the absence of
evidence. This fail-safe contract is the whole point of the system — and every rule below is
enforced by a test:

| Rule | Behaviour |
|---|---|
| Missing / un-verifiable input | → **UNCERTAIN** (route to manual check), never PASS |
| stun→bleed interval beyond the species recovery threshold | → **FAIL** (risk of waking before death) |
| Species with **no published electrical-stun spec** (e.g. gilthead sea bream) | → dose **UNCERTAIN**, never a fabricated pass — the field's biggest gap, encoded honestly |
| Aggregation across layers | **conservative** — the worst layer dominates, no averaging |
| Heartbeat / cardiac signal | **rejected** as insensibility evidence — the fish heart is myogenic and beats for minutes after brain death |

---

## The four layers

| Layer | Module | What it verifies |
|---|---|---|
| **Dose** | `engine._check_dose` | field strength × duration vs the cited species spec |
| **Recovery-clock** | `engine._check_recovery_clock` | stun→bleed interval vs species recovery onset / certifier ≤15 s |
| **Echo-Stun** (optional) | `engine._check_evoked_response` | evoked-response suppression (the physiological differentiator) |
| **Welfare-by-Sampling** | `sampling` | ISO 2859-style zero-acceptance (c=0) lot certification at stated confidence |

`species.py` is the **cited** threshold library (salmon recovery onset 44 s [Lambooij 2010];
certifier ≤15 s stun-to-bleed; sea bream electrical spec **absent**, by design). `simulator.py`
generates reproducible synthetic batches with injectable failure modes. `report.py` emits a
SHA-256-signed, tamper-evident batch record — the "stun black box," in software.

See [`docs/architecture.md`](docs/architecture.md) for the full architecture, data flow, and C4 view.

---

## Install

Requires Python ≥ 3.11. With [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv sync                       # core only (zero runtime deps)
uv sync --all-extras          # core + HTTP API + dev tooling
```

Or with pip:

```bash
pip install .                 # core
pip install '.[api]'          # core + HTTP API
```

---

## Quickstart (CLI)

```bash
uv run stunassure species                                                   # the cited threshold library
uv run stunassure demo --species atlantic_salmon --lot 50000 --failure-rate 0.0
uv run stunassure demo --species atlantic_salmon --lot 50000 --failure-rate 0.30   # → LOT REJECTED
uv run stunassure demo --species gilthead_sea_bream --lot 20000                    # → UNCERTAIN (the gap)
uv run stunassure demo --species atlantic_salmon --lot 50000 --out reports/r.json  # signed artifact
```

A clean salmon batch certifies a 50,000-fish lot at **~95% confidence from a 45-fish sample**; a
30%-failure batch is rejected; sea bream returns all-`UNCERTAIN` because dose is un-verifiable.

## Quickstart (HTTP API)

```bash
uv run uvicorn stunassure.api:app --port 8000
# Interactive OpenAPI docs at http://localhost:8000/docs

curl -s localhost:8000/verify -H 'content-type: application/json' -d '{
  "species_key": "atlantic_salmon", "field_strength_v_per_cm": 2.0,
  "stun_duration_s": 2.0, "stun_to_bleed_s": 5.0, "evoked_response_suppressed": true }'
# → {"verdict":"PASS", ...}
```

Full endpoint reference: [`docs/api.md`](docs/api.md).

## Run with Docker

```bash
docker compose up --build      # API on http://localhost:8000
```

---

## Use as a library

```python
from stunassure.engine import StunEvent, verify

result = verify(StunEvent(
    species_key="atlantic_salmon",
    field_strength_v_per_cm=2.0,
    stun_duration_s=2.0,
    stun_to_bleed_s=5.0,
))
print(result.verdict.label)                       # PASS / UNCERTAIN / FAIL
for f in result.findings:
    print(f.layer, f.verdict.label, "-", f.reason)
```

```python
from stunassure.report import build_report, verify_report
from stunassure.simulator import simulate_batch
from stunassure.sampling import design_plan

plan = design_plan(lot_size=50_000, aql=0.065, target_confidence=0.95)
sample = simulate_batch("atlantic_salmon", n=plan.sample_size, seed=1, failure_rate=0.0)
report = build_report("atlantic_salmon", sample, lot_size=50_000, aql=0.065,
                      target_confidence=0.95, generated_at="2026-06-19T12:00:00Z")
assert verify_report(report)                       # SHA-256 signature verifies (tamper-evident)
```

---

## Cloud deployment

StunAssure is **offline-first**: the verdict is computed at the edge by the dependency-free core,
and the cloud tier only aggregates, stores, and exports. Managed reference architectures with
**monthly cost quotes** are provided for both major clouds:

- **Azure** — IoT Hub → Functions → Container Apps + PostgreSQL Flexible Server + Blob Storage.
  Pilot ≈ **$80–130/mo**. See [`docs/deployment/azure.md`](docs/deployment/azure.md).
- **AWS** — IoT Core → Lambda → ECS Fargate + RDS PostgreSQL + S3. Pilot ≈ **$70–120/mo**.
  See [`docs/deployment/aws.md`](docs/deployment/aws.md).

Both docs include the reference diagram, service mapping, an itemized cost table, free/POC-tier
notes, and a production-HA scaling estimate. Figures are indicative list prices — confirm with the
official pricing calculators for your region.

---

## Quality gates

```bash
make check       # tests + coverage + ruff + mypy
# or individually:
uv run pytest --cov=stunassure --cov-report=term-missing   # ≥ 90% coverage
uv run ruff check src tests                                # lint, clean
uv run mypy                                                # strict, clean
```

CI runs the full gate on Python 3.11 / 3.12 / 3.13 (see `.github/workflows/ci.yml`).

---

## Project layout

```
src/stunassure/      the verification core (engine, species, sampling, report, simulator, cli, api)
tests/               test suite (core + optional API)
docs/                architecture, API reference, Azure & AWS deployment + cost quotes
Dockerfile           small, non-root API image
docker-compose.yml   one-command local API
Makefile             dev shortcuts
```

## What this is — and isn't (yet)

- **Is:** an end-to-end, fail-safe verification core — coherent logic, an audit artifact, an
  optional API, and costed cloud deployment paths — provable with **zero hardware and zero live fish**.
- **Isn't (yet):** the ESP32 inline field/conductivity logger firmware + BOM; the contact
  evoked-response ("Echo-Stun") signal-processing module (needs bench data + a welfare advisor); a
  web dashboard. Several species figures are tagged `needs-primary` in `species.py` and must be
  traced to primary sources before any external numeric claim.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The fail-safe contract and the "cite every threshold" rule
are non-negotiable, and the core must stay dependency-free.

## License

Proprietary — Responsible Systems Lab. See [`LICENSE`](LICENSE).
