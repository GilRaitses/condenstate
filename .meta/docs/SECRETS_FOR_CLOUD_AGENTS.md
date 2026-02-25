# Secrets for cloud agents

**Do not put secret values in the repo.** The repo only documents *which* secrets and env vars are needed and *where* to configure them.

## Where cloud agents get secrets

- **Cursor cloud / remote environments:** Use Cursor’s settings for that environment (e.g. **Settings → Cursor Settings → “Cloud” or “Environments” or “Secrets”**, or the cloud agent setup wizard). Add the variable names below there; Cursor injects them into the cloud agent’s environment when it runs.
- **Known issue:** Some users report that variables set in Cursor’s cloud agent settings do not appear in the agent’s terminal (`printenv`). If that happens, check Cursor’s docs or support for “environment variables” / “secrets” for cloud agents, and verify in the agent terminal that the vars you need are present before relying on them.

So: **you “register” what’s needed in the repo (this doc); you set the actual values in Cursor’s cloud/environment/secrets UI**, not in the repo.

## Variables the condenstate cloud agent needs

Set these in Cursor’s environment/secrets for the **condenstate** cloud project (or the cloud agent that will run in a VM and SSH to magniphyq / use PHY600 data):

| Variable | Purpose | Example (do not commit) |
|----------|---------|-------------------------|
| `PHY600_ROOT` | Path to PHY600 repo on the **cloud** machine (if the cloud agent has a clone there) or a shared path. Used for pipeline, registry, data. | `/home/ubuntu/PHY600` or leave unset if all data is on magniphyq |
| `MAGNIPHYQ_IP` | Magniphyq instance IP for SSH and dashboard. | Resolve via AWS CLI if unset |
| `SSH_KEY_PATH` | Path to the SSH private key **on the cloud VM** (e.g. key copied or mounted there). Same key as laptop for EC2. | `/home/ubuntu/.ssh/pax-ec2-key.pem` |

**SSH key in the cloud:** The key itself must exist on the cloud VM. Options:

1. **Cursor “secrets” or “files”:** If Cursor lets you attach a secret file to a cloud environment, upload the key and set `SSH_KEY_PATH` to the path where Cursor mounts it.
2. **Manual one-time setup:** Once the cloud VM exists, copy the key there (e.g. from your laptop via `scp` or a one-time paste into a file) and set permissions `chmod 600`. Then set `SSH_KEY_PATH` in Cursor’s env to that path.
3. **Vault:** Store the key in a vault (e.g. AWS Secrets Manager, 1Password); have a small bootstrap script the agent runs once that fetches it and writes to `SSH_KEY_PATH`. The agent needs one credential (e.g. AWS role, vault token) that *is* injected by Cursor.

## Repo’s role (“registration”)

- **.env.example** – Lists variable names and safe example values. Copy to `.env` locally; never commit `.env`.
- **This doc** – Lists what the cloud agent needs and where to configure it (Cursor cloud env / secrets).
- **.cursor/rules/condenstate-orchestration.mdc** – Tells the agent to use these env vars and where to read more.

So “secrets registered in the repo” means: **the repo documents the names and purpose of the secrets; you set the values in Cursor’s cloud agent / environment settings (and, for the key file, ensure it exists on the cloud VM via Cursor’s file injection, manual setup, or a vault).**

## Quick check in the cloud agent

After starting a cloud agent, run:

```bash
echo "PHY600_ROOT=$PHY600_ROOT" "MAGNIPHYQ_IP set=$([ -n "$MAGNIPHYQ_IP" ] && echo yes || echo no)" "SSH_KEY_PATH=$SSH_KEY_PATH"
test -f "$SSH_KEY_PATH" && echo "SSH key file exists" || echo "SSH key file missing"
```

If vars are empty or the key is missing, fix them in Cursor’s environment/secrets or via the key setup options above.

---

## Cloud agent SSH failed (magniphyq_reachable: no)

When the cloud agent reports `magniphyq_reachable: no` or `gaps: SSH failed`, work through this checklist. The cloud VM must have the same SSH access to magniphyq as your laptop.

### 1. Cursor cloud environment

- In Cursor, open settings for the **cloud** environment / project where the condenstate cloud agent runs.
- Set **environment variables** (or “Secrets”):
  - `MAGNIPHYQ_IP` = magniphyq’s current public IP (from AWS CLI or your laptop’s `.env`).
  - `SSH_KEY_PATH` = path **on the cloud VM** where the private key file will live (e.g. `/home/ubuntu/.ssh/pax-ec2-key.pem`).
- Save. Some Cursor setups require a restart of the cloud session for env vars to appear; if the agent still doesn’t see them, check Cursor docs.

### 2. SSH key on the cloud VM

The key file must exist **on the cloud VM** at the path you set as `SSH_KEY_PATH`. The cloud agent cannot use a key that only exists on your laptop.

- **Option A – Cursor file/secret:** If Cursor allows attaching a file (e.g. “Secret files”) to the cloud environment, upload the same key you use on the laptop and set `SSH_KEY_PATH` to the path where Cursor mounts it.
- **Option B – One-time copy:** From your laptop, copy the key to the cloud VM once (e.g. `scp -i <cloud-vm-key> ~/.ssh/pax-ec2-key.pem ubuntu@<cloud-vm-ip>:~/.ssh/pax-ec2-key.pem`), then SSH to the cloud VM and run `chmod 600 ~/.ssh/pax-ec2-key.pem`. Set `SSH_KEY_PATH` in Cursor to that path.
- **Option C – Vault:** Store the key in a vault; add a small bootstrap step that the cloud agent (or you) runs once to fetch it and write it to `SSH_KEY_PATH` with mode 600.

### 3. Network: magniphyq security group

Magniphyq’s EC2 security group must allow **inbound SSH (22)** from the cloud agent’s outbound IP. If the cloud agent runs in Cursor’s infrastructure, that IP may be dynamic; for testing you can temporarily allow `0.0.0.0/0` on port 22, then restrict later if needed. In AWS: EC2 → Security Groups → magniphyq’s group → Inbound rules → SSH from the cloud agent’s IP or 0.0.0.0/0.

### 4. Pre-flight in the cloud agent terminal

Before running the cloud readiness directive, in the cloud agent’s terminal run:

```bash
echo "MAGNIPHYQ_IP=${MAGNIPHYQ_IP:-<unset>}"
echo "SSH_KEY_PATH=${SSH_KEY_PATH:-<unset>}"
test -f "${SSH_KEY_PATH}" && echo "SSH key file: exists" || echo "SSH key file: missing"
```

Fix any unset or missing item using steps 1–2, then re-run the cloud agent eval directive.
