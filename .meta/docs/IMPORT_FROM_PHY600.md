# What to import into condenstate from PHY600

Copy from `~/PHY600` (or PHY600 repo root) into `~/condenstate` keeping paths below relative to repo root. Do **not** import blocked or transform-before-export items (see EXPORT_MANIFEST.md).

---

## 1. Docs (paper 1 + onboarding)

| PHY600 path | Copy to condenstate as |
|-------------|------------------------|
| `bioRxiv_preprint_synapsin/main.tex` | `paper1/main.tex` (or `manuscript/paper1/main.tex`) |
| `bioRxiv_preprint_synapsin/abstract.md` | `paper1/abstract.md` |
| `bioRxiv_preprint_synapsin/references.bib` | `paper1/references.bib` |
| `Presentations/modeling/PLAN.md` | `paper2/PLAN.md` (or `modeling/PLAN.md`) |
| `.meta/docs/SST_DDB_CRASHCOURSE.md` | `.meta/docs/SST_DDB_CRASHCOURSE.md` |
| `AGENTS.md` | `AGENTS.md` |
| `Makefile` | `Makefile` (adjust targets if they reference PHY600-only paths) |

Optional: `bioRxiv_preprint_synapsin/figures/` (PDFs) if you want manuscript figures in repo; else treat as build outputs.

---

## 2. Scripts – Paper 1 (rerun_v2 pipeline)

| PHY600 path | Copy to condenstate as |
|-------------|------------------------|
| `rerun_v2/pipeline/analyze_sim.py` | `pipeline/analyze_sim.py` (or `rerun_v2/pipeline/analyze_sim.py`) |
| `rerun_v2/pipeline/generate_canonical_figures.py` | `pipeline/generate_canonical_figures.py` |
| `rerun_v2/pipeline/build_figure_manifest.py` | `pipeline/build_figure_manifest.py` |

**Note:** `rerun_v2/pipeline/sweep.sh` is listed in EXPORT_MANIFEST but does not exist in PHY600; the actual orchestrator is `run_pipeline.sh`, which **sources `config.sh`** (blocked – has SSH/remote endpoints). So either:
- Import only the three Python scripts above (portable; they read paths from args or config), or
- Import `run_pipeline.sh` plus a **sanitized** `config.sh` template (no real IPs/keys) for local/CI use.

Do **not** import: `config.sh` as-is, `1_collect.sh`, `2_analyze.sh`, `3_integrate.sh`, `fire_from_magniphyq.sh` (they are EC2/magniphyq-specific).

---

## 3. Scripts – Paper 2 (modeling / bridge)

| PHY600 path | Copy to condenstate as |
|-------------|------------------------|
| `Presentations/modeling/run_pipeline.py` | `modeling/run_pipeline.py` |
| `Presentations/modeling/config.yaml` | `modeling/config.yaml` |
| `Presentations/modeling/bridge_lammps_to_ode.py` | `modeling/bridge_lammps_to_ode.py` |
| `Presentations/modeling/phase4_analysis/generate_figures.py` | `modeling/phase4_analysis/generate_figures.py` |

**Dependencies:** `run_pipeline.py` invokes other phases (phase1 ODE, phase2 spiking, phase3 vesicle, phase5 manuscript). For a minimal condenstate, importing the four files above gives you the bridge and figure-generation logic; full pipeline runs may require additional modules under `Presentations/modeling/` (e.g. `phase2_spiking/`, `phase3_vesicle/`, `phase0_setup/requirements.txt`). Add them if you need end-to-end `run_pipeline.py` execution.

---

## 4. Simulation parameter matrix + run driver (Paper 1)

| PHY600 path | Copy to condenstate as |
|-------------|------------------------|
| `assets/aws_cli_package/simulation/deep_research_upload/parameters/simulation_matrix.csv` | `simulation/parameters/simulation_matrix.csv` |
| `assets/aws_cli_package/simulation/run_single_sim.sh` | `simulation/run_single_sim.sh` |
| `assets/aws_cli_package/simulation/S1_Parameter_StickerSpacer_Polymers.py` | `simulation/S1_Parameter_StickerSpacer_Polymers.py` |
| `assets/aws_cli_package/simulation/S2_Poly_Stickers_Generation_RandAB.py` | `simulation/S2_Poly_Stickers_Generation_RandAB.py` |
| `assets/aws_cli_package/simulation/S3_Relax_StickerSpacer_Polymers.py` | `simulation/S3_Relax_StickerSpacer_Polymers.py` |
| `assets/aws_cli_package/simulation/S4_Record_StickerSpacers_Polymers.py` | `simulation/S4_Record_StickerSpacers_Polymers.py` |

`run_single_sim.sh` uses `SCRIPT_DIR` to call the S1–S4 scripts; keep them in the same directory or set `SCRIPT_DIR` in the script to the directory that contains the S* scripts.

---

## 5. Data / registry (transform before import)

| PHY600 path | Action |
|-------------|--------|
| `rerun_v2/analysis_registry.json` | **Transform:** replace absolute paths with repo-relative paths (e.g. under `.meta/runs/paper1/` or `data/`), then copy the normalized JSON into condenstate (e.g. `pipeline/analysis_registry.json` or `.meta/paper1/analysis_registry.json`). See EXPORT_MANIFEST “transform-before-export”. |

Raw simulation outputs (LAMMPS dumps, logs) are large and host-specific; either host them elsewhere and point the registry at URLs, or add a small sample for tests only.

---

## 6. Do not import (blocked)

- `rerun_v2/pipeline/config.sh` (SSH, IPs, keys)
- `.cursor/rules/cloudflare-tunnel-config.mdc`
- Any `.ssh` keys, EC2 deployment docs with live endpoints
- `Presentations/modeling/AGENT_HANDOFF.md` (transform first if needed – strip local paths)

---

## Suggested layout in condenstate after import

```
condenstate/
├── .ddb/          (already present)
├── .meta/
│   ├── docs/      (+ SST_DDB_CRASHCOURSE.md)
│   ├── figs/      (already placeholders)
│   └── runs/      (already placeholders)
├── .sst/          (already present)
├── AGENTS.md
├── Makefile
├── paper1/        (or manuscript/paper1/)
│   ├── main.tex
│   ├── abstract.md
│   └── references.bib
├── paper2/        (or modeling/)
│   └── PLAN.md
├── pipeline/      (analyze_sim, generate_canonical_figures, build_figure_manifest)
├── modeling/      (run_pipeline.py, config.yaml, bridge_lammps_to_ode.py, phase4_analysis/)
└── simulation/    (simulation_matrix.csv, run_single_sim.sh, S1–S4*.py)
```

After adding files, run `python3 .ddb/tools/register_sst.py` and `python3 .sst/tools/lifecycle_guard.py` and commit any updated `.ddb`/`.sst`.
