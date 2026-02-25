# Orchestration plan (canon)

**Sequencing.** Plan memo first, then parallel workers A and B. No worker edits this memo; they read it and run their assigned tasks.

**Ownership.**

- **claims_matrix** (`.sst/claims_matrix.json`): Single owner. One designated worker or the orchestrator updates it; parallel workers do not edit it unless assigned.
- **evidence_index** (`.sst/evidence_index.json`): Single owner. One designated worker or the orchestrator updates it; parallel workers do not edit it unless assigned.

**What “cleared” means.** All of the following are true:

- **eval_gates pass:** `python3 .sst/tools/eval_gates.py --block` exits 0 and overall is pass.
- **local_readiness pass:** Checks in `.meta/docs/DIRECTIVE_LOCAL_READINESS_CHECK.md` are satisfied (scripts, data, env_file, ssh_key, cursor_rules); readiness block reports `ready: yes`.
- **magniphyq status fields:** From `.meta/docs/DIRECTIVE_LOCAL_VERIFY_MAGNIPHYQ_AND_DATA.md`: `magniphyq_reachable: yes`, `condenstate_on_magniphyq: yes`, `data_dir_ok: yes`, and data size ~4GB or greater.

**Every worker on boot.** Each worker must run, in order:

1. `git pull origin main`
2. `python3 .sst/tools/eval_gates.py --block`
3. Then proceed with assigned work.

Workers must not push or commit unless the plan or orchestrator assigns that role.
