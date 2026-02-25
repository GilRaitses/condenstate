#!/usr/bin/env python3
"""Local lifecycle gate checks for mirror resume safety."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SST_DIR = ROOT / ".sst"
DDB_REGISTRY = ROOT / ".ddb" / "registry.json"
RUN_MANIFEST = SST_DIR / "run_manifest.json"
LIFECYCLE_CONTRACT = SST_DIR / "lifecycle_contract.md"
LIFECYCLE_INDEX = SST_DIR / "lifecycle_index.json"
RECONSTRUCTION_CHECK = SST_DIR / "reconstruction_check.json"
SYSTEM_CURRENT = SST_DIR / "system" / "CURRENT"
CLAIMS_MATRIX = SST_DIR / "claims_matrix.json"
EVIDENCE_INDEX = SST_DIR / "evidence_index.json"


def canonical_text_hash(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    normalized = "\n".join(line.rstrip() for line in lines).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_contract_payload() -> dict[str, Any]:
    text = LIFECYCLE_CONTRACT.read_text(encoding="utf-8")
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if not match:
        raise ValueError("lifecycle_contract.md missing fenced JSON payload")
    return json.loads(match.group(1))


def contract_is_active_in_registry(contract_hash: str, lifecycle_id: str) -> bool:
    if not DDB_REGISTRY.exists():
        return False
    registry = load_json(DDB_REGISTRY)
    for entry in registry.get("entries", []):
        if entry.get("status") != "active":
            continue
        if entry.get("kind") != "lifecycle_contract":
            continue
        if entry.get("artifact_path") != ".sst/lifecycle_contract.md":
            continue
        if entry.get("artifact_hash") != contract_hash:
            continue
        scope = entry.get("scope", {})
        if scope.get("lifecycle_id") == lifecycle_id:
            return True
    return False


def current_snapshot_path() -> Path:
    rel_name = SYSTEM_CURRENT.read_text(encoding="utf-8").strip()
    if not rel_name:
        raise ValueError(".sst/system/CURRENT is empty")
    return SST_DIR / "system" / rel_name


def json_pointer_get(obj: Any, pointer: str) -> Any:
    if pointer == "":
        return obj
    if not pointer.startswith("/"):
        raise ValueError(f"invalid json pointer: {pointer}")
    current = obj
    for token in pointer.lstrip("/").split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(token)]
        elif isinstance(current, dict):
            current = current[token]
        else:
            raise KeyError(pointer)
    return current


def canon_json_paths() -> list[Path]:
    paths: list[Path] = []
    for path in SST_DIR.glob("**/*.json"):
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        if rel.startswith(".sst/tools/"):
            continue
        paths.append(path)
    return sorted(paths)


def decision_identity_fields_have_no_unset() -> tuple[bool, list[str]]:
    violations: list[str] = []
    for path in canon_json_paths():
        payload = load_json(path)
        identity = payload.get("decisiondb_identity_fields")
        if not isinstance(identity, dict):
            continue
        for key, value in identity.items():
            if "UNSET" in str(value):
                violations.append(f"{path.relative_to(ROOT)}:{key}")
    return len(violations) == 0, violations


def supported_claims_have_evidence() -> tuple[bool, list[str]]:
    if not CLAIMS_MATRIX.exists():
        return False, ["missing .sst/claims_matrix.json"]
    payload = load_json(CLAIMS_MATRIX)
    violations: list[str] = []
    for claim in payload.get("claims", []):
        if str(claim.get("status", "")).lower() != "supported":
            continue
        evidence_refs = claim.get("evidence_refs", [])
        if not isinstance(evidence_refs, list) or len(evidence_refs) == 0:
            violations.append(str(claim.get("claim_id", "unknown_claim")))
    return len(violations) == 0, violations


def evidence_hashes_match() -> tuple[bool, list[str]]:
    if not EVIDENCE_INDEX.exists():
        return False, ["missing .sst/evidence_index.json"]
    payload = load_json(EVIDENCE_INDEX)
    violations: list[str] = []
    for record in payload.get("evidence", []):
        evidence_id = str(record.get("evidence_id", "unknown_evidence"))
        raw_path = str(record.get("raw_path", ""))
        raw_file_sha = str(record.get("raw_file_sha256", ""))
        slice_sha = str(record.get("slice_sha256", ""))
        pointer = str(record.get("range", {}).get("json_pointer", ""))

        if not raw_path:
            violations.append(f"{evidence_id}:missing_raw_path")
            continue
        if "UNSET" in raw_file_sha or "UNSET" in slice_sha:
            violations.append(f"{evidence_id}:unset_hash")
            continue

        abs_raw = ROOT / raw_path
        if not abs_raw.exists():
            violations.append(f"{evidence_id}:raw_missing:{raw_path}")
            continue

        raw_bytes = abs_raw.read_bytes()
        calc_raw = hashlib.sha256(raw_bytes).hexdigest()
        if calc_raw != raw_file_sha:
            violations.append(f"{evidence_id}:raw_hash_mismatch")
            continue

        if pointer:
            try:
                raw_obj = json.loads(raw_bytes.decode("utf-8"))
                slice_value = json_pointer_get(raw_obj, pointer)
                slice_bytes = json.dumps(slice_value, sort_keys=True, separators=(",", ":")).encode("utf-8")
            except Exception:
                violations.append(f"{evidence_id}:invalid_json_pointer")
                continue
        else:
            slice_bytes = raw_bytes

        calc_slice = hashlib.sha256(slice_bytes).hexdigest()
        if calc_slice != slice_sha:
            violations.append(f"{evidence_id}:slice_hash_mismatch")
    return len(violations) == 0, violations


def evaluate_resume_gates(expected_lifecycle_id: str | None = None) -> dict[str, Any]:
    manifest = load_json(RUN_MANIFEST)
    lifecycle_index = load_json(LIFECYCLE_INDEX)
    reconstruction = load_json(RECONSTRUCTION_CHECK)
    contract_payload = extract_contract_payload()
    contract_text = LIFECYCLE_CONTRACT.read_text(encoding="utf-8")
    contract_hash = canonical_text_hash(contract_text)

    manifest_lifecycle = str(manifest.get("lifecycle_id", ""))
    contract_lifecycle = str(contract_payload.get("lifecycle_id", ""))
    lifecycle_index_lifecycle = str(lifecycle_index.get("lifecycle_id", ""))
    reconstruction_lifecycle = str(reconstruction.get("lifecycle_id", ""))

    reasons: list[str] = []
    checks: dict[str, bool] = {}

    checks["manifest_contract_match"] = manifest_lifecycle == contract_lifecycle
    if not checks["manifest_contract_match"]:
        reasons.append("abort: lifecycle_id mismatch between run_manifest and lifecycle_contract")

    checks["lifecycle_index_match"] = lifecycle_index_lifecycle == contract_lifecycle
    if not checks["lifecycle_index_match"]:
        reasons.append("abort: lifecycle_id mismatch between lifecycle_index and lifecycle_contract")

    checks["reconstruction_lifecycle_match"] = reconstruction_lifecycle == contract_lifecycle
    if not checks["reconstruction_lifecycle_match"]:
        reasons.append("abort: lifecycle_id mismatch between reconstruction_check and lifecycle_contract")

    checks["reconstructable"] = bool(reconstruction.get("reconstructable", False))
    if not checks["reconstructable"]:
        reasons.append("abort: reconstruction_check.reconstructable is false")

    checks["summary_pass"] = reconstruction.get("summary", {}).get("status") == "pass"
    if not checks["summary_pass"]:
        reasons.append("abort: reconstruction_check summary status is not pass")

    if expected_lifecycle_id is not None:
        checks["requested_lifecycle_match"] = expected_lifecycle_id == contract_lifecycle
        if not checks["requested_lifecycle_match"]:
            reasons.append("abort: lifecycle_id mismatch against requested lifecycle_id")
    else:
        checks["requested_lifecycle_match"] = True

    orphan_count = int(lifecycle_index.get("orphan_count", 0))
    checks["orphan_free"] = orphan_count == 0

    current_snapshot = current_snapshot_path()
    checks["current_snapshot_exists"] = current_snapshot.exists()
    if not checks["current_snapshot_exists"]:
        reasons.append("abort: current snapshot referenced by .sst/system/CURRENT is missing")

    managed_refs = set(lifecycle_index.get("managed_snapshot_refs", []))
    current_rel = str(current_snapshot.relative_to(ROOT)) if current_snapshot.exists() else ""
    checks["current_snapshot_managed"] = current_rel in managed_refs
    if checks["current_snapshot_exists"] and not checks["current_snapshot_managed"]:
        reasons.append("abort: current snapshot is not in lifecycle_index managed_snapshot_refs")

    orphan_override = contract_payload.get("orphan_override_rule", {})
    override_enabled = bool(orphan_override.get("enabled", False))
    checks["override_enabled_if_needed"] = checks["orphan_free"] or override_enabled
    if orphan_count > 0 and not override_enabled:
        reasons.append("abort: orphan snapshots detected and override is not explicitly enabled")

    checks["contract_active_in_registry"] = contract_is_active_in_registry(contract_hash, contract_lifecycle)
    if orphan_count > 0 and override_enabled and not checks["contract_active_in_registry"]:
        reasons.append("abort: orphan override enabled but updated lifecycle contract is not active in .ddb registry")

    checks["decisiondb_identity_fields_no_unset"], unset_violations = decision_identity_fields_have_no_unset()
    if not checks["decisiondb_identity_fields_no_unset"]:
        reasons.append("abort: UNSET found in decisiondb_identity_fields")

    checks["supported_claims_have_evidence_refs"], supported_claim_violations = supported_claims_have_evidence()
    if not checks["supported_claims_have_evidence_refs"]:
        reasons.append("abort: supported claim missing evidence_refs")

    checks["evidence_hashes_match_raw"], evidence_hash_violations = evidence_hashes_match()
    if not checks["evidence_hashes_match_raw"]:
        reasons.append("abort: evidence hash mismatch or invalid evidence record")

    allowed = len(reasons) == 0
    return {
        "allowed": allowed,
        "lifecycle_id": contract_lifecycle,
        "checks": checks,
        "orphan_count": orphan_count,
        "override_enabled": override_enabled,
        "contract_hash": contract_hash,
        "unset_violations": unset_violations,
        "supported_claim_violations": supported_claim_violations,
        "evidence_hash_violations": evidence_hash_violations,
        "reasons": reasons,
    }


def main() -> int:
    result = evaluate_resume_gates()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
