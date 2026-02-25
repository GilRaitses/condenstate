#!/usr/bin/env python3
"""Deterministically register .sst artifacts into .ddb/registry.json."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SST_DIR = ROOT / ".sst"
REGISTRY_PATH = ROOT / ".ddb" / "registry.json"
CONFIG_PATH = ROOT / ".ddb" / "register_config.json"

REQUIRED_SCOPE_KEYS = ("od_pair", "graph_id", "run_id", "lifecycle_id")
REQUIRED_IDENTITY_KEYS = ("repo_commit", "objective_hash", "graph_hash", "params_hash")


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_text_bytes(text: str) -> bytes:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    normalized = "\n".join(line.rstrip() for line in lines)
    return normalized.encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_scope(scope: dict[str, Any], fallback_lifecycle_id: str) -> dict[str, Any]:
    normalized = dict(scope)
    normalized.setdefault("od_pair", "unknown")
    normalized.setdefault("graph_id", "unknown")
    normalized.setdefault("run_id", "unknown")
    normalized.setdefault("lifecycle_id", fallback_lifecycle_id or "unknown")
    return {key: normalized.get(key) for key in REQUIRED_SCOPE_KEYS}


def canonical_identity(identity: dict[str, Any], defaults: dict[str, Any]) -> dict[str, str]:
    normalized = dict(defaults)
    normalized.update(identity)
    missing = [key for key in REQUIRED_IDENTITY_KEYS if not normalized.get(key)]
    if missing:
        raise ValueError(f"Missing identity_fields keys: {missing}")
    return {key: str(normalized[key]) for key in REQUIRED_IDENTITY_KEYS}


def parse_md_header(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if not stripped.startswith("<!--"):
        return {}
    start = text.find("<!--")
    end = text.find("-->", start + 4)
    if end == -1:
        return {}
    out: dict[str, str] = {}
    for line in text[start + 4 : end].splitlines():
        raw = line.strip()
        if not raw or ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        out[key.strip()] = value.strip()
    return out


@dataclass
class ArtifactRecord:
    kind: str
    scope: dict[str, Any]
    identity_fields: dict[str, str]
    artifact_path: str
    artifact_hash: str
    equivalence_policy: dict[str, Any]
    provenance: dict[str, Any]

    @property
    def equivalence_key(self) -> str:
        key_obj = {
            "kind": self.kind,
            "scope": self.scope,
            "identity_fields": self.identity_fields,
        }
        return sha256_hex(canonical_json_bytes(key_obj))

    @property
    def decision_id(self) -> str:
        key_obj = {
            "kind": self.kind,
            "scope": self.scope,
            "identity_fields": self.identity_fields,
            "artifact_hash": self.artifact_hash,
        }
        return sha256_hex(canonical_json_bytes(key_obj))


def read_defaults() -> tuple[dict[str, Any], dict[str, Any], str]:
    manifest_path = SST_DIR / "run_manifest.json"
    if not manifest_path.exists():
        return {}, {}, "unknown"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    default_scope = manifest.get("decision_scope", {})
    default_identity = manifest.get("identity_fields", {})
    lifecycle_id = str(manifest.get("lifecycle_id", "unknown"))
    return default_scope, default_identity, lifecycle_id


def parse_json_artifact(
    path: Path,
    default_scope: dict[str, Any],
    default_identity: dict[str, Any],
    fallback_lifecycle_id: str,
) -> ArtifactRecord:
    payload = json.loads(path.read_text(encoding="utf-8"))
    lifecycle_id = str(payload.get("lifecycle_id", fallback_lifecycle_id))
    scope = canonical_scope(payload.get("decision_scope", default_scope), lifecycle_id)
    identity = canonical_identity(payload.get("identity_fields", {}), default_identity)
    kind = payload.get("artifact_kind", path.stem)
    artifact_hash = sha256_hex(canonical_json_bytes(payload))
    return ArtifactRecord(
        kind=kind,
        scope=scope,
        identity_fields=identity,
        artifact_path=str(path.relative_to(ROOT)),
        artifact_hash=artifact_hash,
        equivalence_policy={
            "policy_name": "canonical_json_sha256",
            "canonicalization": "JSON sort keys, compact separators, UTF-8",
            "compare_fields": ["__full_json__"],
        },
        provenance={
            "source_artifact": str(path.relative_to(ROOT)),
            "source_type": "json",
            "generator": ".ddb/tools/register_sst.py",
        },
    )


def parse_md_artifact(
    path: Path,
    default_scope: dict[str, Any],
    default_identity: dict[str, Any],
    fallback_lifecycle_id: str,
) -> ArtifactRecord:
    text = path.read_text(encoding="utf-8")
    header = parse_md_header(path)
    lifecycle_id = header.get("LIFECYCLE_ID", fallback_lifecycle_id)
    if "DECISION_SCOPE_JSON" in header:
        scope_json = json.loads(header["DECISION_SCOPE_JSON"])
    else:
        scope_json = dict(default_scope)
    scope = canonical_scope(scope_json, lifecycle_id)
    if "DECISION_IDENTITY_FIELDS_JSON" in header:
        identity_json = json.loads(header["DECISION_IDENTITY_FIELDS_JSON"])
    else:
        identity_json = {}
    identity = canonical_identity(identity_json, default_identity)
    kind = header.get("DECISION_KIND", path.stem)
    artifact_hash = sha256_hex(canonical_text_bytes(text))
    return ArtifactRecord(
        kind=kind,
        scope=scope,
        identity_fields=identity,
        artifact_path=str(path.relative_to(ROOT)),
        artifact_hash=artifact_hash,
        equivalence_policy={
            "policy_name": "canonical_lf_trim_trailing_ws_sha256",
            "canonicalization": "LF normalize, trim trailing whitespace per line, UTF-8",
            "compare_fields": ["__full_text__"],
        },
        provenance={
            "source_artifact": str(path.relative_to(ROOT)),
            "source_type": "text",
            "generator": ".ddb/tools/register_sst.py",
        },
    )


def parse_artifact(
    path: Path,
    default_scope: dict[str, Any],
    default_identity: dict[str, Any],
    fallback_lifecycle_id: str,
) -> ArtifactRecord:
    if path.suffix == ".json":
        return parse_json_artifact(path, default_scope, default_identity, fallback_lifecycle_id)
    if path.suffix == ".md":
        return parse_md_artifact(path, default_scope, default_identity, fallback_lifecycle_id)
    raise ValueError(f"Unsupported artifact type: {path}")


def load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"schema_version": "1.0", "entries": []}
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if "entries" not in registry or not isinstance(registry["entries"], list):
        raise ValueError("Invalid .ddb/registry.json format")
    return registry


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"known_artifacts": [], "exclude_globs": [".sst/tools/**"]}
    payload = json.loads(path.read_text(encoding="utf-8"))
    known_artifacts = payload.get("known_artifacts", [])
    exclude_globs = payload.get("exclude_globs", [".sst/tools/**"])
    if not isinstance(known_artifacts, list):
        raise ValueError("register_config known_artifacts must be a list")
    if not isinstance(exclude_globs, list):
        raise ValueError("register_config exclude_globs must be a list")
    return {"known_artifacts": known_artifacts, "exclude_globs": exclude_globs}


def should_exclude(rel_path: str, patterns: list[str]) -> bool:
    normalized = rel_path.replace("\\", "/")
    return any(fnmatch(normalized, pattern) for pattern in patterns)


def collect_artifact_paths(config: dict[str, Any]) -> list[Path]:
    artifacts: list[Path] = []
    known_artifacts = [str(p) for p in config.get("known_artifacts", [])]
    exclude_globs = [str(p) for p in config.get("exclude_globs", [])]

    if known_artifacts:
        for relative_path in known_artifacts:
            path = ROOT / relative_path
            if not path.exists() or not path.is_file():
                continue
            if path.suffix not in {".json", ".md"}:
                continue
            rel = str(path.relative_to(ROOT))
            if should_exclude(rel, exclude_globs):
                continue
            artifacts.append(path)
    else:
        for path in sorted(SST_DIR.glob("**/*")):
            if not path.is_file():
                continue
            rel = str(path.relative_to(ROOT))
            if should_exclude(rel, exclude_globs):
                continue
            if path.suffix not in {".json", ".md"}:
                continue
            artifacts.append(path)
    return artifacts


def upsert_entries(registry: dict[str, Any], records: list[ArtifactRecord]) -> list[str]:
    entries = registry["entries"]
    created: list[str] = []
    for record in records:
        active_equivalent = [
            entry
            for entry in entries
            if entry.get("status") == "active"
            and entry.get("kind") == record.kind
            and entry.get("scope") == record.scope
            and entry.get("identity_fields") == record.identity_fields
        ]
        if any(entry.get("artifact_hash") == record.artifact_hash for entry in active_equivalent):
            continue

        superseded_ids = [entry["decision_id"] for entry in active_equivalent]
        for entry in active_equivalent:
            entry["status"] = "superseded"

        new_entry = {
            "decision_id": record.decision_id,
            "kind": record.kind,
            "scope": record.scope,
            "identity_fields": record.identity_fields,
            "artifact_path": record.artifact_path,
            "artifact_hash": record.artifact_hash,
            "equivalence_policy": record.equivalence_policy,
            "provenance": record.provenance,
            "status": "active",
        }
        if superseded_ids:
            new_entry["supersedes"] = superseded_ids

        entries.append(new_entry)
        created.append(record.decision_id)
    registry["entries"] = sorted(
        entries,
        key=lambda entry: (
            entry.get("kind", ""),
            json.dumps(entry.get("scope", {}), sort_keys=True, separators=(",", ":")),
            json.dumps(entry.get("identity_fields", {}), sort_keys=True, separators=(",", ":")),
            entry.get("decision_id", ""),
        ),
    )
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description="Register .sst artifacts into .ddb/registry.json")
    parser.add_argument("--dry-run", action="store_true", help="Compute registrations but do not write registry")
    parser.add_argument(
        "--config",
        default=str(CONFIG_PATH.relative_to(ROOT)),
        help="Repo-relative path to mirror local register config JSON",
    )
    args = parser.parse_args()

    if not SST_DIR.exists():
        raise SystemExit(".sst directory not found")

    config_path = ROOT / args.config
    config = load_config(config_path)
    default_scope, default_identity, lifecycle_id = read_defaults()
    registry = load_registry()
    artifacts = collect_artifact_paths(config)
    records = [parse_artifact(path, default_scope, default_identity, lifecycle_id) for path in artifacts]
    created = upsert_entries(registry, records)

    if args.dry_run:
        print("dry_run: true")
        print(f"config: {args.config}")
        print(f"artifact_count: {len(artifacts)}")
        print(f"new_decision_count: {len(created)}")
        if created:
            print("new_decision_ids:")
            for decision_id in created:
                print(decision_id)
        else:
            print("new_decision_ids: none")
        return 0

    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if created:
        print("new_decision_ids:")
        for decision_id in created:
            print(decision_id)
    else:
        print("new_decision_ids: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
