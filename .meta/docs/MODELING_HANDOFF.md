# Agent Handoff: Material Eligibility Modeling Pipeline

All paths below are **relative to the repository root** (the directory that contains `.sst`).

## Context

This is a computational neuroscience modeling project to support a presentation on synaptic vesicle condensates as eligibility variables. The goal is to build computational evidence that **condensate material state can function as a slow eligibility variable** that gates synaptic plasticity.

## What Already Exists

- `paper1/main.tex` – Manuscript (needs modeling section added)
- `paper1/main.pdf` – Current compiled version (4 pages)
- `simulation/` – Reference implementation pattern (LAMMPS simulation with similar structure), if present

## Your Mission

Execute the 6-phase pipeline autonomously. Each phase has:
1. A script to run
2. A test with gate criteria
3. An artifact that must be produced

**Do not stop to ask questions.** If a phase fails its gate, debug and retry until it passes, then freeze that phase and continue.

## Phase Summary

| Phase | What to Build | Gate Criterion | Artifact |
|-------|--------------|----------------|----------|
| 0 | Environment setup | Brian2 installs, tests pass | `phase0_env_test.json` |
| 1 | ODE model with material eligibility | Bifurcation detected, dynamics differ from baseline | `phase1_ode_results.json` |
| 2 | Brian2 spiking network with 4-factor learning | Learning curves differ (p<0.05), history effect >0.3 | `phase2_brian2_results.json` |
| 3 | Vesicle pool model with condensate coupling | PPR correlates with eta (p<0.05) | `phase3_vesicle_results.json` |
| 4 | Generate 5 publication figures | 5+ valid PDFs | `phase4_figures.json` |
| 5 | Update manuscript with results | PDF compiles with 6+ pages | `main.pdf` |

## Key Equations

### Material Eligibility ODE (Phase 1)
```python
dE/dt = -E/tau_E + activity                    # Fast eligibility (seconds)
deta/dt = (eta_0 - eta)/tau_eta + phosph*act   # Slow material state (minutes)
dw/dt = E * dopamine * sigmoid(eta_thresh - eta)  # Gated plasticity
```

### Four-Factor Learning Rule (Phase 2)
```
Standard 3-factor: dw = E * R (eligibility * reward)
Our 4-factor: dw = E * R * g(eta)  where g(eta) = 1/(1 + exp(k*(eta - threshold)))
```

### Vesicle Pool with Condensate (Phase 3)
```
Reserve -> Intermediate -> RRP -> Released
k_mobilization = k_max / (1 + eta/eta_half)  # Condensate slows vesicle mobilization
```

## Success Criteria

The pipeline is complete when:
1. All 5 figures exist in `paper1/figures/` (or `figures/` at repo root)
2. `paper1/main.pdf` has 6+ pages including a "Computational Modeling" section
3. All `phase*_results.json` artifacts exist with `status: pass`

## How to Start

```bash
cd modeling

# Phase 0: Setup environment
pip install brian2 numpy scipy matplotlib

# Then run each phase in order, checking gates before proceeding
python phase0_setup/test_environment.py
python phase1_ode/parameter_sweep.py
python phase2_spiking/network_simulation.py
python phase3_vesicle/condensate_coupling.py
python phase4_analysis/generate_figures.py
python phase5_manuscript/update_manuscript.py
```

## Reference Papers (for parameter values)

1. **Eligibility traces**: Gerstner et al. 2018 - tau_E ~ 1-5 seconds
2. **Synapsin condensates**: Wu et al. 2023 - material timescale ~ minutes
3. **Vesicle pools**: Schneggenburger & Neher 2000 - RRP ~2000, k_mobilization ~0.02/s
4. **cAMP gating**: Qiu et al. 2024 - bidirectional plasticity based on slow state

## Files to Create

See `modeling/PLAN.md` in this repo for the full phase specification. Key files needed:

- `phase0_setup/requirements.txt`
- `phase0_setup/test_environment.py`
- `phase1_ode/material_eligibility_ode.py`
- `phase1_ode/parameter_sweep.py`
- `phase1_ode/test_phase1.py`
- `phase2_spiking/four_factor_learning.py`
- `phase2_spiking/network_simulation.py`
- `phase2_spiking/test_phase2.py`
- `phase3_vesicle/vesicle_pool_model.py`
- `phase3_vesicle/condensate_coupling.py`
- `phase3_vesicle/test_phase3.py`
- `phase4_analysis/generate_figures.py`
- `phase4_analysis/statistical_tests.py`
- `phase5_manuscript/update_manuscript.py`

## Guardrails

1. **Freeze on pass**: When a phase passes its gate, commit artifacts to git and do not modify
2. **Retry on fail**: If gate fails, debug and retry (up to 5 attempts) before escalating
3. **No human input**: Run autonomously until complete or blocked by infrastructure issue
4. **Artifact-first**: Always produce the JSON artifact even if partial, for debugging

## Final Deliverable

When complete, the user should have:
1. Updated `paper1/main.pdf` with computational results integrated
2. 5 figures in `paper1/figures/` (or `figures/`)
3. All phase artifacts in `modeling/` directory
4. Git history showing phase progression
