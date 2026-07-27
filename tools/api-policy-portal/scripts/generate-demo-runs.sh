#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS="$ROOT/validation-results"
mkdir -p "$RESULTS"

create_run() {
  local run_id="$1"
  local example="$2"
  local run_dir="$RESULTS/$run_id"
  rm -rf "$run_dir"
  mkdir -p "$run_dir"

  python - "$run_dir/metadata.json" "$run_id" "$example" <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path
out, run_id, example = sys.argv[1:]
Path(out).write_text(json.dumps({
    "run_id": run_id,
    "repository": "policy-repository/examples",
    "ref": example,
    "commit": "demo",
    "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    "workflow_url": ""
}, indent=2), encoding="utf-8")
PY

  set +e
  (cd "$ROOT" && pytest -q --junitxml "$run_dir/test-results.xml") \
    >"$run_dir/tests.log" 2>&1
  echo $? >"$run_dir/test-exit-code.txt"

  (cd "$ROOT" && PYTHONPATH=src python -m api_build_standards.cli validate "examples/$example" \
    --json-report "$run_dir/policy-report.json" \
    --markdown-report "$run_dir/policy-report.md") \
    >"$run_dir/policy-validation.log" 2>&1
  echo $? >"$run_dir/policy-exit-code.txt"
  set -e
}

create_run "demo-green" "compliant-api"
create_run "demo-amber" "amber-api"
create_run "demo-red" "noncompliant-api"

echo "Demo validation runs created under $RESULTS"
