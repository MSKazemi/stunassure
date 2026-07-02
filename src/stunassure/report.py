"""Signed batch report — the audit-ready, tamper-evident welfare record.

Turns a verified sample + a sampling decision into a structured report carrying a SHA-256
signature over its canonical content, so any later edit is detectable (the "stun black box"
idea, in software). Deterministic: the timestamp is passed in, never read from the wall clock,
so the same inputs always produce the same signature.

Fail-safe certification rule: a lot is certified only if **every sampled fish positively
PASSED**. An UNCERTAIN counts as a sample defect (route to manual check) — we never certify on
absence of evidence.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

from .engine import StunEvent, Verdict, verify
from .sampling import design_plan, evaluate

_SIGNATURE_KEY = "signature"
_GENERATOR = "StunAssure/0.1.0"


def _canonical(body: dict[str, Any]) -> str:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sign(body: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()


def build_report(
    species_key: str,
    sample_events: list[StunEvent],
    lot_size: int,
    aql: float,
    target_confidence: float,
    generated_at: str,
    generator: str = _GENERATOR,
) -> dict[str, Any]:
    """Verify a sample, certify the lot, and return a signed report dict."""
    from . import species as species_mod

    profile = species_mod.get_profile(species_key)
    common_name = profile.common_name if profile else species_key

    results = [verify(e) for e in sample_events]
    counts = Counter(r.verdict for r in results)
    pass_n = counts.get(Verdict.PASS, 0)
    uncertain_n = counts.get(Verdict.UNCERTAIN, 0)
    fail_n = counts.get(Verdict.FAIL, 0)

    # Fail-safe: anything not positively PASS is a sample defect for certification.
    observed_defects = len(sample_events) - pass_n
    plan = design_plan(lot_size, aql, target_confidence)
    decision = evaluate(plan, observed_defects)

    events_block = [
        {
            "sample_id": e.sample_id,
            "verdict": r.verdict.label,
            "findings": [
                {"layer": f.layer, "verdict": f.verdict.label, "reason": f.reason}
                for f in r.findings
            ],
        }
        for e, r in zip(sample_events, results, strict=True)
    ]

    body: dict[str, Any] = {
        "schema": "stunassure.batch-report/v1",
        "generator": generator,
        "generated_at": generated_at,
        "species": {"key": species_key, "common_name": common_name},
        "lot_size": lot_size,
        "summary": {
            "sample_size": len(sample_events),
            "pass": pass_n,
            "uncertain": uncertain_n,
            "fail": fail_n,
        },
        "certification": {
            "method": "zero-acceptance lot sampling (c=0, hypergeometric)",
            "aql": aql,
            "target_confidence": target_confidence,
            "designed_sample_size": plan.sample_size,
            "observed_defects": observed_defects,
            "accepted": decision.accepted,
            "achieved_confidence": round(decision.achieved_confidence, 4),
            "reason": decision.reason,
        },
        "events": events_block,
        "disclaimer": (
            "StunAssure flags welfare risk and verifies process; it does not determine "
            "consciousness. UNCERTAIN routes to manual check. Heartbeat is not an insensibility "
            "signal (the fish heart is myogenic)."
        ),
    }
    report = dict(body)
    report[_SIGNATURE_KEY] = _sign(body)
    return report


def verify_report(report: dict[str, Any]) -> bool:
    """Return True iff the report's signature matches its content (no tampering)."""
    if _SIGNATURE_KEY not in report:
        return False
    body = {k: v for k, v in report.items() if k != _SIGNATURE_KEY}
    return _sign(body) == str(report[_SIGNATURE_KEY])


def to_json(report: dict[str, Any]) -> str:
    """Pretty JSON serialization (preserves the signature)."""
    return json.dumps(report, indent=2, ensure_ascii=False)


def to_markdown(report: dict[str, Any]) -> str:
    """Human-readable audit summary."""
    s = report["summary"]
    c = report["certification"]
    verdict_line = "✅ LOT CERTIFIED" if c["accepted"] else "⛔ LOT REJECTED — manual check"
    lines = [
        f"# StunAssure Batch Welfare Report — {report['species']['common_name']}",
        "",
        f"- Generated: {report['generated_at']} by {report['generator']}",
        f"- Lot size: {report['lot_size']:,}   ·   Sample: {s['sample_size']}",
        f"- Signature: `{report[_SIGNATURE_KEY][:16]}…` (SHA-256, tamper-evident)",
        "",
        "## Sample verdicts",
        f"- **PASS:** {s['pass']} · **UNCERTAIN:** {s['uncertain']} · **FAIL:** {s['fail']}",
        "",
        "## Certification (Welfare-by-Sampling)",
        f"- Method: {c['method']}",
        f"- AQL {c['aql']:.1%} @ target {c['target_confidence']:.0%} → "
        f"sample {c['designed_sample_size']}, defects {c['observed_defects']}",
        f"- **{verdict_line}** — {c['reason']}",
        "",
        f"> {report['disclaimer']}",
    ]
    return "\n".join(lines)
