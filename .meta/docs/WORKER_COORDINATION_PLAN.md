# Worker coordination plan

## thing1: plan
Paper 1 runs first as the throughput driver, since it pins the data products that everything else can cite. Paper 2 runs in parallel, since it can be advanced from the current drafts without waiting on new simulation output. The coordination rule stays simple: Paper 1 produces registered sweep artifacts and figures, then Paper 2 is allowed to cite those artifacts for its anchoring claims.

## thing2: paper1_sequence
Paper 1 should move in a tight loop: lock the objective spec, run the sweep, register outputs, then mint phase boundary objects and figures with evidence slices. After that loop closes once, widen the sweep grid or add replicates, then repeat the same loop with supersession.

## thing3: paper2_sequence
Paper 2 should move as a formalization pass: lock the model spec, define the slow state proxy and the update rule family, define the metrics, then run the smallest experiment that produces a stable regime map figure. After that first figure exists, refine the narrative constraints and tighten any language that risks sounding causal.

## thing4: cloud_breakdown
Run two cloud workers in parallel. Worker A owns Paper 1 compute and phase diagram products. Worker B owns Paper 2 model spec, metrics, and the first figure.

## thing5: handoff_rules
Any write to .sst must follow an existing .meta output and a new evidence slice entry. After each .sst write, run register_sst.py, then commit and push. If a gate fails, the worker stops and writes a short gap note into .meta/reports for the next agent.

## thing6: first_cloud_directive_choice
Start with Worker A on Paper 1, since it can confirm whether magniphyq has the full results tree and can scale the sweep without blocking the rest. Worker B can start immediately on Paper 2 with a no-compute pass that locks schemas, names metrics, and prepares a figure manifest so the first run lands cleanly.
