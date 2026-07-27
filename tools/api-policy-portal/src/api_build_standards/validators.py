from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import yaml
from jsonschema import Draft202012Validator

from .models import DimensionResult, Finding, ValidationReport

Evaluator = Callable[[dict[str, Any], Path, dict[str, Any], dict[str, Any]], bool]


def get(data: dict[str, Any], dotted: str, default: Any = None) -> Any:
    value: Any = data
    for key in dotted.split("."):
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return loaded


def openapi_document(manifest: dict[str, Any], repo: Path) -> dict[str, Any] | None:
    target = repo / str(get(manifest, "contracts.openapi", ""))
    return load_yaml(target) if target.is_file() else None


def evaluate_truthy(data, _repo, _settings, args):
    return bool(get(data, args["path"]))


def evaluate_falsey(data, _repo, _settings, args):
    return not bool(get(data, args["path"], False))


def evaluate_nonempty(data, _repo, _settings, args):
    return bool(str(get(data, args["path"], "")).strip())


def evaluate_file_exists(data, repo, _settings, args):
    return (repo / str(get(data, args["path"], ""))).is_file()


def evaluate_dir_has_files(data, repo, _settings, args):
    target = repo / str(get(data, args["path"], ""))
    return target.is_dir() and any(item.is_file() for item in target.rglob("*"))


def evaluate_openapi_structural(data, repo, _settings, _args):
    document = openapi_document(data, repo)
    return bool(
        document
        and str(document.get("openapi", "")).startswith("3.")
        and document.get("info")
        and isinstance(document.get("paths"), dict)
    )


def evaluate_openapi_security(data, repo, _settings, _args):
    document = openapi_document(data, repo)
    return bool(document and get(document, "components.securitySchemes", {}) and document.get("security"))


def evaluate_openapi_headers(data, repo, settings, _args):
    document = openapi_document(data, repo)
    if not document:
        return False
    serialized = yaml.safe_dump(document).lower()
    return all(header.lower() in serialized for header in settings["required_observability_headers"])


def evaluate_health_paths(data, repo, settings, _args):
    document = openapi_document(data, repo)
    return bool(
        document
        and set(settings["required_health_paths"]).issubset(set(document.get("paths", {})))
    )


def evaluate_no_prohibited_paths(data, repo, settings, _args):
    document = openapi_document(data, repo)
    if not document:
        return False
    terms = [term.lower() for term in settings["prohibited_path_terms"]]
    return all(not any(term in path.lower() for term in terms) for path in document.get("paths", {}))


def evaluate_integrity_complete(data, _repo, _settings, _args):
    if not get(data, "integrity.nosql", False):
        return bool(get(data, "integrity.idempotency"))
    required = [
        "integrity.aggregate_owner",
        "integrity.single_writer",
        "integrity.concurrency_control",
        "integrity.idempotency",
        "integrity.outbox_inbox",
        "integrity.projection_freshness",
        "integrity.reconciliation",
        "integrity.saga_or_compensation",
    ]
    return all(bool(get(data, path)) for path in required)


def evaluate_mcp_governed(data, _repo, _settings, _args):
    if not get(data, "ai.mcp.enabled", False):
        return True
    required = [
        "ai.mcp.scoped_tools",
        "ai.mcp.object_level_authorization",
        "ai.mcp.audit",
        "ai.mcp.approval_for_high_risk",
    ]
    return all(bool(get(data, path)) for path in required)


def evaluate_a2a_governed(data, _repo, _settings, _args):
    if not get(data, "ai.a2a.enabled", False):
        return True
    required = [
        "ai.a2a.agent_identity",
        "ai.a2a.delegation_chain",
        "ai.a2a.task_status",
        "ai.a2a.audit",
    ]
    return all(bool(get(data, path)) for path in required)


EVALUATORS: dict[str, Evaluator] = {
    "truthy": evaluate_truthy,
    "falsey": evaluate_falsey,
    "nonempty": evaluate_nonempty,
    "file_exists": evaluate_file_exists,
    "dir_has_files": evaluate_dir_has_files,
    "openapi_structural": evaluate_openapi_structural,
    "openapi_security": evaluate_openapi_security,
    "openapi_headers": evaluate_openapi_headers,
    "health_paths": evaluate_health_paths,
    "no_prohibited_paths": evaluate_no_prohibited_paths,
    "integrity_complete": evaluate_integrity_complete,
    "mcp_governed": evaluate_mcp_governed,
    "a2a_governed": evaluate_a2a_governed,
}


def load_policy_repository(index_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    index = load_yaml(index_path)["policy_repository"]
    dimensions: list[dict[str, Any]] = []
    for item in index["dimensions"]:
        path = index_path.parent / item["file"]
        dimensions.append(load_yaml(path)["dimension"])
    total_weight = sum(float(item["weight"]) for item in dimensions)
    if total_weight != 100:
        raise ValueError(f"Policy dimension weights must total 100, found {total_weight}")
    return index, dimensions


def traffic_light(raw_score: float, blocking: bool, thresholds: dict[str, Any]) -> str:
    if blocking:
        return "RED"
    if raw_score >= float(thresholds["green"]):
        return "GREEN"
    if raw_score >= float(thresholds["amber"]):
        return "AMBER"
    return "RED"


def validate_repository(repo: Path, policy_index_path: Path, schema_path: Path) -> ValidationReport:
    manifest_path = repo / "api.yaml"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing API manifest: {manifest_path}")

    manifest = load_yaml(manifest_path)
    index, policy_dimensions = load_policy_repository(policy_index_path)
    settings = index["shared_settings"]
    findings: list[Finding] = []

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    for error in Draft202012Validator(schema).iter_errors(manifest):
        findings.append(Finding("META-001", "metadata", "CRITICAL", error.message, True))

    dimension_results: list[DimensionResult] = []
    for dimension in policy_dimensions:
        passed = 0
        failed_ids: list[str] = []
        dimension_findings: list[Finding] = []
        for gate in dimension["gates"]:
            evaluator_name = gate["evaluator"]
            evaluator = EVALUATORS.get(evaluator_name)
            if evaluator is None:
                raise ValueError(f"Unknown evaluator '{evaluator_name}' in gate {gate['id']}")
            try:
                ok = bool(evaluator(manifest, repo, settings, gate.get("args", {})))
            except Exception:
                ok = False
            if ok:
                passed += 1
            else:
                finding = Finding(
                    gate["id"],
                    dimension["key"],
                    gate.get("severity", "HIGH"),
                    gate["title"],
                    bool(gate.get("blocking", False)),
                )
                findings.append(finding)
                dimension_findings.append(finding)
                failed_ids.append(gate["id"])

        total = len(dimension["gates"])
        raw_score = round(100 * passed / total, 1)
        weight = float(dimension["weight"])
        earned = round(weight * raw_score / 100, 2)
        light = traffic_light(
            raw_score,
            any(finding.blocking for finding in dimension_findings),
            dimension.get("traffic_light", {"green": 90, "amber": 70}),
        )
        dimension_results.append(
            DimensionResult(
                key=dimension["key"],
                label=dimension["name"],
                owner=dimension.get("owner", "Unassigned"),
                weight=weight,
                earned=earned,
                raw_score=raw_score,
                traffic_light=light,
                checks_passed=passed,
                checks_total=total,
                failed_gate_ids=failed_ids,
            )
        )

    score = round(sum(item.earned for item in dimension_results), 1)
    risk_tier = str(get(manifest, "api.risk_tier", "high"))
    minimum_score = float(index["risk_tiers"].get(risk_tier, {}).get("minimum_score", index["default_minimum_score"]))
    has_blocker = any(finding.blocking for finding in findings)
    any_red = any(item.traffic_light == "RED" for item in dimension_results)
    any_amber = any(item.traffic_light == "AMBER" for item in dimension_results)

    overall_thresholds = index["traffic_lights"]
    if has_blocker or any_red or score < float(overall_thresholds["amber"]["minimum_score"]):
        overall = "RED"
        decision = "REJECTED - RELEASE BLOCKED"
    elif any_amber or score < max(minimum_score, float(overall_thresholds["green"]["minimum_score"])):
        overall = "AMBER"
        decision = "REMEDIATION OR RISK ACCEPTANCE REQUIRED"
    else:
        overall = "GREEN"
        decision = "APPROVED"

    return ValidationReport(
        api_name=str(get(manifest, "api.name", repo.name)),
        policy_version=str(index["version"]),
        risk_tier=risk_tier,
        minimum_score=minimum_score,
        score=score,
        traffic_light=overall,
        decision=decision,
        dimensions=dimension_results,
        findings=findings,
    )
