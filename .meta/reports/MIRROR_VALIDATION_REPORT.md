# mirror validation report

## Commands executed

Validation was run from inside `synapsin_mirror` and captured in `MIRROR_VALIDATION_COMMAND_OUTPUT.md`. `[synapsin_mirror/.meta/reports/MIRROR_VALIDATION_COMMAND_OUTPUT.md:L1-L9]`

Executed commands:

1. `python3 ".ddb/tools/register_sst.py"`
2. `python3 ".sst/tools/lifecycle_guard.py"`

Both outputs are recorded in the captured command output file. `[synapsin_mirror/.meta/reports/MIRROR_VALIDATION_COMMAND_OUTPUT.md:L6-L39]`

## Adapter validation

Registration completed with no new decision IDs after the integration write (`new_decision_ids: none`), indicating deterministic convergence on current canonical surfaces. `[synapsin_mirror/.meta/reports/MIRROR_VALIDATION_COMMAND_OUTPUT.md:L6-L6]`

Parity with PHY600 canonical contract was preserved:

- Original protocol defines JSON and text canonicalization rules and the decision-id formula with `artifact_hash`. `[.ddb/PROTOCOL.md:L5-L16]` `[.ddb/PROTOCOL.md:L33-L35]`
- Original adapter implements matching canonicalization functions and decision-id computation fields. `[.ddb/tools/register_sst.py:L21-L33]` `[.ddb/tools/register_sst.py:L92-L100]`
- Mirror adapter keeps the same canonicalization and decision-id formula behavior. `[synapsin_mirror/.ddb/tools/register_sst.py:L24-L35]` `[synapsin_mirror/.ddb/tools/register_sst.py:L95-L102]`

Canonicalization rules validated in code path:

- JSON canonicalization uses sorted keys, compact separators, UTF-8 bytes. `[synapsin_mirror/.ddb/tools/register_sst.py:L24-L26]`
- Text canonicalization normalizes line endings, trims trailing whitespace, UTF-8 bytes. `[synapsin_mirror/.ddb/tools/register_sst.py:L28-L31]`
- SHA256 hashing function is shared for both artifact types. `[synapsin_mirror/.ddb/tools/register_sst.py:L34-L35]`

Decision-id computation validated in code path:

- Decision ID is `sha256(canonical_json({kind, scope, identity_fields, artifact_hash}))`. `[synapsin_mirror/.ddb/tools/register_sst.py:L95-L102]`

Registry write semantics validated in code path:

- Adapter writes registry entries in non-dry-run mode and reports decision IDs when created. `[synapsin_mirror/.ddb/tools/register_sst.py:L337-L345]`
- Adapter dry-run path remains available and no-write. `[synapsin_mirror/.ddb/tools/register_sst.py:L324-L335]`

Mirror confinement validated in code path and runtime:

- Adapter root is anchored to `parents[2]` (the mirror root for this copied script path). `[synapsin_mirror/.ddb/tools/register_sst.py:L15-L18]`
- Runtime working directory confirms execution from mirror root (`.`). `[synapsin_mirror/.meta/reports/MIRROR_VALIDATION_COMMAND_OUTPUT.md:L5-L5]`

## Lifecycle gate validation

Lifecycle guard returned `"allowed": true`. `[synapsin_mirror/.meta/reports/MIRROR_VALIDATION_COMMAND_OUTPUT.md:L19-L21]`

Reconstruction and lifecycle checks were true, including `reconstructable`, lifecycle matches, orphan-free state, empty reasons list, and the added refusal-gate checks for decision identities, claims-evidence linkage, and evidence hash validation. `[synapsin_mirror/.meta/reports/MIRROR_VALIDATION_COMMAND_OUTPUT.md:L22-L39]`

`contract_active_in_registry` is true after registration, satisfying override preconditions if needed. `[synapsin_mirror/.meta/reports/MIRROR_VALIDATION_COMMAND_OUTPUT.md:L21-L24]`

## Result

Mirror local validation passed for deterministic registration, lifecycle gate execution, and refusal-gate enforcement checks.
