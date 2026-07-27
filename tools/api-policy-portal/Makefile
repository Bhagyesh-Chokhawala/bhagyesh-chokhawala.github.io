.PHONY: install test catalog validate-example validate-amber validate-failing demo-results portal portal-serve clean

install:
	python -m pip install -e ".[dev]"

test:
	pytest

catalog:
	api-standards catalog

validate-example:
	api-standards validate examples/compliant-api \
		--json-report reports/compliant.json \
		--markdown-report reports/compliant.md

validate-amber:
	-api-standards validate examples/amber-api \
		--json-report reports/amber.json \
		--markdown-report reports/amber.md

validate-failing:
	-api-standards validate examples/noncompliant-api \
		--json-report reports/noncompliant.json \
		--markdown-report reports/noncompliant.md

demo-results:
	bash scripts/generate-demo-runs.sh

portal: demo-results
	api-standards portal build --results validation-results --output public

portal-serve: portal
	api-standards portal serve --directory public --port 8000

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info reports/*.json reports/*.md validation-results public
