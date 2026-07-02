# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Web dashboard** (`GET /ui/`) — zero-build, single-file UI over the API: verify one event,
  simulate + certify a batch, verify/tamper-test the signature, download the signed report, and
  browse the species library.
- **`POST /demo`** endpoint — simulate + verify + certify a batch in one call (CLI parity), so the
  dashboard exercises the whole stack with zero hardware.
- **CITATION.cff** — machine-readable software citation.
- **MkDocs Material documentation site** — `mkdocs.yml` + landing page + docs CI workflow (builds
  strict on push; deploys to GitHub Pages on manual dispatch).

## [0.1.0] — 2026-07-02

### Added
- **Verification core** (`stunassure`) — zero-runtime-dependency, fail-safe engine:
  - `engine` — dose · recovery-clock · Echo-Stun layers with conservative aggregation
    (worst layer dominates) and a three-state `Verdict` (PASS / UNCERTAIN / FAIL). Heartbeat
    is rejected as an insensibility signal.
  - `species` — cited species threshold library; missing electrical specs are encoded honestly
    as un-verifiable rather than fabricated.
  - `sampling` — Welfare-by-Sampling: zero-acceptance (c=0) hypergeometric lot certification.
  - `report` — SHA-256-signed, tamper-evident batch report (JSON + Markdown).
  - `simulator` — reproducible synthetic batches with injectable failure modes.
  - `cli` — `stunassure demo` and `stunassure species`.
- **Optional HTTP API** (`stunassure[api]`, FastAPI) — `/health`, `/species`, `/verify`,
  `/reports`, `/reports/verify`.
- Docker image, docker-compose, Makefile, and GitHub Actions CI (pytest + coverage + ruff + mypy).
- Documentation: architecture, API reference, and Azure + AWS deployment reference architectures
  with monthly cost estimates.

[Unreleased]: https://github.com/MSKazemi/stunassure/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/MSKazemi/stunassure/releases/tag/v0.1.0
