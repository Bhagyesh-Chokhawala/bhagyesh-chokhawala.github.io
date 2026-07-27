from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .portal import build_portal, serve_portal
from .reporting import render_markdown, write_json_report, write_markdown_report
from .validators import load_policy_repository, validate_repository


def main() -> None:
    parser = argparse.ArgumentParser(prog="api-standards")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="Validate an API repository")
    validate.add_argument("repository", type=Path)
    validate.add_argument(
        "--policy-index",
        type=Path,
        default=Path("policy-repository/policy-index.yaml"),
    )
    validate.add_argument(
        "--schema",
        type=Path,
        default=Path("schemas/api-metadata.schema.json"),
    )
    validate.add_argument("--json-report", type=Path)
    validate.add_argument("--markdown-report", type=Path)

    catalog = commands.add_parser("catalog", help="List policy dimensions and gate counts")
    catalog.add_argument(
        "--policy-index",
        type=Path,
        default=Path("policy-repository/policy-index.yaml"),
    )

    portal = commands.add_parser("portal", help="Build or serve the policy guidance portal")
    portal_commands = portal.add_subparsers(dest="portal_command", required=True)

    portal_build = portal_commands.add_parser("build", help="Build the static website")
    portal_build.add_argument("--results", type=Path, default=Path("validation-results"))
    portal_build.add_argument("--output", type=Path, default=Path("public"))
    portal_build.add_argument(
        "--policy-index", type=Path, default=Path("policy-repository/policy-index.yaml")
    )
    portal_build.add_argument("--templates", type=Path, default=Path("website/templates"))
    portal_build.add_argument("--static", type=Path, default=Path("website/static"))
    portal_build.add_argument(
        "--config", type=Path, default=Path("website/portal-config.yaml")
    )
    portal_build.add_argument(
        "--previous-site",
        type=Path,
        help="Optional prior published site used to retain historical run pages",
    )

    portal_serve = portal_commands.add_parser("serve", help="Serve a built portal locally")
    portal_serve.add_argument("--directory", type=Path, default=Path("public"))
    portal_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()

    if args.command == "catalog":
        index, dimensions = load_policy_repository(args.policy_index.resolve())
        print(f"{index['name']} v{index['version']}")
        for dimension in dimensions:
            print(
                f"- {dimension['key']}: {dimension['name']} "
                f"({dimension['weight']}%, {len(dimension['gates'])} gates)"
            )
        raise SystemExit(0)

    if args.command == "portal":
        if args.portal_command == "serve":
            serve_portal(args.directory.resolve(), args.port)
            return
        summary = build_portal(
            policy_index_path=args.policy_index.resolve(),
            results_dir=args.results.resolve(),
            output_dir=args.output.resolve(),
            template_dir=args.templates.resolve(),
            static_dir=args.static.resolve(),
            config_path=args.config.resolve(),
            previous_site=args.previous_site.resolve() if args.previous_site else None,
        )
        print(
            f"Portal built at {args.output.resolve()} — "
            f"{summary['dimensions']} dimensions, {summary['stats']['total_runs']} runs"
        )
        raise SystemExit(0)

    try:
        report = validate_repository(
            args.repository.resolve(),
            args.policy_index.resolve(),
            args.schema.resolve(),
        )
    except Exception as error:
        print(f"Validation error: {error}", file=sys.stderr)
        raise SystemExit(2) from error

    markdown = render_markdown(report)
    print(markdown)
    if args.json_report:
        write_json_report(report, args.json_report)
    if args.markdown_report:
        write_markdown_report(report, args.markdown_report)
    raise SystemExit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
