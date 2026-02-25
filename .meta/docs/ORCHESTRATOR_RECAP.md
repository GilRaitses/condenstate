# Orchestrator recap: condenstate + cloud agents (March preprint push)

**For:** ChatGPT (or other) orchestrator that coordinates Cursor cloud agents to polish papers and study artifacts for peer review and March preprint/journal submission.

**Repo:** condenstate (GitHub GilRaitses/condenstate) — public mirror for Paper 1 (synapsin phase diagram) and Paper 2 (bridge/ODE). Canon state in `.sst/`, decision registry in `.ddb/`, worker outputs in `.meta/runs/` and `.meta/figs/`.

**Goal:** Improve papers and front-end touchpoints for study artifacts; leave everything polished and ready for peer review and a seamless transition to preprint (e.g. bioRxiv) and journal shopping in **March** (target next month from 2/25).

---

## 1. What’s already set up

### Cloud agents (Cursor)

- **Env in Cursor** for the condenstate cloud project: `MAGNIPHYQ_IP`, `SSH_KEY_PATH`, optionally `PHY600_ROOT`. Set in Cursor Settings → Environment / Secrets for that project.
- **SSH key on the cloud VM:** The EC2 key exists at the path in `SSH_KEY_PATH` on the cloud VM (e.g. copied via scp or Cursor secret file). Key access has been tested and returns “key access ok”.
- **Magniphyq:** EC2 instance that holds `~/condenstate` (clone) and `~/results/` (~4GB sim data). Cloud agents SSH as `ubuntu@$MAGNIPHYQ_IP` with `-i $SSH_KEY_PATH`.

### Docs to point orchestrator/agents at

| Doc | Use |
|-----|-----|
| `.meta/docs/PASTE_DIRECTIVES.md` | Exact text to paste into local vs cloud agents (test key, full readiness, cloud eval). |
| `.meta/docs/CLOUD_AGENT_SETUP_GUIDE.md` | If a cloud agent reports SSH/env/key missing. |
| `.meta/docs/SECRETS_FOR_CLOUD_AGENTS.md` | What vars and key the cloud agent needs; where to set them (Cursor). |
| `.meta/docs/KEY_ROTATION.md` | Rotate SSH key if it was exposed (no pasting of new key in chat). |
| `.meta/docs/ORCHESTRATOR_HEADS_UP.md` | Eval, readiness checklist, env setup; one-line summary for starting work. |
| `.meta/docs/SYNAPSIN_ORCHESTRATION_PLAYBOOK.md` | Canon surfaces, write discipline, refusal gates, resume. |
| `.meta/docs/DIRECTIVE_CLOUD_AGENT_EVAL.md` | Full cloud readiness: SSH, condenstate on magniphyq, ~/results size; output block format. |
| `.meta/docs/DIRECTIVE_IMPORT_EXACT_PATHS.md` | Import paths from PHY600 into condenstate (paper1, paper2, pipeline, modeling). |

---

## 2. Orchestrator workflow (high level)

1. **Spin up a Cursor cloud agent** in the condenstate project.
2. **Verify key access** by pasting the “Cloud agent: test key access only” block from `PASTE_DIRECTIVES.md`. Expect: `key access ok`.
3. **Run full cloud readiness** when you need the agent to use magniphyq/data: paste the “Cloud agent (when spun up in Cursor cloud)” block from `PASTE_DIRECTIVES.md`. Agent follows `DIRECTIVE_CLOUD_AGENT_EVAL.md` and outputs the `--- condenstate_cloud_readiness ---` block.
4. **Assign work:** Have the cloud agent improve papers (Paper 1 / Paper 2), polish front-end touchpoints for study artifacts (figures, manuscript, supplementary, any dashboard or public-facing links referenced in the repo), and keep canon updated per `.sst/layout_policy.md` and `SYNAPSIN_ORCHESTRATION_PLAYBOOK.md`.
5. **Local agent (optional):** For condenstate on your laptop, use the “Local agent (condenstate repo on your laptop)” block in `PASTE_DIRECTIVES.md`; it runs eval, readiness, SSH check, and outputs the local check block.

---

## 3. Paste blocks (quick reference)

**Test key only (new cloud agent):**

```
Test SSH access to magniphyq. (1) Echo whether MAGNIPHYQ_IP and SSH_KEY_PATH are set (say "set" or "unset", do not print values). (2) Run: test -f "$SSH_KEY_PATH" && echo key_file_exists || echo key_file_missing. (3) Run: ssh -o StrictHostKeyChecking=accept-new -i "$SSH_KEY_PATH" ubuntu@$MAGNIPHYQ_IP "echo ok". (4) Report: key access ok (if you see "ok" from SSH) or what failed (unset var, missing file, or SSH error). Do not output the IP, key path, or key contents.
```

**Full cloud readiness (use after key test passes):**

```
Follow .meta/docs/DIRECTIVE_CLOUD_AGENT_EVAL.md.

First run this pre-flight in your terminal and fix any unset or missing item (set MAGNIPHYQ_IP and SSH_KEY_PATH in Cursor cloud env; ensure the SSH key file exists on this VM at SSH_KEY_PATH):

echo "MAGNIPHYQ_IP=${MAGNIPHYQ_IP:-<unset>}"
echo "SSH_KEY_PATH=${SSH_KEY_PATH:-<unset>}"
test -f "${SSH_KEY_PATH}" && echo "SSH key file: exists" || echo "SSH key file: missing"

Then verify: (1) SSH to magniphyq (ubuntu@$MAGNIPHYQ_IP -i $SSH_KEY_PATH). (2) On magniphyq, ~/condenstate exists with .sst and .ddb. (3) On magniphyq, ~/results exists and is about 4GB+. Output only the --- condenstate_cloud_readiness --- block from that doc. Do not put IP or key in the block. If SSH fails, see .meta/docs/SECRETS_FOR_CLOUD_AGENTS.md section "Cloud agent SSH failed".
```

(Full text and other blocks are in `.meta/docs/PASTE_DIRECTIVES.md`.)

---

## 4. Canon and write discipline (for delegating to agents)

- **Paper 1:** `.sst/paper1/*` (objective_spec, sweep_manifest, figure_manifest, etc.). Manuscript sources: e.g. `paper1/main.tex`, `abstract.md`, `references.bib` (or import from PHY600 per `DIRECTIVE_IMPORT_EXACT_PATHS.md`).
- **Paper 2:** `.sst/paper2/*` (objective_spec, model_spec, sweep_manifest, bridge_notes, etc.).
- **Writes:** New run/fig outputs go to `.meta/runs/paper1/`, `.meta/runs/paper2/`, `.meta/figs/paper1/`, `.meta/figs/paper2/`. Update `.sst/paper1/*` or `.sst/paper2/*` only when there is evidence in `.meta` to bind. After any `.sst` change: run `python3 .ddb/tools/register_sst.py` and commit.
- **Eval:** `make eval` or `python3 .sst/tools/eval_gates.py --report --block` — exit 0 = gates/contracts pass.

---

## 5. Front-end touchpoints and study artifacts

- **Manuscripts:** Paper 1 and Paper 2 LaTeX/sources; figures in repo or under `.meta/figs/`; supplement and references.
- **Artifacts:** Simulation outputs and analysis live on magniphyq (`~/results/`, path-normalized analysis/registry as needed). Cloud agents reach them via SSH; local agent may use `PHY600_ROOT` or the same paths.
- **Dashboard / external links:** Any monitor or front-end URLs are documented in the repo (e.g. `.sst/` or `.meta/docs`). Keep references consistent and host-agnostic in the public mirror; do not commit live IPs or secrets. Polish any public-facing copy (README, docs, figure captions) so submission and peer review are straightforward.

---

## 6. March timeline

- **Now (2/25):** Orchestrator and cloud agents ready; key verified.
- **March:** Preprint submission (e.g. bioRxiv) and journal shopping. All improvements and polish should leave the repo in a state where submission and sharing with referees are seamless.

---

## 7. One-line handoff to the orchestrator

**Condenstate is the public mirror for Paper 1 and Paper 2. Cloud agents have SSH key access to magniphyq and can run the cloud readiness directive. Use the paste blocks in `.meta/docs/PASTE_DIRECTIVES.md` to test key and run full readiness. Delegate paper improvements and front-end touchpoints to those agents; enforce canon and write discipline from `SYNAPSIN_ORCHESTRATION_PLAYBOOK.md` and `.sst/layout_policy.md`. Target: polished and peer-review ready for March preprint and journal submission.**
