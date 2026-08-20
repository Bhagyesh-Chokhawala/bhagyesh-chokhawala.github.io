#!/usr/bin/env python3
"""Validate an AI readiness assessment against the portal control catalog.

Usage:
  python tools/validate_assessment.py artifacts/samples/sample-release-assessment.json

The script intentionally has no third-party dependencies.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "data" / "artifacts.json").read_text(encoding="utf-8"))


def main(path: str) -> int:
    assessment = json.loads(Path(path).read_text(encoding="utf-8"))
    risk = assessment.get("riskTier", "R2")
    controls = assessment.get("controls")
    if controls is None:
        print("Assessment has no 'controls' array. This sample is summary-only; export a full assessment from the portal.")
        return 2
    by_id = {c["id"]: c for c in controls}
    applicable = [a for a in CATALOG if risk in a["riskTiers"]]
    mandatory = [a for a in applicable if a["requirement"] == "MUST"]
    missing = [a["id"] for a in mandatory if not by_id.get(a["id"], {}).get("satisfied", False)]
    all_done = sum(bool(by_id.get(a["id"], {}).get("satisfied", False)) for a in applicable)
    score = round(100 * all_done / len(applicable)) if applicable else 0
    status = "RED" if missing else ("GREEN" if score >= 90 else "AMBER")
    result = {"riskTier": risk, "status": status, "score": score, "mandatoryBlockers": missing}
    print(json.dumps(result, indent=2))
    return 1 if status == "RED" else 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: validate_assessment.py <assessment.json>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
