# Directive: Local readiness check (condenstate agent)

**Give this to the condenstate agent first.** The agent must run the checks below and then output **only** the confirmation block at the end (no extra chat). Do not echo secrets; report only presence/absence or path names.

---

## Directive (paste this)

You are the local worker in the condenstate repo. Run a full readiness check and then output only the confirmation block below. Do not include secrets or key contents in your response.

**1. Gates/contracts**  
From repo root, run: `python3 .sst/tools/eval_gates.py --report --block`  
Note: overall (pass/fail), report path, and exit code.

**2. Data and scripts in repo**  
Using `.meta/docs/IMPORT_FROM_PHY600.md` and `.meta/docs/CONDENSTATE_GAP_AND_CONTENT.md` as reference, check whether the repo contains:
- **Scripts:** `pipeline/` (analyze_sim.py, generate_canonical_figures.py, build_figure_manifest.py), `modeling/` (run_pipeline.py, config.yaml, bridge_lammps_to_ode.py, phase4_analysis/), `paper1/` or `manuscript/paper1/` (main.tex, abstract.md, references.bib), `simulation/` (simulation_matrix.csv, run_single_sim.sh, S1–S4 scripts). List each as present or missing.
- **Data:** Whether there is a path-normalized analysis_registry or paper2 phase artifacts in repo, or document “data in PHY600” (and that PHY600_ROOT or equivalent is required). List as present_in_repo / in_phy600 / missing.

**3. Env and secrets (do not print values)**  
- `.env` in repo root: present or missing. If missing, state that agent or user should copy from `.env.example` and set vars.
- SSH key: Check that the key file exists at default `~/.ssh/pax-ec2-key.pem` or at the path given in `.env` (if present). Report: exists / missing (do not read or print key contents).
- Optional vars: Report whether MAGNIPHYQ_IP and PHY600_ROOT are set (yes/no), without printing their values. If `.env` is missing, report “not checked”.

**4. Cursor workspace**  
- `.cursor/rules/` present: yes/no.
- List the names of any `.mdc` or rule files under `.cursor/rules/` (e.g. condenstate-orchestration.mdc).
- Confirm `.meta/docs/ENV_AND_ORCHESTRATION.md` exists and is readable.

**5. Output this block and nothing else**

After the checks, output exactly one block in this format (fill in the bracketed parts; do not put secrets in the block):

```
--- condenstate_local_readiness ---
repo: condenstate
eval: [pass|fail]
eval_report: [path to .meta/reports/completeness_*.md or empty]
scripts_pipeline: [present|missing]
scripts_modeling: [present|missing]
paper1_manuscript: [present|missing]
simulation: [present|missing]
data: [present_in_repo|in_phy600|missing]
env_file: [present|missing]
ssh_key: [exists|missing]
env_vars_set: [yes|no|not_checked]
cursor_rules: [present|missing]
cursor_rules_list: [comma-separated filenames or none]
ready: [yes|no]
gaps: [one-line summary of what is missing or "none"]
at: [ISO UTC timestamp]
---
```

Use `ready: yes` only when eval is pass, env_file is present, ssh_key exists, and gaps are acceptable for the next step (or "none"). Otherwise `ready: no` and set `gaps` to what is missing. Do not add any text before or after the block.
