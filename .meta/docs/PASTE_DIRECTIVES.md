# Copy-paste directives for local and cloud agents

Use the exact text below in each agent. No edits needed except to choose the right block.

---

## Local agent (condenstate repo on your laptop)

Paste this into the condenstate agent:

```
Follow .meta/docs/DIRECTIVE_LOCAL_VERIFY_MAGNIPHYQ_AND_DATA.md.

Do in order: (1) Run eval_gates.py --report --block. (2) Run the full local readiness check from DIRECTIVE_LOCAL_READINESS_CHECK.md. (3) SSH to magniphyq (MAGNIPHYQ_IP and SSH_KEY_PATH from .env or env) and verify ~/condenstate has .sst and .ddb, and ~/results has sim_* dirs and is about 4GB+. If you cannot SSH, set magniphyq_reachable: no and note in gaps that the cloud agent must verify. (4) If there are uncommitted changes, commit and push to origin main (do not commit .env). Optionally: ssh to magniphyq and run "cd ~/condenstate && git pull origin main". (5) Output only the --- condenstate_local_full_check --- block from that doc; do not put IP or key in the block.
```

---

## Cloud agent (when spun up in Cursor cloud)

Paste this into the cloud agent:

```
Follow .meta/docs/DIRECTIVE_CLOUD_AGENT_EVAL.md.

First run this pre-flight in your terminal and fix any unset or missing item (set MAGNIPHYQ_IP and SSH_KEY_PATH in Cursor cloud env; ensure the SSH key file exists on this VM at SSH_KEY_PATH):

echo "MAGNIPHYQ_IP=${MAGNIPHYQ_IP:-<unset>}"
echo "SSH_KEY_PATH=${SSH_KEY_PATH:-<unset>}"
test -f "${SSH_KEY_PATH}" && echo "SSH key file: exists" || echo "SSH key file: missing"

Then verify: (1) SSH to magniphyq (ubuntu@$MAGNIPHYQ_IP -i $SSH_KEY_PATH). (2) On magniphyq, ~/condenstate exists with .sst and .ddb. (3) On magniphyq, ~/results exists and is about 4GB+. Output only the --- condenstate_cloud_readiness --- block from that doc. Do not put IP or key in the block. If SSH fails, see .meta/docs/SECRETS_FOR_CLOUD_AGENTS.md section "Cloud agent SSH failed".
```
