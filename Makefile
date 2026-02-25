# condenstate: canonical targets for gates and eval

.PHONY: eval eval-report ddb-register lifecycle-guard

# Run gates + contracts eval; report to stdout. Exit 0 = all pass.
eval:
	python3 .sst/tools/eval_gates.py

# Run eval and write report to .meta/reports/completeness_<timestamp>.md
eval-report:
	python3 .sst/tools/eval_gates.py --report

# Register .sst artifacts into .ddb/registry.json
ddb-register:
	python3 .ddb/tools/register_sst.py

# Run lifecycle guard only (JSON to stdout)
lifecycle-guard:
	python3 .sst/tools/lifecycle_guard.py
