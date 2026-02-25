# PHY600 dot-surface audit for clean mirror

## Audit basis

This audit is based on the file-tree snapshot captured in `synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md`. `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L1-L4]`

PHY600 root currently contains `.sst` with 24 files and `.ddb` with 3 files. `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L7-L42]`

Root `.sstate` and `.decisiondb` are absent in this repository state. `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L43-L46]`

## Canonical surface expectations used in this mirror

PHY600 documentation defines `.sst` as operational state and `.ddb` as deterministic registry, which is the canonical model mirrored here. `[.meta/docs/SST_DDB_CRASHCOURSE.md:L5-L15]`

The mirror was created with local `.sst`, `.ddb`, and `.meta` surfaces and lifecycle/rehydration files under `.sst/system`. `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L47-L70]`

## Comparison: PHY600 root vs minimal clean mirror

| Surface requirement | PHY600 root status | Mirror status | Evidence |
|---|---|---|---|
| Canonical state surface (`.sst`) | present | present | `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L7-L31]` `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L49-L60]` |
| Canonical decision surface (`.ddb`) | present | present | `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L33-L41]` `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L61-L65]` |
| Rehydration pointer (`.sst/system/CURRENT`) | not present at root | present in mirror | `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L7-L31]` `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L56-L58]` |
| Rehydration snapshot (`.sst/system/state_snapshot_*.json`) | not present at root | present in mirror | `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L7-L31]` `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L56-L58]` |
| Local lifecycle guard tool | present in PHY600 (`.sst/tools/lifecycle_guard.py`) | mirrored as local-only guard | `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L30-L31]` `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L59-L60]` |
| Legacy `.sstate/.decisiondb` surfaces | missing (root has none) | intentionally not created | `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L43-L46]` |

Mirror reconstruction checks preserve the same minimum dimensions used by PHY600 today: a `reconstruction_tests` array with `name` and `result` entries plus summary counts and status fields. `[.sst/reconstruction_check.json:L16-L34]` `[synapsin_mirror/.sst/reconstruction_check.json:L22-L40]`

## Pax-specific or cloud-bound artifacts to strip from clean mirror exports

Root monitor architecture contract contains hardcoded external frontend/backend host targets, so it must be stripped from mirror-local exports. `[.sst/monitor_architecture.json:L18-L26]`

Companion monitor architecture documentation also contains hardcoded external host targets and should not be exported to a host-agnostic mirror. `[.meta/docs/MONITOR_ARCHITECTURE.md:L9-L10]`

Cloud tunnel configuration includes host binding plus tunnel install credential material and is blocked. `[.cursor/rules/cloudflare-tunnel-config.mdc:L10-L23]`

Private-key material exists under `.ssh` and is blocked from any export. `[.ssh/pax-ec2-key.pem:L1-L1]`

EC2 deployment instructions with hardcoded instance and endpoint details are cloud-bound operational notes and are blocked from clean mirror export. `[Presentations/synapsin_modeling/EC2_DEPLOYMENT.md:L7-L18]` `[Presentations/synapsin_modeling/EC2_DEPLOYMENT.md:L67-L68]`

Pipeline config with hardcoded remote endpoint and SSH key assumptions is environment-bound and blocked from mirror export. `[rerun_v2/pipeline/config.sh:L15-L18]` `[rerun_v2/pipeline/config.sh:L26-L27]`

## Summary

PHY600 already has canonical `.sst/.ddb` root surfaces suitable as source material, and the new `synapsin_mirror` now provides a minimal clean bootstrap that excludes legacy `.sstate/.decisiondb` creation and isolates cloud-bound artifacts behind explicit block rules. `[synapsin_mirror/.meta/reports/PHY600_TREE_SNAPSHOT.md:L7-L70]` `[synapsin_mirror/EXPORT_MANIFEST.md:L32-L44]`
