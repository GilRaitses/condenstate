<!--
LIFECYCLE_ID: mirror-local-20260211-0001
DECISION_KIND: sst_index
DECISION_SCOPE_JSON: {"od_pair":"project:condenstate","graph_id":"condenstate-canon-v1","run_id":"condenstate-manifest-0001","lifecycle_id":"mirror-local-20260211-0001"}
DECISION_IDENTITY_FIELDS_JSON: {"repo_commit":"39f57f49eeae6e87490a9cd4a1e0c20367036526","objective_hash":"1111111111111111111111111111111111111111111111111111111111111111","graph_hash":"2222222222222222222222222222222222222222222222222222222222222222","params_hash":"3333333333333333333333333333333333333333333333333333333333333333"}
-->

# condenstate `.sst` onboarding index

`.sst` is the canonical state surface and `.ddb` is the canonical decision surface for this repository mirror. The active worker targets are Paper 1 (`.sst/paper1/*`) and Paper 2 (`.sst/paper2/*`), with run outputs under `.meta/runs/` and figures under `.meta/figs/`.

## Canon read order

1. `.sst/index.md`
2. `.sst/layout_policy.md`
3. `.sst/claims_matrix.json`
4. `.sst/evidence_index.json`
5. `.sst/paper1/objective_spec.json`
6. `.sst/paper1/sweep_manifest.json`
7. `.sst/paper2/objective_spec.json`

## Canon layout

```text
.sst/
  index.md
  next_agent_boot.md
  resume_protocol.md
  layout_policy.md
  claims_matrix.json
  evidence_index.json
  paper1/
  paper2/
```

`.sst/paper1` and `.sst/paper2` are first-class program surfaces referenced from `.sst/run_manifest.json`.

## Markdown header contract

Markdown artifacts that should be registered by `.ddb/tools/register_sst.py` must begin with an HTML comment header containing:

1. `LIFECYCLE_ID`
2. `DECISION_KIND`
3. `DECISION_SCOPE_JSON`
4. `DECISION_IDENTITY_FIELDS_JSON`

`parse_md_header()` reads key-value pairs from the comment block, and `parse_md_artifact()` consumes `DECISION_KIND`, `DECISION_SCOPE_JSON`, `DECISION_IDENTITY_FIELDS_JSON`, and `LIFECYCLE_ID` to build the registry record.

## JSON contract parsed by registry adapter

JSON artifacts should include:

- `artifact_kind`
- `decision_scope`
- `identity_fields`
- `lifecycle_id`

`parse_json_artifact()` reads these keys directly; `canonical_scope()` normalizes scope keys (`od_pair`, `graph_id`, `run_id`, `lifecycle_id`), and `canonical_identity()` enforces required identity keys (`repo_commit`, `objective_hash`, `graph_hash`, `params_hash`).

## Worker write policy

1. Write run products only under `.meta/runs/` and `.meta/figs/` at first.
2. Write to `.sst/paper*/` only when a `.meta` artifact exists and can be bound by a new evidence slice.
3. After any `.sst` write, run `.ddb/tools/register_sst.py` and commit.

Use `.sst/next_agent_boot.md` for executable boot commands and refusal gates.
