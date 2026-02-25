# Directive: Local condenstate agent – verify all checks and magniphyq/data

**Give this to the agent in the condenstate repo (local/laptop).** The agent must run the checks below and then output **only** the confirmation block at the end. Do not echo secrets (no IPs, no key contents in the block).

---

## Steps

**1. Run gates/contracts eval**

From repo root:

```bash
python3 .sst/tools/eval_gates.py --report --block
```

Note: `eval` (pass/fail), `eval_report` path, exit code.

**2. Run full local readiness**

Follow `.meta/docs/DIRECTIVE_LOCAL_READINESS_CHECK.md`: check data/scripts in repo, env file, SSH key, Cursor rules. Note script/data/env status.

**3. Verify magniphyq: condenstate clone and full data dir**

- Resolve magniphyq IP: from `MAGNIPHYQ_IP` in `.env` or from `aws ec2 describe-instances --region us-east-1 --filters "Name=tag:Name,Values=magniphyq" --query 'Reservations[*].Instances[*].PublicIpAddress' --output text`.
- SSH key: `SSH_KEY_PATH` from `.env` or default `~/.ssh/pax-ec2-key.pem`. User: `ubuntu`.
- Over SSH to magniphyq, verify:
  - **Condenstate repo:** `~/condenstate` exists and contains `.sst` and `.ddb` (e.g. `ls ~/condenstate/.sst ~/condenstate/.ddb`).
  - **Full data dir:** `~/results` exists and contains sim directories (e.g. `sim_*`). Check total size is approximately 4GB (e.g. `du -sh ~/results`); report size in the block. If `~/results` is missing or much smaller than ~4GB, report `data_dir_ok: no` and `data_dir_note: "full sim data not present; sync required"`.
- If you cannot SSH (no key, no IP, or connection failed), set in the block: `magniphyq_reachable: no`, `condenstate_on_magniphyq: not_checked`, `data_dir_ok: not_checked`, and in `gaps` add "magniphyq not reachable; cloud agent must verify".

**4. Output only this block**

Fill in; do not put secrets (no IP, no key) in the block.

```
--- condenstate_local_full_check ---
repo: condenstate
eval: [pass|fail]
eval_report: [path or empty]
scripts_pipeline: [present|missing]
scripts_modeling: [present|missing]
paper1_manuscript: [present|missing]
simulation: [present|missing]
data: [present_in_repo|in_phy600|missing]
env_file: [present|missing]
ssh_key: [exists|missing]
magniphyq_reachable: [yes|no]
condenstate_on_magniphyq: [yes|no|not_checked]
data_dir_ok: [yes|no|not_checked]
data_dir_size_gb: [e.g. 4.2 or empty]
data_dir_note: [one line or empty]
ready: [yes|no]
gaps: [one-line summary of what is missing or none]
at: [ISO UTC]
---
```

Use `ready: yes` only when eval is pass, env and key are in place, magniphyq is reachable, condenstate exists on magniphyq, and data dir is present and ~4GB. Otherwise `ready: no` and set `gaps` accordingly.

---

## Ensuring full data dir on magniphyq (~4GB)

If `~/results` on magniphyq is missing or small, the full sim set must be synced there before cloud agents can use it. Data lives in `~/results/` on magniphyq as `sim_XXX_EYYY_TZZZ_AaBb/` directories (collected from EC2 fleet). Sync from wherever the authoritative copy lives (e.g. from PHY600 pipeline collection) so that magniphyq has the full ~4GB. This directive does not perform the sync; it only verifies and reports.
