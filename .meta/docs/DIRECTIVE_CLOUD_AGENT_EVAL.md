# Directive: Cloud agent eval (magniphyq access and bulk data)

**Give this to the agent when it is spun up in a cloud environment.** The agent must verify it can reach magniphyq, see the local condenstate clone there, and see the full bulk data directory (~4GB of sims). Then output **only** the block below. Do not echo secrets in the block.

---

## Expected on magniphyq

- **Condenstate repo:** `~/condenstate` (clone of condenstate with `.sst`, `.ddb`, scripts, etc.).
- **Bulk data:** `~/results/` with subdirs `sim_XXX_EYYY_TZZZ_AaBb/` for all collected sims; total size approximately 4GB. This is too large for the git repo; cloud agents must access it on magniphyq.

---

## Steps

**1. Resolve magniphyq and key**

- `MAGNIPHYQ_IP` from your environment (Cursor cloud env/secrets). If unset: `aws ec2 describe-instances --region us-east-1 --filters "Name=tag:Name,Values=magniphyq" --query 'Reservations[*].Instances[*].PublicIpAddress' --output text`.
- `SSH_KEY_PATH` from your environment, or default `~/.ssh/pax-ec2-key.pem`. SSH user: `ubuntu`.

**2. Test SSH**

```bash
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@$MAGNIPHYQ_IP "echo ok"
```

If this fails, set `magniphyq_reachable: no` in the block and skip steps 3–4.

**3. Verify condenstate on magniphyq**

```bash
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no ubuntu@$MAGNIPHYQ_IP "test -d ~/condenstate/.sst && test -d ~/condenstate/.ddb && echo yes || echo no"
```

**4. Verify full data dir (~4GB)**

```bash
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no ubuntu@$MAGNIPHYQ_IP "du -sh ~/results 2>/dev/null || echo missing"
```

Check that the reported size is approximately 4GB (e.g. at least 3G). Count sim dirs if useful: `ls -d ~/results/sim_* 2>/dev/null | wc -l`.

**5. Output only this block**

Do not put IP or key in the block.

```
--- condenstate_cloud_readiness ---
repo: condenstate
magniphyq_reachable: [yes|no]
condenstate_on_magniphyq: [yes|no]
data_dir_ok: [yes|no]
data_dir_size_gb: [e.g. 4.2 or empty]
sim_dir_count: [integer or empty]
ready: [yes|no]
gaps: [one-line summary or none]
at: [ISO UTC]
---
```

Use `ready: yes` only when `magniphyq_reachable`, `condenstate_on_magniphyq`, and `data_dir_ok` are all yes and data size is approximately 4GB. Otherwise `ready: no` and set `gaps` (e.g. "data dir missing or too small", "SSH failed", "condenstate not found on magniphyq").

---

## If data dir is missing or too small

The full sim set (~4GB) must exist under `~/results/` on magniphyq before cloud workflows can run. If the eval reports `data_dir_ok: no` or size much less than 4GB, sync the full data to magniphyq first (e.g. from the pipeline collection or wherever the authoritative copy lives), then re-run this eval.
