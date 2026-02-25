<!--
LIFECYCLE_ID: mirror-local-20260211-0001
DECISION_KIND: lifecycle_contract
DECISION_SCOPE_JSON: {"od_pair":"project:condenstate","graph_id":"condenstate-canon-v1","run_id":"condenstate-manifest-0001","lifecycle_id":"mirror-local-20260211-0001"}
DECISION_IDENTITY_FIELDS_JSON: {"repo_commit":"39f57f49eeae6e87490a9cd4a1e0c20367036526","objective_hash":"1111111111111111111111111111111111111111111111111111111111111111","graph_hash":"2222222222222222222222222222222222222222222222222222222222222222","params_hash":"3333333333333333333333333333333333333333333333333333333333333333"}
-->

# Lifecycle contract

- lifecycle_id: `mirror-local-20260211-0001`
- created_at: `2026-02-24T00:00:00Z`
- parent_lifecycle_id: `null`
- owning_branch: `main`
- owning_commit_at_creation: `39f57f49eeae6e87490a9cd4a1e0c20367036526`
- cloud_region_scope: `[]`

## Contract payload

```json
{
  "lifecycle_id": "mirror-local-20260211-0001",
  "created_at": "2026-02-24T00:00:00Z",
  "parent_lifecycle_id": null,
  "owning_branch": "main",
  "owning_commit_at_creation": "39f57f49eeae6e87490a9cd4a1e0c20367036526",
  "cloud_region_scope": [],
  "resource_scope_rules": {
    "managed_resources": [
      ".sst/system/CURRENT",
      ".sst/system/state_snapshot_20260211T000000Z.json",
      ".sst/paper1/objective_spec.json",
      ".sst/paper2/objective_spec.json"
    ],
    "orphan_definition": "state snapshots present under .sst/system that are not referenced by .sst/system/CURRENT",
    "tag_scope": {
      "project": "synapsin_mirror",
      "managed_by": "local_lifecycle_guard",
      "lifecycle_id": "mirror-local-20260211-0001"
    }
  },
  "termination_invariant": {
    "definition": "no orphan local state snapshots and reconstruction_check.reconstructable remains true",
    "enforced_by": [
      ".sst/tools/lifecycle_guard.py"
    ]
  },
  "successor_rule": {
    "definition": "new lifecycle is required when lifecycle_id mismatch is detected or lifecycle contract scope changes",
    "requirements": [
      "set parent_lifecycle_id to current lifecycle_id",
      "write new lifecycle_contract.md payload",
      "write updated lifecycle_id in all execution-state artifacts",
      "run python3 .ddb/tools/register_sst.py"
    ]
  },
  "orphan_override_rule": {
    "enabled": false,
    "reason": null,
    "approved_by": null,
    "approved_at": null,
    "requires_active_registry_contract_hash": true
  }
}
```

## Resume gates

1. Abort on lifecycle_id mismatch across run manifest, lifecycle contract, and lifecycle index.
2. Abort when orphan snapshots exist.
3. Allow continuation only when orphan override is explicitly enabled in this contract payload and the updated lifecycle contract hash is active in `.ddb/registry.json`.
