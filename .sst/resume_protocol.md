<!--
LIFECYCLE_ID: mirror-local-20260211-0001
DECISION_KIND: resume_protocol
DECISION_SCOPE_JSON: {"od_pair":"project:condenstate","graph_id":"condenstate-canon-v1","run_id":"condenstate-manifest-0001","lifecycle_id":"mirror-local-20260211-0001"}
DECISION_IDENTITY_FIELDS_JSON: {"repo_commit":"39f57f49eeae6e87490a9cd4a1e0c20367036526","objective_hash":"1111111111111111111111111111111111111111111111111111111111111111","graph_hash":"2222222222222222222222222222222222222222222222222222222222222222","params_hash":"3333333333333333333333333333333333333333333333333333333333333333"}
-->

# Resume protocol

- lifecycle_id: `mirror-local-20260211-0001`

## Mandatory resume gates

1. **Reconstruction gate**
   - abort when `.sst/reconstruction_check.json` has `reconstructable: false`.

2. **Lifecycle gate**
   - abort when lifecycle_id differs across:
     - `.sst/run_manifest.json`
     - `.sst/lifecycle_contract.md`
     - `.sst/lifecycle_index.json`

3. **Orphan snapshot gate**
   - abort when `orphan_count > 0` in `.sst/lifecycle_index.json`

4. **Override gate**
   - continuation is allowed with orphan snapshots only if:
     - `orphan_override_rule.enabled` is true in `.sst/lifecycle_contract.md`, and
     - that exact contract hash is active in `.ddb/registry.json`

5. **Decision identity gate**
   - abort when any canon JSON artifact under `.sst/` has `UNSET` in `decisiondb_identity_fields`

6. **Claims-evidence gate**
   - abort when any claim with `status = supported` has no `evidence_refs`

7. **Evidence hash gate**
   - abort when `slice_sha256` or `raw_file_sha256` does not match its referenced raw artifact

## Resume sequence

1. run local lifecycle checks (`python3 .sst/tools/lifecycle_guard.py`)
2. run registry registration (`python3 .ddb/tools/register_sst.py`)
3. verify canonical gates in `.sst/next_agent_boot.md`
4. verify reconstruction summary status is `pass`
5. continue local run orchestration only after all gates pass
