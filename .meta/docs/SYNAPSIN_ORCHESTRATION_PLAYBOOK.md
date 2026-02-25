# SYNAPSIN ORCHESTRATION PLAYBOOK

## Purpose

This playbook adapts the existing `synapsin_mirror` lifecycle/reconstruction surfaces for the `condenstate` repository so workers can execute Paper 1 and Paper 2 programs against one shared canon.

## Canonical surfaces

- `.sst` is canonical state.
- `.ddb` is canonical decision registry.
- `.meta` stores run and figure artifacts produced by workers.

## First-class paper targets

- Paper 1 canon: `.sst/paper1/*`
- Paper 2 canon: `.sst/paper2/*`

Both paper targets are referenced from `.sst/run_manifest.json` under `paper_targets` and `runs`.

## Worker read order

1. `.sst/index.md`
2. `.sst/layout_policy.md`
3. `.sst/credentials_policy.md`
4. `.sst/claims_matrix.json`
5. `.sst/evidence_index.json`
6. `.sst/paper1/objective_spec.json`
7. `.sst/paper1/sweep_manifest.json`
8. `.sst/paper2/objective_spec.json`

## Credentials (agent rehydration)

Every agent must be aware of the credentials policy on boot and rehydration. Read `.sst/credentials_policy.md`. Secrets are never in the repo; they are set in `.env` (local) or Cursor environment/secrets (cloud). Required: `PHY600_ROOT`, `SSH_KEY_PATH` (or default), optionally `MAGNIPHYQ_IP`. See `.meta/docs/SECRETS_FOR_CLOUD_AGENTS.md` for cloud setup.

## Write discipline

1. Initial writes go to:
   - `.meta/runs/paper1/`
   - `.meta/runs/paper2/`
   - `.meta/figs/paper1/`
   - `.meta/figs/paper2/`
2. Update `.sst/paper1/*` or `.sst/paper2/*` only after evidence-bearing outputs exist in `.meta`.
3. After every `.sst` change:
   - run `python3 .ddb/tools/register_sst.py`
   - commit updated `.sst/.ddb`

## Refusal gates

A worker must refuse to continue if:

1. any canon JSON file contains `UNSET` in `decisiondb_identity_fields`
2. any claim with `status = supported` has empty `evidence_refs`
3. any evidence record hash does not match referenced raw artifact

## Resume discipline

Use:

```bash
python3 .sst/tools/lifecycle_guard.py
python3 .ddb/tools/register_sst.py
```

Resume is blocked if lifecycle mismatch, orphan snapshots, reconstruction failure, or explicit refusal gates are present.

## Eval directives (completeness report)

To test all gates and contracts and get a single completeness report:

```bash
make eval
# or
python3 .sst/tools/eval_gates.py
```

- **Exit 0:** all pass (register_sst, lifecycle_guard allowed, canon layout complete).
- **Exit 1:** register_sst failed.
- **Exit 2:** lifecycle_guard disallowed (one or more resume gates failed).
- **Exit 3:** canon layout incomplete (missing required .sst/.ddb files).

Options:

- `--report` — also write `.meta/reports/completeness_<timestamp>.md`.
- `--json` — print machine-readable JSON only (for CI).
