<!--
LIFECYCLE_ID: mirror-local-20260211-0001
DECISION_KIND: credentials_policy
DECISION_SCOPE_JSON: {"od_pair":"project:condenstate","graph_id":"condenstate-canon-v1","run_id":"condenstate-manifest-0001","lifecycle_id":"mirror-local-20260211-0001"}
DECISION_IDENTITY_FIELDS_JSON: {"repo_commit":"39f57f49eeae6e87490a9cd4a1e0c20367036526","objective_hash":"1111111111111111111111111111111111111111111111111111111111111111","graph_hash":"2222222222222222222222222222222222222222222222222222222222222222","params_hash":"3333333333333333333333333333333333333333333333333333333333333333"}
-->

# Credentials policy (agent rehydration contract)

This artifact is part of the lifecycle contract. Every agent (local or cloud) must be aware of it on boot and on rehydration.

## Invariant

**Secrets and credential values are never stored in the repo.** The repo only declares which credentials and env vars are required and where they are configured.

## Required awareness

Agents must always know:

1. **Environment variables** (local: `.env` in repo root, copy from `.env.example`; cloud: set in Cursor's environment/secrets for the cloud agent):
   - `PHY600_ROOT` – Path to PHY600 repo (pipeline, registry, data). Required when the agent needs to read or drive PHY600 assets.
   - `MAGNIPHYQ_IP` – Magniphyq instance IP for SSH and dashboard. Optional if resolved via AWS CLI.
   - `SSH_KEY_PATH` – Path to SSH private key for EC2 (e.g. `~/.ssh/pax-ec2-key.pem`). On cloud VMs the key must exist at this path (injected or copied); never commit the key.

2. **Where values live**: Local: `.env` (not committed; in `.gitignore`). Cloud: Cursor's cloud agent / environment / secrets settings. See `.meta/docs/SECRETS_FOR_CLOUD_AGENTS.md`.

3. **Verification**: Before running SSH or pipeline steps that need PHY600 or magniphyq, the agent should confirm `SSH_KEY_PATH` (or default) exists and required vars are set; if not, report the gap and do not proceed with steps that require them.

## Read order

This policy is read as part of agent boot and rehydration immediately after `.sst/layout_policy.md` (see `.sst/next_agent_boot.md`). It is registered in `.ddb` and is a managed resource in the lifecycle contract.

## Reference

- Full instructions for cloud agents: `.meta/docs/SECRETS_FOR_CLOUD_AGENTS.md`
- Env and orchestration (local + cloud): `.meta/docs/ENV_AND_ORCHESTRATION.md`
- Template for local `.env`: `.env.example` (copy to `.env`, set values, do not commit)
