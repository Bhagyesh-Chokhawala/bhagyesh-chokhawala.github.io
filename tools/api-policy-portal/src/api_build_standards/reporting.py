from __future__ import annotations

import json
from pathlib import Path

from .models import ValidationReport

ICONS = {"GREEN": "🟢", "AMBER": "🟠", "RED": "🔴"}


def render_markdown(report: ValidationReport) -> str:
    icon = ICONS[report.traffic_light]
    rows = [
        f"# API Policy Validation: {report.api_name}",
        "",
        f"> {icon} **{report.traffic_light} — {report.decision}**",
        "",
        f"- **Policy repository version:** {report.policy_version}",
        f"- **Risk tier:** {report.risk_tier}",
        f"- **Weighted score:** {report.score:.1f}/100",
        f"- **Required score:** {report.minimum_score:.1f}",
        "",
        "## Dimension traffic lights",
        "",
        "| Light | Dimension | Owner | Score | Weight | Gates | Failed gates |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for dimension in report.dimensions:
        failed = ", ".join(dimension.failed_gate_ids) or "—"
        rows.append(
            f"| {ICONS[dimension.traffic_light]} {dimension.traffic_light} | {dimension.label} | "
            f"{dimension.owner} | {dimension.raw_score:.1f}% | {dimension.weight:.1f} | "
            f"{dimension.checks_passed}/{dimension.checks_total} | {failed} |"
        )

    rows.extend(["", "## Gate findings", ""])
    if not report.findings:
        rows.append("No findings.")
    else:
        rows.extend([
            "| Rule | Dimension | Severity | Blocking | Finding |",
            "|---|---|---|---|---|",
        ])
        for finding in report.findings:
            rows.append(
                f"| {finding.rule_id} | {finding.dimension} | {finding.severity} | "
                f"{'Yes' if finding.blocking else 'No'} | {finding.message} |"
            )
    return "\n".join(rows) + "\n"


def write_json_report(report: ValidationReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")


def write_markdown_report(report: ValidationReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(report), encoding="utf-8")
