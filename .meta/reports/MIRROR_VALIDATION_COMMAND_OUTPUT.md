# mirror validation command output

Command bundle executed from mirror root:

```text
.
new_decision_ids: none
{
  "allowed": true,
  "checks": {
    "contract_active_in_registry": true,
    "current_snapshot_exists": true,
    "current_snapshot_managed": true,
    "decisiondb_identity_fields_no_unset": true,
    "evidence_hashes_match_raw": true,
    "lifecycle_index_match": true,
    "manifest_contract_match": true,
    "orphan_free": true,
    "override_enabled_if_needed": true,
    "reconstructable": true,
    "reconstruction_lifecycle_match": true,
    "requested_lifecycle_match": true,
    "summary_pass": true,
    "supported_claims_have_evidence_refs": true
  },
  "contract_hash": "c7c2143fe16663f83da1c5c6d3926c4a7976387178c8c94073c21806fde1c730",
  "evidence_hash_violations": [],
  "lifecycle_id": "mirror-local-20260211-0001",
  "orphan_count": 0,
  "override_enabled": false,
  "supported_claim_violations": [],
  "unset_violations": [],
  "reasons": []
}
```
