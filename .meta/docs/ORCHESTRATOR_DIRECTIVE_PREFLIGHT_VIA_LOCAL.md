# Orchestrator directive: Preflight via local condenstate agent

**When to use:** You (the orchestrator) need to know whether magniphyq has everything in place so that **cloud agents** could take over (condenstate clone with .sst/.ddb, ~/results ~4GB, scripts/data). The **local** condenstate agent (on the human’s laptop) can SSH to magniphyq and run the preflight; cloud/Codex agents often cannot reach magniphyq.

**Orchestration etiquette:** Follow the condenstate workflow in `.meta/docs/ORCHESTRATOR_RECAP.md`. Use the paste blocks from `.meta/docs/PASTE_DIRECTIVES.md`; do not invent your own. The local agent runs on the human’s machine in the condenstate repo.

---

## What to do

1. **Ask the human** to open the condenstate repo on their **laptop** in Cursor (or the agent environment they use for condenstate locally).

2. **Give the human this directive** to paste into that **local condenstate agent** (exact text from PASTE_DIRECTIVES.md):

```
Follow .meta/docs/DIRECTIVE_LOCAL_VERIFY_MAGNIPHYQ_AND_DATA.md.

Do in order: (1) Run eval_gates.py --report --block. (2) Run the full local readiness check from DIRECTIVE_LOCAL_READINESS_CHECK.md. (3) SSH to magniphyq (MAGNIPHYQ_IP and SSH_KEY_PATH from .env or env) and verify ~/condenstate has .sst and .ddb, and ~/results has sim_* dirs and is about 4GB+. If you cannot SSH, set magniphyq_reachable: no and note in gaps that the cloud agent must verify. (4) If there are uncommitted changes, commit and push to origin main (do not commit .env). Optionally: ssh to magniphyq and run "cd ~/condenstate && git pull origin main". (5) Output only the --- condenstate_local_full_check --- block from that doc; do not put IP or key in the block.
```

3. **Have the human paste back** the agent’s output (the `--- condenstate_local_full_check ---` block).

4. **Interpret the block:**
   - `magniphyq_reachable: yes`, `condenstate_on_magniphyq: yes`, `data_dir_ok: yes`, and `data_dir_size_gb` around 4 → magniphyq is ready for cloud agents to use (when they can reach it). You can delegate work that assumes condenstate and data on magniphyq.
   - `magniphyq_reachable: no` or `data_dir_ok: no` → note the gaps; cloud agents cannot rely on magniphyq until the human fixes SSH or data. Use the local agent for magniphyq-dependent work.
   - `eval: fail` or missing scripts/data → resolve those before assuming cloud or local agents can run full pipelines.

5. **Next steps:** If preflight passes, you can later spin up a **cloud** agent and use the “Cloud agent (when spun up in Cursor cloud)” paste block to verify cloud readiness (or use Codex and `.meta/docs/CODEX_SSH_CHECKLIST.md` if Codex blocks SSH). If preflight fails, direct the human to fix env/SSH/data and re-run the local directive.

---

## One-line summary for the orchestrator

**Ask the human to run the “Local agent (condenstate repo on your laptop)” directive from PASTE_DIRECTIVES.md in their local condenstate agent, then paste back the `--- condenstate_local_full_check ---` block so you can see if magniphyq is ready for cloud handoff.**
