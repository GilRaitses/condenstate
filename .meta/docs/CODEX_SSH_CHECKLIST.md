# Codex: SSH to magniphyq checklist

**For the Codex agent:** Use this to decide if SSH is possible and what to report. **For the user:** Use this to fix a new environment when the agent says "key file missing" or "Network is unreachable."

---

## 1. What the agent should run (status only)

**If MAGNIPHYQ_IP has trailing (or leading) whitespace,** the user must edit the env in Codex and trim it to the IP only (e.g. `3.81.174.42`). Otherwise `nc`/`ssh` will fail.

Run this (uses trimmed IP) and interpret the result:

```bash
ip_trimmed="$(printf '%s' "${MAGNIPHYQ_IP:-}" | xargs)"
echo "MAGNIPHYQ_IP=$([ -n "$ip_trimmed" ] && echo set || echo unset)"
echo "SSH_KEY_PATH=$([ -n "$SSH_KEY_PATH" ] && echo set || echo unset)"
test -f "${SSH_KEY_PATH:-/none}" && echo "key_file=exists" || echo "key_file=missing"
timeout 10 ssh -o BatchMode=yes -o ConnectTimeout=5 -i "${SSH_KEY_PATH:-/dev/null}" "ubuntu@${ip_trimmed:-invalid}" "echo ok" 2>&1 | tail -1
```

**Interpretation:**

| key_file | SSH result | Report |
|----------|------------|--------|
| missing | (any) | **Key file missing.** A human must create it once in this environment (see "Human: create key file" below). Then re-run this check. |
| exists | ok | **SSH OK.** Magniphyq reachable. Proceed with cloud readiness (e.g. `.meta/docs/DIRECTIVE_CLOUD_AGENT_EVAL.md`). |
| exists | Identity file ... not accessible | Key path wrong or permissions. Human: ensure `SSH_KEY_PATH` is correct and run `chmod 600 "$SSH_KEY_PATH"`. |
| exists | Network is unreachable / Connection timed out | **Key OK; network blocks SSH.** Codex does not allow outbound SSH to magniphyq. Do not retry from this environment. Use the laptop (Cursor) for any work that needs SSH to magniphyq. |

---

## 2. Human: create key file (once per new environment)

Codex does **not** create the key file from the `PAX_EC2_KEY_PEM` secret in the shell. So in every **new** Codex environment the key file must be created by a human once.

1. In the Codex terminal, run:
   ```bash
   mkdir -p /workspace/condenstate/.secrets
   cat > /workspace/condenstate/.secrets/pax-ec2-key.pem
   ```
2. **Paste** the full PEM key (including `-----BEGIN ... PRIVATE KEY-----` and `-----END ... PRIVATE KEY-----`), press Enter, then **Ctrl+D** once.
3. Run:
   ```bash
   chmod 600 /workspace/condenstate/.secrets/pax-ec2-key.pem
   ```
4. In Codex environment settings, set **SSH_KEY_PATH** = `/workspace/condenstate/.secrets/pax-ec2-key.pem` (if not already).
5. Re-run the status check in section 1. If you still get "Network is unreachable", see section 3.

**Security:** Pasting the key exposes it. Rotate the key when convenient (`.meta/docs/KEY_ROTATION.md`).

---

## 3. "Network is unreachable" from Codex

If the key file exists and has correct permissions but SSH fails with **Network is unreachable** or **Connection timed out**, Codex’s network is blocking outbound SSH to your EC2 IP. You cannot fix this from the repo or AWS.

- **Do not** keep retrying SSH from Codex.
- **Do** run any magniphyq-dependent work (SSH, data on magniphyq) from somewhere that can reach it (e.g. your laptop with Cursor and the same key).
- Codex can still be used for work that does **not** require SSH (eval, docs, code that doesn’t touch magniphyq).

---

## 4. One-line summary for the agent

**If key_file=missing:** Tell the user: "SSH key file is missing in this environment. See `.meta/docs/CODEX_SSH_CHECKLIST.md` section 2 (Human: create key file). I cannot create it because the secret is not available in this shell."

**If key_file=exists and SSH returns ok:** Proceed with cloud readiness.

**If key_file=exists and SSH returns Network unreachable (or timeout):** Tell the user: "Key is present but Codex cannot reach magniphyq (outbound SSH blocked). Use your laptop/Cursor for magniphyq access. See `.meta/docs/CODEX_SSH_CHECKLIST.md` section 3."

**Do not** say "fix this in Cursor Cloud" — this environment is **Codex**, not Cursor. The checklist above is the fix; no other product is required.

---

## 5. Readiness check (pass/fail, what to fix)

The agent may run this and report only the outcome (no secret values). It trims `MAGNIPHYQ_IP` and reports what’s wrong.

```bash
set -e
ip_trimmed="$(printf '%s' "${MAGNIPHYQ_IP:-}" | xargs)"
fixes=""
[ -z "$ip_trimmed" ] && fixes="${fixes} MAGNIPHYQ_IP unset or empty"
[ "$ip_trimmed" != "${MAGNIPHYQ_IP:-}" ] && fixes="${fixes} MAGNIPHYQ_IP had whitespace (use trimmed value in env)"
[ -z "${SSH_KEY_PATH:-}" ] && fixes="${fixes} SSH_KEY_PATH unset"
[ -n "${SSH_KEY_PATH:-}" ] && [ ! -f "$SSH_KEY_PATH" ] && fixes="${fixes} key file missing at SSH_KEY_PATH"
if [ -n "$ip_trimmed" ] && [ -f "${SSH_KEY_PATH:-/none}" ]; then
  if ! timeout 8 ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new -i "$SSH_KEY_PATH" "ubuntu@$ip_trimmed" "echo ok" 2>/dev/null; then
    fixes="${fixes} network unreachable or SSH failed from this environment"
  fi
fi
[ -z "$fixes" ] && echo "READINESS=pass" || echo "READINESS=fail FIXES:$fixes"
```

---

## 6. Run in your terminal (laptop) before Codex

Run this **on your laptop** (in the condenstate repo or any directory) to see if your env and SSH to magniphyq are good before you open Codex. Uses `.env` if you’re in the repo.

```bash
cd /path/to/condenstate   # or skip if you set vars another way
[ -f .env ] && set -a && source .env && set +a
export MAGNIPHYQ_IP="${MAGNIPHYQ_IP:-}"
export SSH_KEY_PATH="${SSH_KEY_PATH:-$HOME/.ssh/pax-ec2-key.pem}"

ip_trimmed="$(printf '%s' "${MAGNIPHYQ_IP:-}" | xargs)"
fixes=""
[ -z "$ip_trimmed" ] && fixes="${fixes} MAGNIPHYQ_IP unset or empty"
[ "$ip_trimmed" != "${MAGNIPHYQ_IP:-}" ] && fixes="${fixes} MAGNIPHYQ_IP had whitespace"
[ -z "${SSH_KEY_PATH:-}" ] && fixes="${fixes} SSH_KEY_PATH unset"
[ -n "${SSH_KEY_PATH:-}" ] && [ ! -f "$SSH_KEY_PATH" ] && fixes="${fixes} key file missing"
if [ -n "$ip_trimmed" ] && [ -f "${SSH_KEY_PATH:-/none}" ]; then
  if ! timeout 8 ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new -i "$SSH_KEY_PATH" "ubuntu@$ip_trimmed" "echo ok" 2>/dev/null; then
    fixes="${fixes} network unreachable or SSH failed"
  fi
fi
[ -z "$fixes" ] && echo "READINESS=pass" || echo "READINESS=fail FIXES:$fixes"
```

One-liner (from condenstate repo root, with `.env`):

```bash
cd /Users/gilraitses/condenstate && [ -f .env ] && set -a && source .env && set +a; export SSH_KEY_PATH="${SSH_KEY_PATH:-$HOME/.ssh/pax-ec2-key.pem}"; ip_trimmed="$(printf '%s' "${MAGNIPHYQ_IP:-}" | xargs)"; fixes=""; [ -z "$ip_trimmed" ] && fixes="${fixes} MAGNIPHYQ_IP unset"; [ -n "${SSH_KEY_PATH:-}" ] && [ ! -f "$SSH_KEY_PATH" ] && fixes="${fixes} key missing"; [ -n "$ip_trimmed" ] && [ -f "${SSH_KEY_PATH:-/none}" ] && ! timeout 8 ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new -i "$SSH_KEY_PATH" "ubuntu@$ip_trimmed" "echo ok" 2>/dev/null && fixes="${fixes} SSH failed"; [ -z "$fixes" ] && echo "READINESS=pass" || echo "READINESS=fail FIXES:$fixes"
```
