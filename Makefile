.PHONY: fmt lint type test docs ci viz bench audit
fmt:
	black .
lint:
	ruff check .
type:
	mypy src
test:
	pytest
docs:
	mkdocs build --strict
viz:
	python -m neuromotorica.analysis.viz_cli --outdir outputs
bench:
	python -m neuromotorica.analysis.benchmarks_cli
audit:
	pip-audit -r requirements.txt || true
ci: fmt lint type test docs
