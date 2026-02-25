# condenstate: What's Here vs What's Needed

## Dot directories (.ddb, .meta, .sst) are in the repo

They are committed and tracked. GitHub's file browser often does not show dot-prefixed files/folders at the repo root; they are still there. Verify with:

```bash
git clone https://github.com/GilRaitses/condenstate && cd condenstate && ls -la && ls -la .ddb .meta .sst
```

Or browse via GitHub URL: `https://github.com/GilRaitses/condenstate/tree/main/.sst` (and `.ddb`, `.meta`).

---

## What this repo currently contains (canon only)

- **.sst** – Canonical state: paper1/paper2 objective specs, sweep/figure manifests, lifecycle_contract, run_manifest, evidence_index, claims_matrix, layout_policy, resume_protocol, lifecycle_guard.py, reconstruction_check, system snapshots.
- **.ddb** – Decision registry: PROTOCOL.md, registry.json, register_sst.py, register_config.json.
- **.meta** – Playbook (SYNAPSIN_ORCHESTRATION_PLAYBOOK.md), placeholder dirs for runs/figs (.gitkeep), and validation reports. No run data or figure outputs yet.
- **Root** – README.md, EXPORT_MANIFEST.md, REPO_AUDIT_REPORT.md.

So: **specs, contracts, and tooling are present; no scripts, no data, no manuscript sources.**

---

## What's missing to make paper objectives executable

Per EXPORT_MANIFEST.md (which is in this repo), the following are **required for execution** but **not yet in condenstate**:

### Paper 1 (phase diagram)

| Missing | Purpose |
|--------|--------|
| Manuscript sources | `bioRxiv_preprint_synapsin/main.tex`, `abstract.md`, `references.bib` |
| Pipeline scripts | `rerun_v2/pipeline/analyze_sim.py`, `generate_canonical_figures.py`, `build_figure_manifest.py`, `sweep.sh` |
| Simulation defs | `simulation_matrix.csv`, `run_single_sim.sh`, LAMMPS generators (S1–S4) as referenced by run_single_sim |
| Data / registry | Simulation outputs and/or path-normalized `analysis_registry.json` (transform-before-export per EXPORT_MANIFEST) |

### Paper 2 (learning bridge)

| Missing | Purpose |
|--------|--------|
| Modeling pipeline | `Presentations/modeling/run_pipeline.py`, `config.yaml`, `PLAN.md` |
| Bridge & figures | `bridge_lammps_to_ode.py`, `phase4_analysis/generate_figures.py` |
| Data / artifacts | Phase outputs and figure inputs expected by the pipeline |

### Cross-cutting

| Missing | Purpose |
|--------|--------|
| AGENTS.md, Makefile | Onboarding and canonical commands (optional if condenstate is script-only). |
| .meta/docs/SST_DDB_CRASHCOURSE.md | Referenced in EXPORT_MANIFEST for onboarding. |

---

## Recommended next steps

1. **Second export phase**: Copy the "Included for export" items from EXPORT_MANIFEST from PHY600 into condenstate, using repo-relative paths. For `analysis_registry.json`, export a path-normalized version (transform-before-export).
2. **Data policy**: Decide whether condenstate holds (a) only scripts + specs and points to external data, or (b) a snapshot of key data (e.g. analysis registry, figure inputs) with a clear layout under `.meta/runs` and `.meta/figs`.
3. **Lifecycle**: After adding scripts or data, run `python3 .ddb/tools/register_sst.py` and `python3 .sst/tools/lifecycle_guard.py` and commit any updated `.ddb`/`.sst` as in the playbook.
