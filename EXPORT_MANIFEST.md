# synapsin export manifest

This manifest defines what to export from PHY600 into a new public `synapsin` repository, with explicit classification and line-cited rationale.

## Included for export

| Path | Classification | Decision | Reason (line-cited) |
|---|---|---|---|
| `bioRxiv_preprint_synapsin/main.tex` | required for paper 1 | export | Manuscript source declares the synapsin computational phase diagram objective and reports the multi-stage simulation campaign and interaction-model comparison sections needed for paper 1 framing. `[bioRxiv_preprint_synapsin/main.tex:L16-L44]` `[bioRxiv_preprint_synapsin/main.tex:L96-L104]` |
| `bioRxiv_preprint_synapsin/abstract.md` | required for paper 1 | export | Abstract defines phase-diagram scope, parameter ranges, phosphorylation interpretation, and 1-1 vs 1-2 comparison summary. `[bioRxiv_preprint_synapsin/abstract.md:L13-L23]` |
| `bioRxiv_preprint_synapsin/references.bib` | required for paper 1 | export | Citation database exists and contains referenced condensate and synapsin literature entries used by manuscript text. `[bioRxiv_preprint_synapsin/references.bib:L1-L32]` |
| `rerun_v2/pipeline/analyze_sim.py` | required for paper 1 | export | Analysis pipeline computes campaign order parameters and explicitly defines cross-type 1-2 contact metrics, Cv, clustering, S(q), and g12(r) used for quantitative outputs. `[rerun_v2/pipeline/analyze_sim.py:L5-L20]` `[rerun_v2/pipeline/analyze_sim.py:L984-L1051]` |
| `rerun_v2/pipeline/generate_canonical_figures.py` | required for paper 1 | export | Figure generator reads analysis registry plus FENE summary and writes canonical figure files for main and supplementary outputs. `[rerun_v2/pipeline/generate_canonical_figures.py:L204-L220]` |
| `rerun_v2/pipeline/build_figure_manifest.py` | required for paper 1 | export | Figure manifest builder maps figure IDs to source simulations and output files, including manuscript placement metadata. `[rerun_v2/pipeline/build_figure_manifest.py:L69-L127]` |
| `rerun_v2/pipeline/sweep.sh` | required for paper 1 | export | Sweep orchestrator scans fleet completion and runs collect/fire/analyze/integrate sequence for completed simulations. `[rerun_v2/pipeline/sweep.sh:L2-L15]` |
| `assets/aws_cli_package/simulation/deep_research_upload/parameters/simulation_matrix.csv` | required for paper 1 | export | Simulation matrix defines parameter-space coverage across core grid, valency, chain length, fine grid, replicate, and control categories. `[assets/aws_cli_package/simulation/deep_research_upload/parameters/simulation_matrix.csv:L1-L16]` `[assets/aws_cli_package/simulation/deep_research_upload/parameters/simulation_matrix.csv:L67-L75]` |
| `assets/aws_cli_package/simulation/run_single_sim.sh` | required for paper 1 | export | Single-run driver defines parameterized simulation execution and invokes S1-S4 generators before writing completion markers. `[assets/aws_cli_package/simulation/run_single_sim.sh:L5-L8]` `[assets/aws_cli_package/simulation/run_single_sim.sh:L94-L107]` `[assets/aws_cli_package/simulation/run_single_sim.sh:L155-L166]` |
| `Presentations/modeling/run_pipeline.py` | required for paper 2 | export | Pipeline orchestrator defines six modeling phases including ODE, spiking, vesicle, figure generation, and manuscript integration. `[Presentations/modeling/run_pipeline.py:L9-L16]` `[Presentations/modeling/run_pipeline.py:L361-L368]` |
| `Presentations/modeling/config.yaml` | required for paper 2 | export | Configuration encodes paper 2 model parameters, gates, and required figures for each phase. `[Presentations/modeling/config.yaml:L20-L48]` `[Presentations/modeling/config.yaml:L117-L127]` |
| `Presentations/modeling/bridge_lammps_to_ode.py` | required for paper 2 | export | Bridge module maps LAMMPS metrics to ODE material-state eta and compares phosphorylation conditions for cross-scale interpretation. `[Presentations/modeling/bridge_lammps_to_ode.py:L3-L15]` `[Presentations/modeling/bridge_lammps_to_ode.py:L211-L267]` |
| `Presentations/modeling/phase4_analysis/generate_figures.py` | required for paper 2 | export | Paper 2 figure generator loads phase artifacts and emits the required five publication figures. `[Presentations/modeling/phase4_analysis/generate_figures.py:L20-L42]` `[Presentations/modeling/phase4_analysis/generate_figures.py:L539-L588]` |
| `Presentations/modeling/PLAN.md` | required for paper 2 | export | Plan file defines gated autonomous modeling phases and expected artifacts for the material-eligibility workflow. `[Presentations/modeling/PLAN.md:L2-L4]` `[Presentations/modeling/PLAN.md:L173-L178]` `[Presentations/modeling/PLAN.md:L324-L335]` |
| `AGENTS.md` | required for agent onboarding | export | Repository-level onboarding and completion workflow for bead tracking and git hygiene. `[AGENTS.md:L3-L13]` `[AGENTS.md:L21-L33]` |
| `Makefile` | required for agent onboarding | export | Canonical commands expose `ddb-register`, state refresh, and monitor backend entrypoint. `[Makefile:L1-L10]` |
| `.sst/index.md` | required for agent onboarding | export | Canonical state index defines `.sst` + `.ddb` as monitor source of truth and enforcement flow. `[.sst/index.md:L12-L33]` |
| `.sst/resume_protocol.md` | required for agent onboarding | export | Resume contract defines lifecycle mismatch, orphan, and override gates. `[.sst/resume_protocol.md:L14-L27]` |
| `.sst/tools/lifecycle_guard.py` | required for agent onboarding | export | Guard code enforces lifecycle consistency and orphan override checks with explicit abort reasons. `[.sst/tools/lifecycle_guard.py:L58-L111]` |
| `.ddb/PROTOCOL.md` | required for agent onboarding | export | Deterministic hashing, decision-id formula, and supersede rules are specified here. `[.ddb/PROTOCOL.md:L5-L45]` |
| `.ddb/tools/register_sst.py` | required for agent onboarding | export | Adapter code implements canonicalization, parser behavior, decision-id derivation, and registry upsert semantics. `[.ddb/tools/register_sst.py:L21-L33]` `[.ddb/tools/register_sst.py:L53-L69]` `[.ddb/tools/register_sst.py:L92-L100]` `[.ddb/tools/register_sst.py:L219-L263]` |
| `.meta/docs/SST_DDB_CRASHCOURSE.md` | required for agent onboarding | export | Concise operational explanation of `.sst` state surface and `.ddb` deterministic registry flow. `[.meta/docs/SST_DDB_CRASHCOURSE.md:L5-L15]` |

## Legacy or transform-before-export

| Path | Classification | Decision | Reason (line-cited) |
|---|---|---|---|
| `rerun_v2/analysis_registry.json` | legacy | transform-before-export | Registry embeds absolute local paths in result references, so direct export violates repo-relative mirror policy and needs path normalization. `[rerun_v2/analysis_registry.json:L93-L107]` |
| `Presentations/modeling/AGENT_HANDOFF.md` | legacy | transform-before-export | File uses hardcoded local absolute paths and machine-specific run instructions, so it is not mirror-clean onboarding content. `[Presentations/modeling/AGENT_HANDOFF.md:L9-L11]` `[Presentations/modeling/AGENT_HANDOFF.md:L57-L76]` |

## Blocked (do not export)

| Path | Classification | Decision | Blocking trigger (line-cited) |
|---|---|---|---|
| `.cursor/rules/cloudflare-tunnel-config.mdc` | legacy | blocked | Contains host-bound tunnel configuration and a service-install credential string. `[.cursor/rules/cloudflare-tunnel-config.mdc:L10-L23]` |
| `.ssh/pax-ec2-key.pem` | legacy | blocked | Private key material is present. `[.ssh/pax-ec2-key.pem:L1-L1]` |
| `Presentations/synapsin_modeling/EC2_DEPLOYMENT.md` | legacy | blocked | Contains hardcoded instance identifiers, public endpoint data, and SSH-key specific commands. `[Presentations/synapsin_modeling/EC2_DEPLOYMENT.md:L7-L18]` `[Presentations/synapsin_modeling/EC2_DEPLOYMENT.md:L67-L68]` |
| `rerun_v2/pipeline/config.sh` | legacy | blocked | Contains hardcoded remote endpoint address and SSH key path assumptions. `[rerun_v2/pipeline/config.sh:L15-L18]` `[rerun_v2/pipeline/config.sh:L26-L27]` |
| `.sst/monitor_architecture.json` | legacy | blocked | Contains hardcoded external frontend/backend host targets; mirror export must stay host-agnostic. `[.sst/monitor_architecture.json:L18-L26]` |
| `.meta/docs/MONITOR_ARCHITECTURE.md` | legacy | blocked | Documentation is pinned to external host targets and is not mirror-local. `[.meta/docs/MONITOR_ARCHITECTURE.md:L9-L10]` |
