"""StunAssure CLI — run the verification stack end to end.

``stunassure demo`` simulates a batch, verifies each fish (dose + recovery-clock + optional
Echo-Stun), certifies the lot by Welfare-by-Sampling, and prints a signed, tamper-evident
welfare report. Zero hardware, zero live fish — the proposal-ready demonstration of the concept.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from . import species
from .report import build_report, to_json, to_markdown
from .simulator import simulate_batch

_FIXED_DEMO_TIMESTAMP = "2026-06-19T12:00:00Z"


def run_demo(
    species_key: str,
    lot_size: int,
    sample_seed: int,
    failure_rate: float,
    generated_at: str,
    aql: float = 0.065,
    target_confidence: float = 0.95,
) -> dict[str, Any]:
    """Design the sample, simulate it, verify+certify, and return the signed report."""
    from .sampling import design_plan

    plan = design_plan(lot_size, aql, target_confidence)
    sample = simulate_batch(species_key, n=plan.sample_size, seed=sample_seed,
                            failure_rate=failure_rate)
    return build_report(
        species_key=species_key,
        sample_events=sample,
        lot_size=lot_size,
        aql=aql,
        target_confidence=target_confidence,
        generated_at=generated_at,
    )


def _cmd_demo(args: argparse.Namespace) -> int:
    if species.get_profile(args.species) is None:
        print(
            f"error: unknown species '{args.species}'. Known: {', '.join(species.all_keys())}",
            file=sys.stderr,
        )
        return 2
    report = run_demo(
        species_key=args.species,
        lot_size=args.lot,
        sample_seed=args.seed,
        failure_rate=args.failure_rate,
        generated_at=args.timestamp,
        aql=args.aql,
        target_confidence=args.confidence,
    )
    print(to_json(report) if args.json else to_markdown(report))
    if args.out:
        out = Path(args.out)
        out.write_text(to_json(report), encoding="utf-8")
        print(f"\n[written] {out}", file=sys.stderr)
    return 0


def _cmd_species(_args: argparse.Namespace) -> int:
    for key in species.all_keys():
        p = species.get_profile(key)
        assert p is not None
        spec = "published spec" if p.electrical_spec_published else "NO published spec"
        print(
            f"{key:20s} recovery-onset {p.recovery_onset_s:5.0f}s  "
            f"hard-limit {p.hard_recovery_limit_s():5.0f}s  [{spec}]"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stunassure", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="simulate → verify → certify → report")
    demo.add_argument("--species", default="atlantic_salmon")
    demo.add_argument("--lot", type=int, default=10_000, help="production batch size")
    demo.add_argument("--seed", type=int, default=1)
    demo.add_argument("--failure-rate", dest="failure_rate", type=float, default=0.08)
    demo.add_argument("--aql", type=float, default=0.065, help="acceptable quality level")
    demo.add_argument("--confidence", type=float, default=0.95)
    demo.add_argument("--timestamp", default=_FIXED_DEMO_TIMESTAMP)
    demo.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    demo.add_argument("--out", help="also write the JSON report to this path")
    demo.set_defaults(func=_cmd_demo)

    sp = sub.add_parser("species", help="list the species threshold library")
    sp.set_defaults(func=_cmd_species)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    func = args.func
    result: int = func(args)
    return result


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
