# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is **condenstate**, a computational biophysics research scaffold for two papers on synapsin liquid-liquid phase separation. It is a public mirror repository containing canonical state (`.sst/`), a decision registry (`.ddb/`), simulation analysis pipelines, and modeling code. It does not run live services.

### Key commands

All commands are defined in the root `Makefile`:

- `make eval` — runs all gates/contracts evaluation (register_sst + lifecycle_guard + canon layout). Exit 0 = all pass.
- `make eval-report` — same, also writes report to `.meta/reports/`.
- `make ddb-register` — registers `.sst` artifacts into `.ddb/registry.json`.
- `make lifecycle-guard` — runs lifecycle guard only (JSON to stdout).

### Running the modeling pipeline

The Paper 2 modeling pipeline is at `modeling/run_pipeline.py`. Phase 0 will report `brian2` as missing (optional; Phase 2 has a graceful fallback). Phase 1 (ODE model) is the core demo that exercises `numpy`, `scipy`, and `pyyaml`.

To run Phase 1 directly:
```bash
python3 -c "import numpy, scipy, yaml; print('deps OK')"
```

The full pipeline (`python3 modeling/run_pipeline.py`) requires a `main.tex` at the repo root, but the manuscript lives at `paper1/main.tex`. Phase 0 will fail because `MANUSCRIPT_PATH` resolves to `/workspace/main.tex`. This is expected for the public mirror; the pipeline is designed for the PHY600 repo layout.

### Pipeline analysis scripts

Scripts in `pipeline/` (`analyze_sim.py`, `generate_canonical_figures.py`, `build_figure_manifest.py`) require LAMMPS simulation output data not present in this public mirror. They import `numpy` and `matplotlib` but cannot be run without trajectory files.

### Secrets and SSH

This repo contains no secrets. For cloud orchestration with PHY600/magniphyq, see `.meta/docs/CLOUD_AGENT_SETUP_GUIDE.md`. Those features are optional and require `MAGNIPHYQ_IP`, `SSH_KEY_PATH`, and `PHY600_ROOT` environment variables plus an SSH key on the VM.

### Python version

Python 3.10+ is required. The VM provides Python 3.12.
