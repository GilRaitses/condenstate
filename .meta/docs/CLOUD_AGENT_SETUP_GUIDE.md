# Guide: Set up the Cursor cloud agent for condenstate

Use this when the cloud agent reports `magniphyq_reachable: no` or `gaps: SSH failed; missing env vars and key file`. You do these steps once; the agent cannot do them for you.

**Using the dev container:** This repo has a **`.devcontainer`** so Cursor (or VS Code) can “build an environment” that gets these vars from the host. Set `MAGNIPHYQ_IP`, `SSH_KEY_PATH`, and `PHY600_ROOT` in Cursor’s environment/secrets for the project; when the dev container is built, they’re passed in. See **`.devcontainer/README.md`**.

---

## 1. Set environment variables in Cursor

- Open **Cursor** and the **cloud** project/environment where the condenstate cloud agent runs.
- Go to **Settings** (or **Cursor Settings**) and find **Environment variables**, **Secrets**, or **Cloud environment** for that project.
- Add:
  - **`MAGNIPHYQ_IP`** = magniphyq’s current public IP (same value as in your laptop’s condenstate `.env`, or from AWS: `aws ec2 describe-instances --region us-east-1 --filters "Name=tag:Name,Values=magniphyq" --query 'Reservations[*].Instances[*].PublicIpAddress' --output text`).
  - **`SSH_KEY_PATH`** = path **on the cloud VM** where the SSH key file will live (e.g. `/home/ubuntu/.ssh/pax-ec2-key.pem`).
- Save. If your Cursor version needs it, restart or respawn the cloud environment so the agent sees the new vars.

---

## 2. Put the SSH key on the cloud VM and set permissions

The key file must exist **on the cloud VM** at the path you set as `SSH_KEY_PATH`. The cloud agent runs on that VM; it cannot use a key that only exists on your laptop. After placing the key, run `chmod 600 "$SSH_KEY_PATH"` on the cloud VM (or `chmod 600 ~/.ssh/pax-ec2-key.pem` if using that path).

**Option A – Cursor “Secret files” or “Attach file”**  
If Cursor has an option to attach a secret file to the cloud environment, upload your `pax-ec2-key.pem`. Note the path Cursor gives it (e.g. `/workspace/.secrets/pax-ec2-key.pem`) and set `SSH_KEY_PATH` in step 1 to that path.

**Option B – Copy from your laptop once**  
You need the cloud VM’s hostname or IP (Cursor may show it when you open the cloud environment or terminal). From your **laptop**:

```bash
# Create .ssh on cloud VM if needed, then copy the key
scp -i <key-you-use-to-access-cloud-vm> ~/.ssh/pax-ec2-key.pem ubuntu@<cloud-vm-ip>:~/.ssh/pax-ec2-key.pem
```

Then SSH into the cloud VM and run: `chmod 600 ~/.ssh/pax-ec2-key.pem`. Use `SSH_KEY_PATH=/home/ubuntu/.ssh/pax-ec2-key.pem` (or the actual path) in Cursor.

**Option C – Vault**  
Store the key in a vault (e.g. AWS Secrets Manager); add a one-time bootstrap that fetches it and writes it to `SSH_KEY_PATH` with `chmod 600`. See `.meta/docs/SECRETS_FOR_CLOUD_AGENTS.md` for the pattern.

---

## 3. (Optional) Magniphyq security group

If the cloud VM is outside your AWS account, magniphyq’s security group must allow **inbound SSH (22)** from the cloud VM’s IP. In AWS: EC2 → Security Groups → magniphyq’s group → Edit inbound rules → add SSH from the cloud agent’s IP, or `0.0.0.0/0` for testing.

---

## 4. Verify in the cloud agent terminal

In the **cloud** agent’s terminal (same environment that runs the readiness check), run:

```bash
echo "MAGNIPHYQ_IP=${MAGNIPHYQ_IP:-<unset>}"
echo "SSH_KEY_PATH=${SSH_KEY_PATH:-<unset>}"
test -f "${SSH_KEY_PATH}" && echo "key: exists" || echo "key: missing"
```

- If either variable is `<unset>`, fix step 1 and/or restart the cloud session.
- If the key file is **missing**, fix step 2 (ensure the key exists at `SSH_KEY_PATH` on the cloud VM and run `chmod 600` on it).

---

## 5. Re-run the cloud readiness check

Once the env vars and key file are in place, tell the cloud agent and it will re-run the readiness check. Paste the **cloud agent** directive from `.meta/docs/PASTE_DIRECTIVES.md` into the cloud agent again if needed. You should get `magniphyq_reachable: yes` and `ready: yes` once env and key are correct.

---

## Where else to look

- **Full checklist and troubleshooting:** `.meta/docs/SECRETS_FOR_CLOUD_AGENTS.md` (section “Cloud agent SSH failed”).
- **What to paste into each agent:** `.meta/docs/PASTE_DIRECTIVES.md`.
