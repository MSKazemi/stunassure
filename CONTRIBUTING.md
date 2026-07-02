# Contributing to StunAssure

Thanks for helping build a fail-safe fish-welfare verification tool. A few non-negotiables keep
this codebase trustworthy.

## The fail-safe contract is sacred
The dangerous error in welfare is a **false "safe."** Any change must preserve these invariants,
and every one is covered by a test:

1. Missing / un-verifiable input → **UNCERTAIN** (route to manual check), **never PASS**.
2. A recovery-clock breach → **FAIL** (hard).
3. A species with no published electrical spec → dose is **UNCERTAIN**, never a fabricated pass.
4. Layers aggregate **conservatively** — the worst layer dominates (no averaging).
5. **Heartbeat is never accepted** as an insensibility signal (the fish heart is myogenic).

If your change touches aggregation, thresholds, or certification, add a test that would fail if the
invariant were violated.

## Evidence, not rumors
Every welfare number in `species.py` must be traceable to a source. A number without a source is a
rumor. If you cannot cite it, mark it `needs-primary` and do not use it for any external claim.

## The core stays dependency-free
`stunassure` (the core) must have **zero runtime dependencies** — it has to run offline on the
poorest vessel. New third-party dependencies belong only in optional extras (e.g. `[api]`), never
in the core import path.

## Development

```bash
uv sync --all-extras          # install core + api + dev tooling
uv run pytest --cov=stunassure --cov-report=term-missing   # tests + coverage (keep ≥ 90%)
uv run ruff check src tests   # lint
uv run mypy                   # strict type-check
```

Or use the Makefile: `make check`.

## Commit style
Use clear, imperative messages describing the *why*. Keep commits focused.
