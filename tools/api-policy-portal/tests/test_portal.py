from __future__ import annotations

import json
from pathlib import Path

from api_build_standards.portal import build_portal
from api_build_standards.reporting import write_json_report, write_markdown_report
from api_build_standards.validators import validate_repository

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "policy-repository/policy-index.yaml"
SCHEMA = ROOT / "schemas/api-metadata.schema.json"


def test_portal_builds_policy_and_sanitized_report_pages(tmp_path: Path) -> None:
    results = tmp_path / "validation-results"
    run = results / "run-001"
    run.mkdir(parents=True)

    report = validate_repository(ROOT / "examples/compliant-api", POLICY, SCHEMA)
    write_json_report(report, run / "policy-report.json")
    write_markdown_report(report, run / "policy-report.md")
    (run / "metadata.json").write_text(
        json.dumps(
            {
                "run_id": "run-001",
                "repository": "example/customer-disconnect-api",
                "ref": "main",
                "commit": "abc123",
                "timestamp": "2026-07-27T10:00:00+00:00",
                "workflow_url": "https://example.test/actions/1",
            }
        ),
        encoding="utf-8",
    )
    (run / "tests.log").write_text(
        "tests passed\nAuthorization: Bearer SECRET-TOKEN-123\n",
        encoding="utf-8",
    )

    output = tmp_path / "public"
    summary = build_portal(
        policy_index_path=POLICY,
        results_dir=results,
        output_dir=output,
        template_dir=ROOT / "website/templates",
        static_dir=ROOT / "website/static",
        config_path=ROOT / "website/portal-config.yaml",
    )

    assert summary["stats"]["total_runs"] == 1
    assert (output / "index.html").is_file()
    assert (output / "policies/index.html").is_file()
    assert (output / "reports/index.html").is_file()
    assert (output / "reports/runs/run-001/index.html").is_file()

    sanitized = (output / "reports/runs/run-001/files/tests.log").read_text(encoding="utf-8")
    assert "SECRET-TOKEN-123" not in sanitized
    assert "[REDACTED]" in sanitized
