# Env and orchestration (condenstate on the laptop)

When the **same local agent** works in both PHY600 and condenstate and can SSH to AWS, condenstate should use the **same env shape** as PHY600 so the agent knows where to find keys, magniphyq, and the other repo.

## What stays the same (no secrets in repo)

- **SSH key**: Same path as PHY600: `~/.ssh/pax-ec2-key.pem`. Not stored in condenstate; agent uses system/env.
- **Magniphyq IP**: Not committed. Resolve at runtime:
  - Prefer env: `MAGNIPHYQ_IP` (set from `.env` if you use it).
  - Else: `aws ec2 describe-instances --region us-east-1 --filters "Name=tag:Name,Values=magniphyq" --query 'Reservations[*].Instances[*].PublicIpAddress' --output text`
- **PHY600 path**: Where the live pipeline and data live. Prefer env `PHY600_ROOT` (e.g. `~/PHY600`). Agent in condenstate may need to read registry, config, or run scripts there when driving cloud workflows.

## .env.example

Repo root has `.env.example` with optional vars:

- `MAGNIPHYQ_IP` – dashboard IP (optional; can use AWS CLI instead).
- `PHY600_ROOT` – path to PHY600 repo.
- `SSH_KEY_PATH` – SSH key for EC2 (default `~/.ssh/pax-ec2-key.pem`).

Copy to `.env`, set values, and **do not commit `.env`**. Add `.env` to `.gitignore` if it is not already. The agent (or scripts) can load these when running in condenstate so behavior matches PHY600.

## Roles

- **condenstate**: Canon (.sst, .ddb), paper1/paper2 specs, and (after import) scripts/manuscript. No live IPs or keys. Eval clears gates/contracts here.
- **PHY600**: Live pipeline (rerun_v2/pipeline), sim_registry, results, EC2/magniphyq config. Agent may SSH from here or from condenstate using the same key and resolved magniphyq.
- **Local agent**: Can cd into either repo, run eval in condenstate, run pipeline scripts in PHY600, and SSH to magniphyq/EC2 using the env above.

## Getting magniphyq IP in a script

```bash
# Prefer env
if [ -n "$MAGNIPHYQ_IP" ]; then
  echo "$MAGNIPHYQ_IP"
else
  aws ec2 describe-instances --region us-east-1 \
    --filters "Name=tag:Name,Values=magniphyq" \
    --query 'Reservations[*].Instances[*].PublicIpAddress' --output text
fi
```
