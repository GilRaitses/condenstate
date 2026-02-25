<!--
LIFECYCLE_ID: mirror-local-20260211-0001
DECISION_KIND: next_agent_boot
DECISION_SCOPE_JSON: {"od_pair":"project:condenstate","graph_id":"condenstate-canon-v1","run_id":"condenstate-manifest-0001","lifecycle_id":"mirror-local-20260211-0001"}
DECISION_IDENTITY_FIELDS_JSON: {"repo_commit":"39f57f49eeae6e87490a9cd4a1e0c20367036526","objective_hash":"1111111111111111111111111111111111111111111111111111111111111111","graph_hash":"2222222222222222222222222222222222222222222222222222222222222222","params_hash":"3333333333333333333333333333333333333333333333333333333333333333"}
-->

# Next agent boot

## Read order

1. `.sst/index.md`
2. `.sst/layout_policy.md`
3. `.sst/credentials_policy.md`
4. `.sst/claims_matrix.json`
5. `.sst/evidence_index.json`
6. `.sst/paper1/objective_spec.json`
7. `.sst/paper1/sweep_manifest.json`
8. `.sst/paper2/objective_spec.json`

## Write locations

1. Write only under `.meta/runs/` and `.meta/figs/` initially.
2. Write under `.sst/paper*/` only after `.meta` output exists and a new evidence slice can be registered.
3. After any `.sst` write:
   - run `python3 .ddb/tools/register_sst.py`
   - commit the updated `.sst/.ddb` surfaces

## Credentials awareness

Every agent (local or cloud) must be aware of the credentials policy on boot and rehydration. Read `.sst/credentials_policy.md`. Secrets are never in the repo; they are set in `.env` (local) or Cursor's environment/secrets (cloud). Required: `PHY600_ROOT`, `SSH_KEY_PATH` (or default), and optionally `MAGNIPHYQ_IP`. Before running SSH or pipeline steps that need PHY600 or magniphyq, verify env and key path; if missing, report the gap and do not proceed. See `.meta/docs/SECRETS_FOR_CLOUD_AGENTS.md`.

## Refusal gates

Refuse execution when any gate fails:

1. any canon JSON file has `UNSET` in `decisiondb_identity_fields`
2. a claim marked `supported` has empty `evidence_refs`
3. an evidence slice hash does not match its raw file

## Local commands

```bash
python3 .sst/tools/lifecycle_guard.py
python3 .ddb/tools/register_sst.py
```
