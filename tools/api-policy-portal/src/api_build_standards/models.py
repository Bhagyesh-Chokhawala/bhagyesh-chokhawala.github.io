from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Finding:
    rule_id: str
    dimension: str
    severity: str
    message: str
    blocking: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DimensionResult:
    key: str
    label: str
    owner: str
    weight: float
    earned: float
    raw_score: float
    traffic_light: str
    checks_passed: int
    checks_total: int
    failed_gate_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    api_name: str
    policy_version: str
    risk_tier: str
    minimum_score: float
    score: float
    traffic_light: str
    decision: str
    dimensions: list[DimensionResult]
    findings: list[Finding]

    @property
    def blocking_findings(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.blocking]

    @property
    def passed(self) -> bool:
        return self.traffic_light == "GREEN" and not self.blocking_findings

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_name": self.api_name,
            "policy_version": self.policy_version,
            "risk_tier": self.risk_tier,
            "minimum_score": self.minimum_score,
            "score": self.score,
            "traffic_light": self.traffic_light,
            "decision": self.decision,
            "passed": self.passed,
            "dimensions": [dimension.to_dict() for dimension in self.dimensions],
            "findings": [finding.to_dict() for finding in self.findings],
        }
