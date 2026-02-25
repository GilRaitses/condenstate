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
  - **`PHY600_ROOT`** (optional) = path to PHY600 on the VM if used.
- Save. If your Cursor version needs it, restart or respawn the cloud environment so the agent sees the new vars.

**Note:** `.vscode/settings.json` in this repo passes these vars into the integrated terminal (macOS and Linux), so once Cursor has them set, terminals in this workspace will see `MAGNIPHYQ_IP`, `SSH_KEY_PATH`, and `PHY600_ROOT`.

---

## 2. Put the SSH key on the cloud VM and set permissions

The key file must exist **on the cloud VM** at the path you set as `SSH_KEY_PATH`. The cloud agent runs on that VM; it cannot use a key that only exists on your laptop. After placing the key, run `chmod 600 "$SSH_KEY_PATH"` on the cloud VM (or `chmod 600 ~/.ssh/pax-ec2-key.pem` if using that path).

**Is there a way the project can “have” the key so every cloud agent gets it?**  
Only if Cursor supports it: in the **project’s** or **environment’s** settings, look for **“Secret files”**, **“Attach file”**, **“Environment files”**, or similar. If you can attach a file to the cloud environment, upload `pax-ec2-key.pem` once; Cursor will place it at a path (e.g. `/workspace/.secrets/...`). Set `SSH_KEY_PATH` to that path in step 1. Then every new cloud agent in that project will see the key. If your Cursor version has no such option, you have to put the key on the VM once using one of the options below.

**Option A – Cursor “Secret files” or “Attach file”**  
If Cursor has an option to attach a secret file to the cloud environment, upload your `pax-ec2-key.pem`. Note the path Cursor gives it (e.g. `/workspace/.secrets/pax-ec2-key.pem`) and set `SSH_KEY_PATH` in step 1 to that path.

**Option B – Copy from your laptop once**  
You need the cloud VM’s hostname or IP (Cursor may show it when you open the cloud environment or terminal). From your **laptop**:

```bash
# Create .ssh on cloud VM if needed, then copy the key
scp -i <key-you-use-to-access-cloud-vm> ~/.ssh/pax-ec2-key.pem ubuntu@<cloud-vm-ip>:~/.ssh/pax-ec2-key.pem
```

Then SSH into the cloud VM and run: `chmod 600 ~/.ssh/pax-ec2-key.pem`. Use `SSH_KEY_PATH=/home/ubuntu/.ssh/pax-ec2-key.pem` (or the actual path) in Cursor.

**Option C – One-time paste in the current cloud agent**  
If you have no other way to get the key onto the VM: in the **same** cloud agent chat, paste the key contents (the full `-----BEGIN ... END ...` block) and say: “Write this to a file at `~/.ssh/pax-ec2-key.pem` on this machine and run `chmod 600 ~/.ssh/pax-ec2-key.pem`. Do not echo the key back.” The agent can create the file; then set `SSH_KEY_PATH` in Cursor to that path (or leave it if you use that path). **Warning:** the key will appear in the chat; avoid if the conversation is logged or shared. Prefer Option A or B when possible.

**Option D – Vault**  
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

## Do I need to launch a new cloud agent?

**No, not if you add the key in the current session.**  
- If you use **Option C (paste)** in this same cloud agent, the key is written to the VM this agent is on. Re-run the readiness directive in the **same** chat; no new agent needed.  
- If you use **Option B (scp from laptop)**, the key is on the same VM. Again, just re-run the directive in the same agent.  
- You only need to **start a new cloud agent** (or restart the cloud environment) if you changed **Cursor’s env vars** (step 1) and the current terminal still doesn’t show them—then a new session can pick up the new vars.

---

## Where else to look

- **Full checklist and troubleshooting:** `.meta/docs/SECRETS_FOR_CLOUD_AGENTS.md` (section “Cloud agent SSH failed”).
- **What to paste into each agent:** `.meta/docs/PASTE_DIRECTIVES.md`.
