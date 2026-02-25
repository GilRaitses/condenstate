# Copy-paste directives for local and cloud agents

Use the exact text below in each agent. No edits needed except to choose the right block.

**If the cloud agent reports SSH failed or missing env/key:** see **`.meta/docs/CLOUD_AGENT_SETUP_GUIDE.md`** for the step-by-step setup (Cursor env vars, SSH key on cloud VM, pre-flight check).

**To have Cursor build an environment that has these vars:** use the repo’s **dev container** (Reopen in Container / build from `.devcontainer`). Set the vars on the host (Cursor env for cloud, or `.env` for local); they’re passed into the container. See **`.devcontainer/README.md`**.

---

## Local agent: test the dev container

Paste this into the local condenstate agent to verify the dev container gets env vars and the SSH key:

```
Test the dev container for this repo. From repo root:

1. If the devcontainer CLI is available (e.g. `devcontainer` or `npx @devcontainers/cli`), run a build and then run one command inside the container that: (a) echoes MAGNIPHYQ_IP, SSH_KEY_PATH, PHY600_ROOT (values redacted as "set" or "unset"), (b) runs `test -f $SSH_KEY_PATH && echo key_exists || echo key_missing`. Report the output and whether the test passed (vars set and key exists).

2. If the devcontainer CLI is not available, report: "Dev container CLI not found. To test manually: in Cursor use 'Reopen in Container' (or Dev Containers: Reopen in Container), then in the container terminal run: echo MAGNIPHYQ_IP=\${MAGNIPHYQ_IP:-unset} SSH_KEY_PATH=\${SSH_KEY_PATH:-unset}; test -f \"\$SSH_KEY_PATH\" && echo key_exists || echo key_missing."

Do not output secret values (no IP, no key contents).
```

---

## Local agent (condenstate repo on your laptop)

Paste this into the condenstate agent:

```
Follow .meta/docs/DIRECTIVE_LOCAL_VERIFY_MAGNIPHYQ_AND_DATA.md.

Do in order: (1) Run eval_gates.py --report --block. (2) Run the full local readiness check from DIRECTIVE_LOCAL_READINESS_CHECK.md. (3) SSH to magniphyq (MAGNIPHYQ_IP and SSH_KEY_PATH from .env or env) and verify ~/condenstate has .sst and .ddb, and ~/results has sim_* dirs and is about 4GB+. If you cannot SSH, set magniphyq_reachable: no and note in gaps that the cloud agent must verify. (4) If there are uncommitted changes, commit and push to origin main (do not commit .env). Optionally: ssh to magniphyq and run "cd ~/condenstate && git pull origin main". (5) Output only the --- condenstate_local_full_check --- block from that doc; do not put IP or key in the block.
```

---

## Cloud agent: test key access only

Paste this into a **new** cloud agent to verify it has the SSH key and can reach magniphyq (no other checks):

```
Test SSH access to magniphyq. (1) Echo whether MAGNIPHYQ_IP and SSH_KEY_PATH are set (say "set" or "unset", do not print values). (2) Run: test -f "$SSH_KEY_PATH" && echo key_file_exists || echo key_file_missing. (3) Run: ssh -o StrictHostKeyChecking=accept-new -i "$SSH_KEY_PATH" ubuntu@$MAGNIPHYQ_IP "echo ok". (4) Report: key access ok (if you see "ok" from SSH) or what failed (unset var, missing file, or SSH error). Do not output the IP, key path, or key contents.
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

---

## Cloud agent: try again (after fixing env/key)

Paste this into the cloud agent after you’ve set MAGNIPHYQ_IP and SSH_KEY_PATH in Cursor and ensured the key file exists on the VM:

```
Run the cloud readiness check again. Follow .meta/docs/DIRECTIVE_CLOUD_AGENT_EVAL.md: SSH to magniphyq, verify ~/condenstate and ~/results, then output only the --- condenstate_cloud_readiness --- block. Do not put IP or key in the block.
```
