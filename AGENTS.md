# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is a computational biophysics orchestration scaffold (public mirror). It contains canonical state surfaces (`.sst/`), decision registry (`.ddb/`), simulation scripts, analysis pipelines, and manuscript sources for two paper programs. No web server, database, or Docker is involved. All core tooling is Python 3 (stdlib only).

### Running lint/test/build

There is no formal linter or test suite. The primary validation mechanism is the eval gates system:

- `make eval` — runs all gates and contracts; exit 0 means all pass.
- `make eval-report` — same as above plus writes a report to `.meta/reports/`.
- `make lifecycle-guard` — runs lifecycle guard only (JSON to stdout).
- `make ddb-register` — registers `.sst` artifacts into `.ddb/registry.json`.

These commands invoke Python 3 scripts under `.sst/tools/` and `.ddb/tools/` that use only the standard library.

### Modeling pipeline

The modeling pipeline at `modeling/run_pipeline.py` requires `numpy`, `scipy`, and `matplotlib`. It runs in phases (0-5). Phase 1 (ODE model) is the core computational demo. Phases 2+ depend on `brian2` and additional phase-specific modules (`phase2_spiking/`, `phase3_vesicle/`, etc.) that are not present in this public mirror. Phase 0 will report "fail" if `brian2` is missing or the manuscript file is not at the expected relative path; this is expected behavior in the mirror repo.

### Environment variables (optional, for cloud orchestration)

`MAGNIPHYQ_IP`, `SSH_KEY_PATH`, `PHY600_ROOT` — only needed when orchestrating with the sibling PHY600 repo and AWS EC2. See `.meta/docs/ENV_AND_ORCHESTRATION.md` and `.meta/docs/CLOUD_AGENT_SETUP_GUIDE.md`. These are not required for running eval gates or the modeling pipeline locally.
