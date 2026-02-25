# Directive: Import from PHY600 with exact paths

**To the condenstate agent:** Use the path where PHY600 lives as `PHY600_ROOT`. If you have `.env` with `PHY600_ROOT`, use that; else use `~/PHY600`. All destinations are relative to the condenstate repo root (the directory that contains `.sst`). Create destination directories as needed. Do not import any file listed under "Do not import" below.

---

## 1. Create `.env`

In condenstate repo root:

```bash
cp .env.example .env
```

Then set in `.env` (do not commit): `PHY600_ROOT=/path/to/PHY600` (e.g. `PHY600_ROOT=~/PHY600`). Optionally set `MAGNIPHYQ_IP` and `SSH_KEY_PATH`.

---

## 2. Paper 1 manuscript (paper1/)

| Copy from (PHY600) | Copy to (condenstate repo root) |
|--------------------|----------------------------------|
| `$PHY600_ROOT/bioRxiv_preprint_synapsin/main.tex` | `paper1/main.tex` |
| `$PHY600_ROOT/bioRxiv_preprint_synapsin/abstract.md` | `paper1/abstract.md` |
| `$PHY600_ROOT/bioRxiv_preprint_synapsin/references.bib` | `paper1/references.bib` |

Commands (run from condenstate repo root; set PHY600_ROOT first):

```bash
mkdir -p paper1
cp "$PHY600_ROOT/bioRxiv_preprint_synapsin/main.tex"       paper1/main.tex
cp "$PHY600_ROOT/bioRxiv_preprint_synapsin/abstract.md"   paper1/abstract.md
cp "$PHY600_ROOT/bioRxiv_preprint_synapsin/references.bib" paper1/references.bib
```

---

## 3. Pipeline scripts (pipeline/)

| Copy from (PHY600) | Copy to (condenstate repo root) |
|--------------------|----------------------------------|
| `$PHY600_ROOT/rerun_v2/pipeline/analyze_sim.py` | `pipeline/analyze_sim.py` |
| `$PHY600_ROOT/rerun_v2/pipeline/generate_canonical_figures.py` | `pipeline/generate_canonical_figures.py` |
| `$PHY600_ROOT/rerun_v2/pipeline/build_figure_manifest.py` | `pipeline/build_figure_manifest.py` |

Commands:

```bash
mkdir -p pipeline
cp "$PHY600_ROOT/rerun_v2/pipeline/analyze_sim.py"              pipeline/analyze_sim.py
cp "$PHY600_ROOT/rerun_v2/pipeline/generate_canonical_figures.py" pipeline/generate_canonical_figures.py
cp "$PHY600_ROOT/rerun_v2/pipeline/build_figure_manifest.py"    pipeline/build_figure_manifest.py
```

---

## 4. Modeling scripts (modeling/)

| Copy from (PHY600) | Copy to (condenstate repo root) |
|--------------------|----------------------------------|
| `$PHY600_ROOT/Presentations/modeling/run_pipeline.py` | `modeling/run_pipeline.py` |
| `$PHY600_ROOT/Presentations/modeling/config.yaml` | `modeling/config.yaml` |
| `$PHY600_ROOT/Presentations/modeling/bridge_lammps_to_ode.py` | `modeling/bridge_lammps_to_ode.py` |
| `$PHY600_ROOT/Presentations/modeling/phase4_analysis/generate_figures.py` | `modeling/phase4_analysis/generate_figures.py` |

Commands:

```bash
mkdir -p modeling/phase4_analysis
cp "$PHY600_ROOT/Presentations/modeling/run_pipeline.py"     modeling/run_pipeline.py
cp "$PHY600_ROOT/Presentations/modeling/config.yaml"        modeling/config.yaml
cp "$PHY600_ROOT/Presentations/modeling/bridge_lammps_to_ode.py" modeling/bridge_lammps_to_ode.py
cp "$PHY600_ROOT/Presentations/modeling/phase4_analysis/generate_figures.py" modeling/phase4_analysis/generate_figures.py
```

Optional (for full paper2 pipeline): copy the rest of `Presentations/modeling/` (e.g. `phase0_setup/`, `phase1_ode/`, `phase2_spiking/`, `phase3_vesicle/`, `phase5_manuscript/`) into `modeling/` with the same directory names.

---

## 5. Simulation (simulation/)

| Copy from (PHY600) | Copy to (condenstate repo root) |
|--------------------|----------------------------------|
| `$PHY600_ROOT/assets/aws_cli_package/simulation/deep_research_upload/parameters/simulation_matrix.csv` | `simulation/parameters/simulation_matrix.csv` |
| `$PHY600_ROOT/assets/aws_cli_package/simulation/run_single_sim.sh` | `simulation/run_single_sim.sh` |
| `$PHY600_ROOT/assets/aws_cli_package/simulation/S1_Parameter_StickerSpacer_Polymers.py` | `simulation/S1_Parameter_StickerSpacer_Polymers.py` |
| `$PHY600_ROOT/assets/aws_cli_package/simulation/S2_Poly_Stickers_Generation_RandAB.py` | `simulation/S2_Poly_Stickers_Generation_RandAB.py` |
| `$PHY600_ROOT/assets/aws_cli_package/simulation/S3_Relax_StickerSpacer_Polymers.py` | `simulation/S3_Relax_StickerSpacer_Polymers.py` |
| `$PHY600_ROOT/assets/aws_cli_package/simulation/S4_Record_StickerSpacers_Polymers.py` | `simulation/S4_Record_StickerSpacers_Polymers.py` |

Commands:

```bash
mkdir -p simulation/parameters
cp "$PHY600_ROOT/assets/aws_cli_package/simulation/deep_research_upload/parameters/simulation_matrix.csv" simulation/parameters/simulation_matrix.csv
cp "$PHY600_ROOT/assets/aws_cli_package/simulation/run_single_sim.sh" simulation/run_single_sim.sh
cp "$PHY600_ROOT/assets/aws_cli_package/simulation/S1_Parameter_StickerSpacer_Polymers.py" simulation/
cp "$PHY600_ROOT/assets/aws_cli_package/simulation/S2_Poly_Stickers_Generation_RandAB.py" simulation/
cp "$PHY600_ROOT/assets/aws_cli_package/simulation/S3_Relax_StickerSpacer_Polymers.py" simulation/
cp "$PHY600_ROOT/assets/aws_cli_package/simulation/S4_Record_StickerSpacers_Polymers.py" simulation/
```

---

## 6. Optional: paper2 PLAN and SST crash course

| Copy from (PHY600) | Copy to (condenstate repo root) |
|--------------------|----------------------------------|
| `$PHY600_ROOT/Presentations/modeling/PLAN.md` | `modeling/PLAN.md` |
| `$PHY600_ROOT/.meta/docs/SST_DDB_CRASHCOURSE.md` | `.meta/docs/SST_DDB_CRASHCOURSE.md` |

Commands:

```bash
cp "$PHY600_ROOT/Presentations/modeling/PLAN.md" modeling/PLAN.md
cp "$PHY600_ROOT/.meta/docs/SST_DDB_CRASHCOURSE.md" .meta/docs/SST_DDB_CRASHCOURSE.md
```

---

## 7. Do not import

- `$PHY600_ROOT/rerun_v2/pipeline/config.sh`
- Any file containing SSH keys, live IPs, or tunnel credentials
- `$PHY600_ROOT/Presentations/modeling/AGENT_HANDOFF.md` (unless you strip local paths first; a sanitized version exists as `.meta/docs/MODELING_HANDOFF.md`)

---

## 8. After import

From condenstate repo root:

```bash
python3 .ddb/tools/register_sst.py
python3 .sst/tools/lifecycle_guard.py
```

Then re-run the local readiness directive; you should report `ready: yes` once `.env` exists and the four areas (paper1, pipeline, modeling, simulation) are present.
