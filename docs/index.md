# StunAssure

> **Prove, cheaply and fail-safe, that each batch of fish was rendered insensible and stayed
> insensible until death.** `simulate → verify → certify → report`.

StunAssure is a **verification stack** for humane fish stunning and slaughter. Instead of "monitor
and report with a camera," it does something falsifiable: **measure the stun physically → verify
insensibility → enforce the recovery window → certify the batch statistically** — and emits a
signed, tamper-evident audit record for each batch.

The verification **core has zero runtime dependencies** (pure Python standard library), so it runs
anywhere — including offline, on the poorest vessel. An optional HTTP API and cloud reference
architectures are provided for aggregation, dashboards, and certifier exports.

!!! warning "Scope"
    StunAssure flags welfare **risk** and verifies **process delivery**. It does **not** determine
    consciousness or guarantee humane slaughter. Any `UNCERTAIN` result routes to manual/expert review.

## Why this is not "another AI camera"

The dangerous error in welfare is a **false "safe."** The engine never certifies on the absence of
evidence:

| Rule | Behaviour |
|---|---|
| Missing / un-verifiable input | → **UNCERTAIN** (route to manual check), never PASS |
| stun→bleed interval beyond the species recovery threshold | → **FAIL** (risk of waking before death) |
| Species with **no published electrical-stun spec** | → dose **UNCERTAIN**, never a fabricated pass |
| Aggregation across layers | **conservative** — the worst layer dominates, no averaging |
| Heartbeat / cardiac signal | **rejected** as insensibility evidence (the fish heart is myogenic) |

## The four layers

| Layer | What it verifies |
|---|---|
| **Dose** | field strength × duration vs the cited species spec |
| **Recovery-clock** | stun→bleed interval vs species recovery onset / certifier ≤15 s |
| **Echo-Stun** (optional) | evoked-response suppression (the physiological differentiator) |
| **Welfare-by-Sampling** | ISO 2859-style zero-acceptance (c=0) lot certification at stated confidence |

## Where to next

- [**Architecture**](architecture.md) — the fail-safe contract, the four layers, data flow, C4 view.
- [**HTTP API**](api.md) — the optional FastAPI service and its endpoints.
- [**Deploy on Azure**](deployment/azure.md) — reference architecture + monthly cost quote.
- [**Deploy on AWS**](deployment/aws.md) — reference architecture + monthly cost quote.

## Quickstart

```bash
uv sync                                                          # core only (zero runtime deps)
uv run stunassure species                                       # the cited threshold library
uv run stunassure demo --species atlantic_salmon --lot 50000    # simulate → verify → certify → report
```

Source: [github.com/MSKazemi/stunassure](https://github.com/MSKazemi/stunassure).
