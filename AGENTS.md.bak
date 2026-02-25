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
This is **condenstate**, a computational biophysics research scaffold for two papers on synapsin liquid-liquid phase separation. It is a public mirror repository containing canonical state (`.sst/`), a decision registry (`.ddb/`), simulation analysis pipelines, and modeling code. It does not run live services.

### Key commands

All commands are defined in the root `Makefile`:

- `make eval` — runs all gates/contracts evaluation (register_sst + lifecycle_guard + canon layout). Exit 0 = all pass.
- `make eval-report` — same, also writes report to `.meta/reports/`.
- `make ddb-register` — registers `.sst` artifacts into `.ddb/registry.json`.
- `make lifecycle-guard` — runs lifecycle guard only (JSON to stdout).

### Running the modeling pipeline

The Paper 2 modeling pipeline is at `modeling/run_pipeline.py`. Phase 0 will report `brian2` as missing (optional; Phase 2 has a graceful fallback). Phase 1 (ODE model) is the core demo that exercises `numpy`, `scipy`, and `pyyaml`.

To verify Phase 1 deps:
```bash
python3 -c "import numpy, scipy, yaml; print('deps OK')"
```

The full pipeline (`python3 modeling/run_pipeline.py`) halts at Phase 0 because `brian2` is absent and `MANUSCRIPT_PATH` resolves to `/workspace/main.tex` (manuscript lives at `paper1/main.tex`). This is expected for the public mirror.

To run Phase 1 (ODE model) bypassing Phase 0's gate:
```bash
python3 -c "
import sys; sys.path.insert(0, 'modeling')
from run_pipeline import run_phase1, load_config
results = run_phase1(load_config())
print('Status:', results['status'])
"
```

### Pipeline analysis scripts

Scripts in `pipeline/` (`analyze_sim.py`, `generate_canonical_figures.py`, `build_figure_manifest.py`) require LAMMPS simulation output data not present in this public mirror. They import `numpy` and `matplotlib` but cannot be run without trajectory files.

### Secrets and SSH

For cloud orchestration with PHY600/magniphyq, three Cursor secrets must be set (repo-scoped to condenstate). See `.meta/docs/CLOUD_AGENT_SETUP_GUIDE.md` for full details.

- `MAGNIPHYQ_IP` — magniphyq EC2 public IP
- `SSH_KEY_PATH` — path to PEM key on the VM (the value from `.env.example`)
- `PAX_EC2_KEY_PEM` — full PEM file content of the SSH private key

The VM startup script writes `PAX_EC2_KEY_PEM` to the path in `$SSH_KEY_PATH` with `chmod 600` automatically. To verify SSH connectivity:
```bash
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@$MAGNIPHYQ_IP "echo ok"
```

Full setup guide: `.meta/docs/CLOUD_AGENT_SETUP_GUIDE.md`.

### Python version

Python 3.10+ is required. The VM provides Python 3.12.
