# .ddb Protocol for `.sst` lifecycle enforcement

This repository publishes monitoring and lifecycle decisions from `.sst` into `.ddb/registry.json`.

## Canonicalization

- JSON artifacts:
  - UTF-8 encoding
  - sort keys
  - compact separators (`","` and `":"`)
  - hash with `sha256`
- Text artifacts:
  - normalize line endings to LF
  - trim trailing whitespace per line
  - UTF-8 encoding
  - hash with `sha256`

## Registry schema

Each registry entry contains:

- `decision_id` (deterministic hash)
- `kind`
- `scope` (`od_pair`, `graph_id`, `run_id`, `lifecycle_id`)
- `identity_fields` (`repo_commit`, `objective_hash`, `graph_hash`, `params_hash`)
- `artifact_path` (repo-root-relative)
- `artifact_hash`
- `equivalence_policy`
- `provenance`
- `status` (`active` or `superseded`)
- `supersedes` (present when replacing equivalent active entry)

## Deterministic decision id

`decision_id = sha256(canonical_json({"kind", "scope", "identity_fields", "artifact_hash"}))`

## Supersede rule

If a new artifact has the same `kind + scope + identity_fields` as an active entry but a different hash:

1. mark existing active entries as `superseded`
2. add new entry with `status: active`
3. set `supersedes` to superseded decision IDs

If hash matches an active equivalent entry, no new entry is created.

## Contract with monitor backend

- Backend APIs must verify artifact hashes against active registry entries before serving panel data.
- Resume gates must refuse continuation when lifecycle contract hash is not active in registry.
- After any state update written into `.sst`, backend refresh must run `make ddb-register`.
