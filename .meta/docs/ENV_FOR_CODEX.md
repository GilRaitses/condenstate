# Environment variables for OpenAI Codex (condenstate)

When using **OpenAI Codex** with the condenstate repo (e.g. cloud agents that SSH to magniphyq or use PHY600 paths), set these in Codex’s project or agent environment (however Codex exposes env vars / secrets for the workspace).

**If the Codex agent reports "key file missing" or "Network is unreachable":** use **`.meta/docs/CODEX_SSH_CHECKLIST.md`** for the exact status check, human steps to create the key, and when to give up on SSH from Codex.

## Variables

| Variable | Required | Purpose | Example |
|----------|----------|---------|---------|
| **MAGNIPHYQ_IP** | For SSH workflows | Magniphyq EC2 public IP | `3.81.174.42` (or resolve via AWS CLI) |
| **SSH_KEY_PATH** | For SSH workflows | Path to EC2 private key (PEM) **on the machine where Codex runs** | `~/.ssh/pax-ec2-key.pem` or `/path/on/codex/vm/pax-ec2-key.pem` |
| **PHY600_ROOT** | Optional | Path to PHY600 repo on that machine | `~/PHY600` or leave unset |

## Secrets (SSH key)

If Codex injects **Secrets** as environment variables, the **secret name must be a valid shell identifier**: no hyphens, no dots. Otherwise you get `export: 'pax-ec2-key.pem=...': not a valid identifier`.

- **Use a secret name like `PAX_EC2_KEY_PEM`** (not `pax-ec2-key.pem`). The value is the raw PEM file content.
- Set **Environment variable** `SSH_KEY_PATH` to the path where the key file will live, e.g. `/workspace/.secrets/pax-ec2-key.pem`.
- Codex may write that secret to a file automatically; if not, add a setup step that runs once: write `$PAX_EC2_KEY_PEM` to `$SSH_KEY_PATH` and run `chmod 600 "$SSH_KEY_PATH"`. (The agent must not echo the variable.)

## Notes

- The **key file** must exist on the machine where the Codex agent runs. If Codex runs in a cloud VM, use the secret-as-env-var pattern above (valid name like `PAX_EC2_KEY_PEM`) and a path in `SSH_KEY_PATH`. Do not paste the key in chat; see `.meta/docs/KEY_ROTATION.md` if the key was exposed.
- For **local** use (Codex on your laptop), copy `.env.example` to `.env` in the repo root and set the same three names there; do not commit `.env`.
- Eval and modeling (`make eval`, pipeline) do not require these vars; only SSH to magniphyq and PHY600 path resolution do.

## Quick check (in Codex agent terminal)

```bash
echo "MAGNIPHYQ_IP set=$([ -n "$MAGNIPHYQ_IP" ] && echo yes || echo no)" "SSH_KEY_PATH set=$([ -n "$SSH_KEY_PATH" ] && echo yes || echo no)"
test -f "$SSH_KEY_PATH" && echo key_file_exists || echo key_file_missing
ssh -o StrictHostKeyChecking=accept-new -i "$SSH_KEY_PATH" ubuntu@$MAGNIPHYQ_IP "echo ok"
```

Expect: vars set, key_file_exists, and `ok` from SSH. Do not print the IP or key path in shared output.
