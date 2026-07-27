from pathlib import Path

from api_build_standards.validators import load_policy_repository, validate_repository

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "policy-repository/policy-index.yaml"
SCHEMA = ROOT / "schemas/api-metadata.schema.json"


def test_policy_dimensions_total_100() -> None:
    _index, dimensions = load_policy_repository(POLICY)
    assert sum(float(item["weight"]) for item in dimensions) == 100
    assert len(dimensions) == 10


def test_compliant_api_is_green() -> None:
    report = validate_repository(ROOT / "examples/compliant-api", POLICY, SCHEMA)
    assert report.passed
    assert report.traffic_light == "GREEN"
    assert report.score == 100.0
    assert all(item.traffic_light == "GREEN" for item in report.dimensions)


def test_noncompliant_api_is_red() -> None:
    report = validate_repository(ROOT / "examples/noncompliant-api", POLICY, SCHEMA)
    assert not report.passed
    assert report.traffic_light == "RED"
    assert report.blocking_findings


def test_every_gate_id_is_unique() -> None:
    _index, dimensions = load_policy_repository(POLICY)
    gate_ids = [gate["id"] for dimension in dimensions for gate in dimension["gates"]]
    assert len(gate_ids) == len(set(gate_ids))


def test_amber_api_requires_remediation() -> None:
    report = validate_repository(ROOT / "examples/amber-api", POLICY, SCHEMA)
    assert not report.passed
    assert report.traffic_light == "AMBER"
    assert not report.blocking_findings
    assert any(item.traffic_light == "AMBER" for item in report.dimensions)
