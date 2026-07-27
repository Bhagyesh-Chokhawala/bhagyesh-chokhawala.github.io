from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Iterable

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .validators import load_policy_repository

TEXT_EXTENSIONS = {
    ".txt", ".log", ".md", ".json", ".xml", ".yaml", ".yml", ".csv", ".html"
}
ICONS = {"GREEN": "🟢", "AMBER": "🟠", "RED": "🔴", "UNKNOWN": "⚪"}


@dataclass(frozen=True)
class PortalRun:
    run_id: str
    api_name: str
    repository: str
    ref: str
    commit: str
    timestamp: str
    workflow_url: str
    traffic_light: str
    decision: str
    score: float
    required_score: float
    report: dict[str, Any]
    source_dir: Path
    artifacts: list[dict[str, str]]

    def to_index(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "api_name": self.api_name,
            "repository": self.repository,
            "ref": self.ref,
            "commit": self.commit,
            "timestamp": self.timestamp,
            "workflow_url": self.workflow_url,
            "traffic_light": self.traffic_light,
            "decision": self.decision,
            "score": self.score,
            "required_score": self.required_score,
            "url": f"reports/runs/{self.run_id}/index.html",
        }


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).replace("_", "-").strip("-")
    return cleaned or "run"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _metadata_for(run_dir: Path) -> dict[str, Any]:
    metadata_path = run_dir / "metadata.json"
    if metadata_path.is_file():
        return load_json(metadata_path)
    return {
        "run_id": run_dir.name,
        "repository": "local",
        "ref": "local",
        "commit": "unknown",
        "timestamp": datetime.fromtimestamp(run_dir.stat().st_mtime, tz=timezone.utc).isoformat(),
        "workflow_url": "",
    }


def discover_runs(results_dir: Path) -> list[PortalRun]:
    if not results_dir.exists():
        return []
    runs: list[PortalRun] = []
    candidates = sorted(
        {
            path.parent
            for pattern in ("**/policy-report.json", "**/report.json", "**/api-policy-result.json")
            for path in results_dir.glob(pattern)
        }
    )
    for run_dir in candidates:
        report_path = next(
            (
                path
                for path in (
                    run_dir / "policy-report.json",
                    run_dir / "report.json",
                    run_dir / "api-policy-result.json",
                )
                if path.is_file()
            ),
            None,
        )
        if report_path is None:
            continue
        report = load_json(report_path)
        metadata = _metadata_for(run_dir)
        run_id = slug(str(metadata.get("run_id") or run_dir.name))
        artifacts = [
            {"name": path.name, "relative": path.name}
            for path in sorted(run_dir.iterdir())
            if path.is_file()
        ]
        runs.append(
            PortalRun(
                run_id=run_id,
                api_name=str(report.get("api_name", metadata.get("api_name", run_dir.name))),
                repository=str(metadata.get("repository", "local")),
                ref=str(metadata.get("ref", "local")),
                commit=str(metadata.get("commit", "unknown")),
                timestamp=str(metadata.get("timestamp", utc_now())),
                workflow_url=str(metadata.get("workflow_url", "")),
                traffic_light=str(report.get("traffic_light", "UNKNOWN")),
                decision=str(report.get("decision", "UNKNOWN")),
                score=float(report.get("score", 0.0)),
                required_score=float(report.get("minimum_score", 0.0)),
                report=report,
                source_dir=run_dir,
                artifacts=artifacts,
            )
        )
    return sorted(runs, key=lambda item: item.timestamp, reverse=True)


def _compile_redactors(config: dict[str, Any]) -> list[re.Pattern[str]]:
    patterns = config.get("redaction_patterns", [])
    return [re.compile(str(pattern)) for pattern in patterns]


def redact_text(text: str, redactors: Iterable[re.Pattern[str]]) -> str:
    result = text
    for pattern in redactors:
        result = pattern.sub("[REDACTED]", result)
    return result


def copy_sanitized_file(source: Path, destination: Path, redactors: list[re.Pattern[str]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() in TEXT_EXTENSIONS:
        try:
            text = source.read_text(encoding="utf-8", errors="replace")
        except OSError:
            shutil.copy2(source, destination)
            return
        destination.write_text(redact_text(text, redactors), encoding="utf-8")
    else:
        shutil.copy2(source, destination)


def _read_log_preview(path: Path, redactors: list[re.Pattern[str]], limit: int) -> str:
    if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
        return ""
    data = path.read_text(encoding="utf-8", errors="replace")
    data = redact_text(data, redactors)
    if len(data.encode("utf-8")) > limit:
        data = data[-limit:]
        data = "[Preview truncated to the last portion of the log]\n" + data
    return data


def _load_previous_index(previous_site: Path | None) -> list[dict[str, Any]]:
    if previous_site is None:
        return []
    index_path = previous_site / "reports" / "run-index.json"
    if not index_path.is_file():
        return []
    data = json.loads(index_path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def _copy_previous_runs(previous_site: Path | None, output_dir: Path) -> None:
    if previous_site is None:
        return
    source = previous_site / "reports" / "runs"
    destination = output_dir / "reports" / "runs"
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)


def build_portal(
    *,
    policy_index_path: Path,
    results_dir: Path,
    output_dir: Path,
    template_dir: Path,
    static_dir: Path,
    config_path: Path,
    previous_site: Path | None = None,
) -> dict[str, Any]:
    config_document = load_yaml(config_path)
    config = config_document.get("portal", config_document)
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["icon"] = lambda value: ICONS.get(str(value), "⚪")
    env.filters["fmt_date"] = lambda value: str(value).replace("T", " ").replace("+00:00", " UTC")
    env.globals["site_title"] = config.get("title", "API Policy Portal")
    env.globals["site_description"] = config.get("description", "")
    env.globals["generated_at"] = utc_now()

    index, dimensions = load_policy_repository(policy_index_path)
    redactors = _compile_redactors(config)
    log_limit = int(config.get("max_inline_log_bytes", 250_000))

    if static_dir.is_dir():
        shutil.copytree(static_dir, output_dir / "assets", dirs_exist_ok=True)
    _copy_previous_runs(previous_site, output_dir)

    # Dimension catalog and detail pages
    policies_dir = output_dir / "policies"
    policies_dir.mkdir(parents=True, exist_ok=True)
    for dimension in dimensions:
        destination = policies_dir / slug(dimension["key"]) / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            env.get_template("dimension.html").render(
                page_title=dimension["name"],
                active="policies",
                dimension=dimension,
                policy=index,
            ),
            encoding="utf-8",
        )
    (policies_dir / "index.html").write_text(
        env.get_template("policies.html").render(
            page_title="Policy catalog",
            active="policies",
            policy=index,
            dimensions=dimensions,
        ),
        encoding="utf-8",
    )

    # Current validation runs
    discovered = discover_runs(results_dir)
    current_index: list[dict[str, Any]] = []
    for run in discovered:
        run_output = output_dir / "reports" / "runs" / run.run_id
        files_output = run_output / "files"
        files_output.mkdir(parents=True, exist_ok=True)
        artifact_rows: list[dict[str, str]] = []
        previews: list[dict[str, str]] = []
        for artifact in run.artifacts:
            source = run.source_dir / artifact["relative"]
            destination = files_output / source.name
            copy_sanitized_file(source, destination, redactors)
            artifact_rows.append(
                {
                    "name": source.name,
                    "url": f"files/{source.name}",
                    "type": source.suffix.lower().lstrip(".") or "file",
                }
            )
            if source.suffix.lower() in {".log", ".txt"}:
                preview = _read_log_preview(source, redactors, log_limit)
                if preview:
                    previews.append({"name": source.name, "content": preview})
        (run_output / "index.html").write_text(
            env.get_template("run.html").render(
                page_title=f"Validation run — {run.api_name}",
                active="reports",
                run=run,
                report=run.report,
                artifacts=artifact_rows,
                previews=previews,
            ),
            encoding="utf-8",
        )
        current_index.append(run.to_index())

    # Merge old run index with current, newest current version wins.
    merged: dict[str, dict[str, Any]] = {
        str(item.get("run_id")): item for item in _load_previous_index(previous_site)
    }
    for item in current_index:
        merged[item["run_id"]] = item
    all_runs = sorted(merged.values(), key=lambda item: str(item.get("timestamp", "")), reverse=True)
    retention = int(config.get("retain_runs", 200))
    all_runs = all_runs[:retention]

    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "run-index.json").write_text(json.dumps(all_runs, indent=2), encoding="utf-8")
    (reports_dir / "index.html").write_text(
        env.get_template("reports.html").render(
            page_title="Validation reports",
            active="reports",
            runs=all_runs,
        ),
        encoding="utf-8",
    )

    stats = {
        "total_runs": len(all_runs),
        "green": sum(item.get("traffic_light") == "GREEN" for item in all_runs),
        "amber": sum(item.get("traffic_light") == "AMBER" for item in all_runs),
        "red": sum(item.get("traffic_light") == "RED" for item in all_runs),
    }
    (output_dir / "index.html").write_text(
        env.get_template("home.html").render(
            page_title="Home",
            active="home",
            policy=index,
            dimensions=dimensions,
            runs=all_runs[:10],
            stats=stats,
        ),
        encoding="utf-8",
    )

    for guide_name, title, template_name in (
        ("getting-started", "Getting started", "getting_started.html"),
        ("testing-any-api", "Test any API", "testing_any_api.html"),
        ("adoption", "Cap & Grow adoption", "adoption.html"),
        ("security", "Portal security and log hygiene", "security.html"),
    ):
        destination = output_dir / guide_name / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            env.get_template(template_name).render(
                page_title=title,
                active="guidance",
                policy=index,
            ),
            encoding="utf-8",
        )

    return {"runs": all_runs, "stats": stats, "dimensions": len(dimensions)}


def serve_portal(directory: Path, port: int) -> None:
    import http.server
    import socketserver

    handler = http.server.SimpleHTTPRequestHandler
    previous = Path.cwd()
    try:
        import os

        os.chdir(directory)
        with socketserver.TCPServer(("", port), handler) as server:
            print(f"Serving API Policy Portal at http://localhost:{port}")
            server.serve_forever()
    finally:
        import os

        os.chdir(previous)
