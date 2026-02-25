<!--
LIFECYCLE_ID: mirror-local-20260211-0001
DECISION_KIND: layout_policy
DECISION_SCOPE_JSON: {"od_pair":"project:condenstate","graph_id":"condenstate-canon-v1","run_id":"condenstate-manifest-0001","lifecycle_id":"mirror-local-20260211-0001"}
DECISION_IDENTITY_FIELDS_JSON: {"repo_commit":"39f57f49eeae6e87490a9cd4a1e0c20367036526","objective_hash":"1111111111111111111111111111111111111111111111111111111111111111","graph_hash":"2222222222222222222222222222222222222222222222222222222222222222","params_hash":"3333333333333333333333333333333333333333333333333333333333333333"}
-->

# `.sst` layout policy

## Role of each root surface

1. `.sst` is durable canonical state and should not be treated as scratch output.
2. `.ddb` is the deterministic decision registry for canonical artifact hashes.
3. `.meta` is worker output storage and can be overwritten by reruns.

## Canonical on-disk layout

```text
.sst/
  credentials_policy.md
  claims_matrix.json
  evidence_index.json
  paper1/
    objective_spec.json
    sweep_manifest.json
    eta_mapping.json
    phase_boundaries.json
    figure_manifest.json
  paper2/
    objective_spec.json
    model_spec.json
    sweep_manifest.json
    figure_manifest.json
    bridge_notes.md
```

## Write constraints

1. Initial worker writes must go to `.meta/runs/` and `.meta/figs/`.
2. A worker may write to `.sst/paper1/*` or `.sst/paper2/*` only when corresponding `.meta` artifacts exist and are linked via `evidence_index`.
3. After any `.sst` write, run `python3 .ddb/tools/register_sst.py` and commit.
