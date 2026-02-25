# Heads-up for external orchestrator

## Agent status in condenstate

The agent is **live in condenstate** and has been **cleared for**:

- **Resume** – Lifecycle gates passed (lifecycle_id consistent across run_manifest, lifecycle_contract, lifecycle_index, reconstruction_check; no orphans; contract active in .ddb; reconstructable).
- **Contracts** – No UNSET in decisiondb_identity_fields; supported claims have evidence_refs; evidence hashes match raw artifacts.
- **Canon layout** – All required .sst and .ddb files present (index, run_manifest, paper1/paper2 specs, registry, lifecycle_guard, etc.).

So the repo is in a consistent state and **cleared for running paper1 and paper2 workflows** (specs and contracts allow work to proceed). Execution readiness (scripts, data, env) is separate and checked below.

---

## What the orchestrator can tell the agent to do

To have the agent **check whether it has everything it needs** to start working on paper1 and paper2 directives (including for cloud agents driven from condenstate):

### 1. Run the gates/contracts eval

```bash
cd <condenstate_repo_root>
python3 .sst/tools/eval_gates.py --report --block
```

Interpret the block: `overall: pass` means gates/contracts still pass; `report:` path is the completeness report. Exit code 0 = all pass.

### 2. Run the readiness checklist (what’s missing for paper1/paper2)

The agent should:

1. **Read** `.meta/docs/IMPORT_FROM_PHY600.md` and `.meta/docs/CONDENSTATE_GAP_AND_CONTENT.md`.
2. **Check** whether condenstate already has:
   - `pipeline/` (analyze_sim.py, generate_canonical_figures.py, build_figure_manifest.py),
   - `modeling/` (run_pipeline.py, config.yaml, bridge_lammps_to_ode.py, phase4_analysis/),
   - `paper1/` or `manuscript/paper1/` (main.tex, abstract.md, references.bib),
   - `simulation/` (simulation_matrix.csv, run_single_sim.sh, S1–S4 scripts).
3. If any are missing: either **import from PHY600** per IMPORT_FROM_PHY600.md (agent needs access to PHY600 repo) or **record gaps** and proceed only for tasks that don’t need them.
4. **Data**: Paper1 needs simulation outputs or a path-normalized analysis_registry; paper2 needs phase artifacts. Either they live in PHY600 (agent uses `PHY600_ROOT`) or a designated data path; document where the agent should look.

### 3. Set up env (same as PHY600 on the laptop)

So the **local agent** in condenstate can SSH to AWS and use PHY600 when needed:

1. **Copy** `.env.example` to `.env` in condenstate repo root.
2. **Set** (at least when driving cloud/SSH workflows):
   - `MAGNIPHYQ_IP` (or leave unset and resolve via AWS CLI),
   - `PHY600_ROOT` (e.g. `~/PHY600`),
   - `SSH_KEY_PATH` (e.g. `~/.ssh/pax-ec2-key.pem`) if different from default.
3. **Do not commit** `.env`. See `.meta/docs/ENV_AND_ORCHESTRATION.md`.

After that, the agent in condenstate has the same env “shape” as in PHY600 (key path, magniphyq resolution, PHY600 path) and can coordinate with cloud agents or run pipeline steps that need SSH/registry/data.

---

## One-line summary for the orchestrator

**Condenstate agent is live and cleared for resume and paper1/paper2 workflows. To start: have the agent run eval (`eval_gates.py --report --block`), then follow the readiness checklist (IMPORT_FROM_PHY600 + CONDENSTATE_GAP_AND_CONTENT), and set env from `.env.example` so it has the same SSH/PHY600/magniphyq context as the laptop PHY600 agent.**
