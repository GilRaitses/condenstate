#!/usr/bin/env python3
"""
Bridge LAMMPS sticker-spacer simulation metrics to ODE material eligibility model.

This script:
1. Reads metrics from LAMMPS simulations (metrics_summary.csv)
2. Maps microscopic observables to mesoscopic material state η
3. Re-runs ODE model with LAMMPS-informed parameters
4. Compares phosphorylated (A2B22) vs dephosphorylated (A4B20) conditions

Mapping:
    η = η_scale × fraction_in_largest_cluster + η_offset
    
This provides a physical interpretation of the abstract η parameter.
"""

import os
import json
import numpy as np
from scipy.integrate import odeint
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import csv


# ============================================================
# LAMMPS METRICS LOADING
# ============================================================

def load_metrics(csv_path: str) -> List[Dict]:
    """Load metrics from LAMMPS quick_analysis.py output."""
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found")
        return []
    
    metrics = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            for key in ['stickers', 'spacers', 'temp', 'epsilon', 
                       'rg_mean', 'rg_std', 'n_clusters', 'largest_cluster',
                       'mean_cluster_size', 'fraction_in_largest', 
                       'density_contrast', 'density_std']:
                if key in row and row[key]:
                    try:
                        row[key] = float(row[key])
                    except ValueError:
                        pass
            metrics.append(row)
    
    return metrics


def get_metrics_by_condition(metrics: List[Dict], 
                              architecture: str = None,
                              temp: float = None,
                              epsilon: float = None) -> List[Dict]:
    """Filter metrics by experimental conditions."""
    filtered = metrics
    
    if architecture:
        filtered = [m for m in filtered if m.get('architecture') == architecture]
    if temp:
        filtered = [m for m in filtered if m.get('temp') == temp]
    if epsilon:
        filtered = [m for m in filtered if m.get('epsilon') == epsilon]
    
    return filtered


# ============================================================
# η MAPPING FUNCTIONS
# ============================================================

def map_fraction_to_eta(fraction_in_largest: float,
                        eta_scale: float = 1.5,
                        eta_offset: float = 0.1,
                        eta_max: float = 2.0) -> float:
    """
    Map cluster fraction to material state η.
    
    Higher fraction_in_largest → more phase separation → higher η
    
    Args:
        fraction_in_largest: Fraction of chains in largest cluster (0-1)
        eta_scale: Scaling factor
        eta_offset: Baseline η when no clustering
        eta_max: Maximum η value
        
    Returns:
        η value for ODE model
    """
    eta = eta_offset + eta_scale * fraction_in_largest
    return min(eta, eta_max)


def map_density_contrast_to_eta(density_contrast: float,
                                 eta_scale: float = 0.3,
                                 eta_offset: float = 0.2) -> float:
    """
    Alternative mapping using density contrast.
    
    Higher density contrast → more phase separation → higher η
    """
    # Density contrast of 1 means uniform, >1 means non-uniform
    eta = eta_offset + eta_scale * (density_contrast - 1)
    return max(0, eta)


def estimate_eta_from_metrics(metrics: Dict, 
                               method: str = 'fraction') -> float:
    """
    Estimate η from LAMMPS metrics.
    
    Args:
        metrics: Dictionary with LAMMPS metrics
        method: 'fraction' or 'density' or 'combined'
        
    Returns:
        Estimated η value
    """
    if method == 'fraction':
        return map_fraction_to_eta(metrics.get('fraction_in_largest', 0.5))
    elif method == 'density':
        return map_density_contrast_to_eta(metrics.get('density_contrast', 1.0))
    elif method == 'combined':
        eta_frac = map_fraction_to_eta(metrics.get('fraction_in_largest', 0.5))
        eta_dens = map_density_contrast_to_eta(metrics.get('density_contrast', 1.0))
        return 0.7 * eta_frac + 0.3 * eta_dens
    else:
        raise ValueError(f"Unknown method: {method}")


# ============================================================
# ODE MODEL (from phase1)
# ============================================================

def material_eligibility_ode(y, t, tau_E, tau_eta, eta_0, eta_thresh, k, phosph_rate):
    """ODE system for material eligibility gating."""
    E, eta, w = y
    
    # Pulsed activity (every 10 seconds for 1 second)
    activity = 1.0 if (t % 10) < 1 else 0.0
    # Delayed dopamine (arrives 2 seconds after activity)
    dopamine = 1.0 if ((t - 2) % 10) < 0.5 and t > 2 else 0.0
    
    # ODEs
    dE_dt = -E / tau_E + activity
    deta_dt = (eta_0 - eta) / tau_eta + phosph_rate * activity
    
    # Material gating
    material_gate = 1 / (1 + np.exp(k * (eta - eta_thresh)))
    dw_dt = E * dopamine * material_gate
    
    return [dE_dt, deta_dt, dw_dt]


def run_ode_with_eta0(eta_0: float, 
                      eta_thresh: float = 0.5,
                      tau_E: float = 1.0,
                      tau_eta: float = 120.0,
                      k_gate: float = 10.0,
                      phosph_rate: float = 0.1,
                      t_max: float = 500.0,
                      dt: float = 0.01) -> Dict:
    """
    Run ODE model with specified initial η.
    
    Args:
        eta_0: Initial/baseline material state (from LAMMPS)
        eta_thresh: Gating threshold
        Other params: ODE parameters
        
    Returns:
        Results dictionary
    """
    t = np.linspace(0, t_max, int(t_max / dt))
    
    # Initial conditions: E=0, eta=eta_0, w=0.5
    y0 = [0, eta_0, 0.5]
    
    sol = odeint(
        material_eligibility_ode, y0, t,
        args=(tau_E, tau_eta, eta_0, eta_thresh, k_gate, phosph_rate)
    )
    
    E_trace = sol[:, 0]
    eta_trace = sol[:, 1]
    w_trace = sol[:, 2]
    
    # Compute gating over time
    gate_trace = 1 / (1 + np.exp(k_gate * (eta_trace - eta_thresh)))
    
    return {
        't': t,
        'E': E_trace,
        'eta': eta_trace,
        'w': w_trace,
        'gate': gate_trace,
        'final_weight': w_trace[-1],
        'mean_gate': np.mean(gate_trace),
        'time_above_thresh': np.mean(eta_trace > eta_thresh)
    }


# ============================================================
# PHOSPHORYLATION COMPARISON
# ============================================================

def compare_phosphorylation_states(metrics_a4b20: List[Dict],
                                    metrics_a2b22: List[Dict],
                                    epsilon: float = 5.0,
                                    temp: float = 300.0) -> Dict:
    """
    Compare dephosphorylated (A4B20) vs phosphorylated (A2B22) conditions.
    
    Args:
        metrics_a4b20: Metrics for A4B20 (4 stickers, dephosphorylated)
        metrics_a2b22: Metrics for A2B22 (2 stickers, phosphorylated)
        epsilon: Interaction strength to compare at
        temp: Temperature to compare at
        
    Returns:
        Comparison results
    """
    # Filter to matching conditions
    a4 = get_metrics_by_condition(metrics_a4b20, 'A4B20', temp, epsilon)
    a2 = get_metrics_by_condition(metrics_a2b22, 'A2B22', temp, epsilon)
    
    if not a4:
        print(f"No A4B20 data for ε={epsilon}, T={temp}K")
        # Use placeholder
        eta_dephos = 0.8
    else:
        eta_dephos = estimate_eta_from_metrics(a4[0])
    
    if not a2:
        print(f"No A2B22 data for ε={epsilon}, T={temp}K")
        # Use placeholder (expect lower clustering)
        eta_phos = 0.4
    else:
        eta_phos = estimate_eta_from_metrics(a2[0])
    
    # Run ODE for both conditions
    results_dephos = run_ode_with_eta0(eta_dephos)
    results_phos = run_ode_with_eta0(eta_phos)
    
    return {
        'epsilon': epsilon,
        'temp': temp,
        'eta_dephosphorylated': eta_dephos,
        'eta_phosphorylated': eta_phos,
        'delta_eta': eta_dephos - eta_phos,
        'final_weight_dephos': results_dephos['final_weight'],
        'final_weight_phos': results_phos['final_weight'],
        'weight_ratio': results_phos['final_weight'] / (results_dephos['final_weight'] + 1e-10),
        'mean_gate_dephos': results_dephos['mean_gate'],
        'mean_gate_phos': results_phos['mean_gate'],
        'interpretation': (
            'Phosphorylation reduces clustering (lower η), '
            'which opens the material gate, allowing more plasticity.'
            if eta_phos < eta_dephos else
            'Unexpected: phosphorylation increased clustering.'
        )
    }


# ============================================================
# TEMPERATURE DEPENDENCE
# ============================================================

def analyze_valency_sweep(metrics: List[Dict],
                          epsilon: float = 5.0,
                          temp: float = 300.0,
                          eta_scale: float = 1.5,
                          eta_offset: float = 0.1) -> List[Dict]:
    """At fixed (epsilon, temp), compute mean eta and ODE outputs per architecture."""
    from collections import defaultdict
    grouped = defaultdict(list)
    for m in metrics:
        try:
            ep, t = float(m.get('epsilon', 0)), float(m.get('temp', 0))
        except (TypeError, ValueError):
            continue
        if abs(ep - epsilon) < 0.01 and abs(t - temp) < 0.1:
            arch = m.get('architecture', '')
            if arch and m.get('fraction_in_largest') is not None:
                grouped[arch].append(m)
    out = []
    for arch in sorted(grouped.keys()):
        vals = grouped[arch]
        fracs = [float(v['fraction_in_largest']) for v in vals]
        mean_frac = np.mean(fracs)
        eta = map_fraction_to_eta(mean_frac, eta_scale=eta_scale, eta_offset=eta_offset)
        ode = run_ode_with_eta0(eta)
        out.append({
            'architecture': arch,
            'eta': float(eta),
            'final_weight': float(ode['final_weight']),
            'mean_gate': float(ode['mean_gate']),
            'n_sims': len(vals),
            'fraction_in_largest_mean': float(mean_frac)
        })
    return out


def analyze_epsilon_sweep(metrics: List[Dict],
                          architecture: str = 'A4B20',
                          temp: float = 300.0,
                          eta_scale: float = 1.5,
                          eta_offset: float = 0.1) -> List[Dict]:
    """At fixed (architecture, temp), compute mean eta and ODE outputs per epsilon."""
    from collections import defaultdict
    grouped = defaultdict(list)
    for m in metrics:
        if m.get('architecture') != architecture:
            continue
        try:
            t = float(m.get('temp', 0))
        except (TypeError, ValueError):
            continue
        if abs(t - temp) < 0.1 and m.get('fraction_in_largest') is not None:
            ep = float(m.get('epsilon', 0))
            grouped[ep].append(m)
    out = []
    for ep in sorted(grouped.keys()):
        vals = grouped[ep]
        fracs = [float(v['fraction_in_largest']) for v in vals]
        mean_frac = np.mean(fracs)
        eta = map_fraction_to_eta(mean_frac, eta_scale=eta_scale, eta_offset=eta_offset)
        ode = run_ode_with_eta0(eta)
        out.append({
            'epsilon': float(ep),
            'eta': float(eta),
            'final_weight': float(ode['final_weight']),
            'mean_gate': float(ode['mean_gate']),
            'n_sims': len(vals),
            'fraction_in_largest_mean': float(mean_frac)
        })
    return out


def run_sensitivity_grid(metrics: List[Dict],
                         scale_range=(1.05, 1.95),
                         offset_range=(0.07, 0.13),
                         n_scale: int = 3,
                         n_offset: int = 3) -> Dict:
    """Vary eta_scale and eta_offset; re-run phosphorylation comparison. Return grid of weight_ratio."""
    scales = np.linspace(scale_range[0], scale_range[1], n_scale)
    offsets = np.linspace(offset_range[0], offset_range[1], n_offset)
    a4 = get_metrics_by_condition(metrics, 'A4B20', 300.0, 5.0)
    a2 = get_metrics_by_condition(metrics, 'A2B22', 300.0, 5.0)
    if not a4 or not a2:
        return {'weight_ratios': [], 'scales': scales.tolist(), 'offsets': offsets.tolist()}
    grid = []
    for eta_scale in scales:
        row = []
        for eta_offset in offsets:
            eta_d = map_fraction_to_eta(a4[0].get('fraction_in_largest', 0), eta_scale=eta_scale, eta_offset=eta_offset)
            eta_p = map_fraction_to_eta(a2[0].get('fraction_in_largest', 0), eta_scale=eta_scale, eta_offset=eta_offset)
            r_d = run_ode_with_eta0(eta_d)
            r_p = run_ode_with_eta0(eta_p)
            ratio = r_p['final_weight'] / (r_d['final_weight'] + 1e-10)
            row.append(float(ratio))
        grid.append(row)
    return {
        'weight_ratios': grid,
        'scales': scales.tolist(),
        'offsets': offsets.tolist(),
        'interpretation': 'Weight ratio > 1 (phos/dephos) across grid => direction robust'
    }


def analyze_temperature_dependence(metrics: List[Dict],
                                    architecture: str = 'A4B20',
                                    epsilon: float = 5.0) -> Dict:
    """
    Analyze how η varies with temperature.
    
    Lower T → stronger phase separation → higher η → more gating
    """
    results = {}
    
    for temp in [250, 275, 300, 325]:
        filtered = get_metrics_by_condition(metrics, architecture, float(temp), epsilon)
        
        if filtered:
            eta = estimate_eta_from_metrics(filtered[0])
            ode_results = run_ode_with_eta0(eta)
            
            results[temp] = {
                'eta': eta,
                'final_weight': ode_results['final_weight'],
                'mean_gate': ode_results['mean_gate'],
                'fraction_in_largest': filtered[0].get('fraction_in_largest', None)
            }
        else:
            results[temp] = {'eta': None, 'note': 'No data'}
    
    return results


# ============================================================
# MAIN
# ============================================================

def main():
    """Run bridging analysis."""
    print("=" * 60)
    print("LAMMPS → ODE BRIDGING ANALYSIS")
    print("=" * 60)
    
    # Try to load real metrics
    base_dir = Path(__file__).parent.parent
    modeling_dir = Path(__file__).parent

    # Paths to check for metrics (combined CSV from rerun_v2 results is preferred)
    metric_paths = [
        modeling_dir / "bridge_metrics_combined.csv",
        base_dir / "synapsin_modeling" / "runs" / "synapsin" / "metrics_summary.csv",
        base_dir / "synapsin_modeling" / "runs" / "synapsin_high_eps" / "metrics_summary.csv",
        base_dir / "synapsin_modeling" / "runs" / "temp_sweep" / "metrics_summary.csv",
        Path.home() / "synapsin_modeling" / "simulation" / "runs" / "temp_sweep" / "metrics_summary.csv",
        Path.home() / "synapsin_phospho" / "runs" / "phospho" / "metrics_summary.csv",
    ]
    
    all_metrics = []
    for path in metric_paths:
        if path.exists():
            print(f"Loading: {path}")
            all_metrics.extend(load_metrics(str(path)))
    
    if not all_metrics:
        print("\nNo LAMMPS metrics found. Using placeholder values for demonstration.")
        print("Run quick_analysis.py on simulation outputs to generate real metrics.\n")
        
        # Create placeholder metrics for demonstration
        all_metrics = [
            {'architecture': 'A4B20', 'temp': 300, 'epsilon': 5.0, 
             'fraction_in_largest': 0.65, 'density_contrast': 2.3},
            {'architecture': 'A4B20', 'temp': 250, 'epsilon': 5.0,
             'fraction_in_largest': 0.82, 'density_contrast': 3.1},
            {'architecture': 'A4B20', 'temp': 325, 'epsilon': 5.0,
             'fraction_in_largest': 0.45, 'density_contrast': 1.6},
            {'architecture': 'A2B22', 'temp': 300, 'epsilon': 5.0,
             'fraction_in_largest': 0.35, 'density_contrast': 1.4},
        ]
    
    # Separate by architecture
    a4b20_metrics = [m for m in all_metrics if m.get('architecture') == 'A4B20']
    a2b22_metrics = [m for m in all_metrics if m.get('architecture') == 'A2B22']
    
    print(f"\nLoaded {len(a4b20_metrics)} A4B20 runs, {len(a2b22_metrics)} A2B22 runs")
    
    # === Analysis 1: Phosphorylation comparison ===
    print("\n" + "=" * 60)
    print("PHOSPHORYLATION EFFECT (A4B20 vs A2B22)")
    print("=" * 60)
    
    comparison = compare_phosphorylation_states(a4b20_metrics, a2b22_metrics, epsilon=5.0)
    
    print(f"\nAt ε=5.0, T=300K:")
    print(f"  η (dephosphorylated, A4B20): {comparison['eta_dephosphorylated']:.3f}")
    print(f"  η (phosphorylated, A2B22):   {comparison['eta_phosphorylated']:.3f}")
    print(f"  Δη (phosphorylation effect): {comparison['delta_eta']:.3f}")
    print(f"\nODE Results:")
    print(f"  Final weight (dephos): {comparison['final_weight_dephos']:.3f}")
    print(f"  Final weight (phos):   {comparison['final_weight_phos']:.3f}")
    print(f"  Weight ratio (phos/dephos): {comparison['weight_ratio']:.2f}x")
    print(f"  Mean gate (dephos): {comparison['mean_gate_dephos']:.3f}")
    print(f"  Mean gate (phos):   {comparison['mean_gate_phos']:.3f}")
    print(f"\nInterpretation: {comparison['interpretation']}")
    
    # === Analysis 2: Temperature dependence ===
    print("\n" + "=" * 60)
    print("TEMPERATURE DEPENDENCE (A4B20, ε=5)")
    print("=" * 60)
    
    temp_results = analyze_temperature_dependence(a4b20_metrics, 'A4B20', 5.0)
    
    print(f"\n{'T (K)':<10} {'η':<10} {'Final w':<12} {'Mean gate':<10}")
    print("-" * 42)
    for temp in sorted(temp_results.keys()):
        r = temp_results[temp]
        if r.get('eta') is not None:
            print(f"{temp:<10} {r['eta']:<10.3f} {r['final_weight']:<12.3f} {r['mean_gate']:<10.3f}")
        else:
            print(f"{temp:<10} {'N/A':<10} {'N/A':<12} {'N/A':<10}")
    
    print("\nLower T → higher η → more gating → less plasticity")
    print("Higher T → lower η → less gating → more plasticity")
    
    # === Analysis 3: Valency sweep (epsilon=5, T=300) ===
    valency_sweep = analyze_valency_sweep(all_metrics, epsilon=5.0, temp=300.0)
    print("\n" + "=" * 60)
    print("VALENCY SWEEP (ε=5, T=300 K)")
    print("=" * 60)
    for v in valency_sweep:
        print(f"  {v['architecture']}: η={v['eta']:.3f}, final_w={v['final_weight']:.3f}, mean_gate={v['mean_gate']:.3f} (n={v['n_sims']})")

    # === Analysis 4: Epsilon sweep (A4B20, T=300) ===
    epsilon_sweep = analyze_epsilon_sweep(all_metrics, architecture='A4B20', temp=300.0)
    print("\n" + "=" * 60)
    print("EPSILON SWEEP (A4B20, T=300 K)")
    print("=" * 60)
    for e in epsilon_sweep[:5]:
        print(f"  ε={e['epsilon']:.0f}: η={e['eta']:.3f}, mean_gate={e['mean_gate']:.3f}")
    if len(epsilon_sweep) > 5:
        print(f"  ... ({len(epsilon_sweep)} points total)")

    # === Analysis 5: Sensitivity grid ===
    sensitivity = run_sensitivity_grid(all_metrics, n_scale=3, n_offset=3)
    print("\n" + "=" * 60)
    print("SENSITIVITY (weight ratio phos/dephos)")
    print("=" * 60)
    if sensitivity.get('weight_ratios'):
        for i, row in enumerate(sensitivity['weight_ratios']):
            print(f"  scale={sensitivity['scales'][i]:.2f}: {[f'{x:.3f}' for x in row]}")

    # === Save results ===
    output_path = Path(__file__).parent / "bridge_results.json"
    results = {
        'phosphorylation_comparison': comparison,
        'temperature_dependence': {str(k): v for k, v in temp_results.items()},
        'valency_sweep': valency_sweep,
        'epsilon_sweep': epsilon_sweep,
        'sensitivity': sensitivity,
        'mapping_parameters': {
            'method': 'fraction',
            'eta_scale': 1.5,
            'eta_offset': 0.1,
            'eta_thresh': 0.5
        }
    }
    
    # Convert numpy arrays for JSON
    def convert_for_json(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_for_json(v) for v in obj]
        elif isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        return obj
    
    with open(output_path, 'w') as f:
        json.dump(convert_for_json(results), f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    print("\n" + "=" * 60)
    print("BRIDGING COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()
