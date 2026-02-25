"""
Generate publication-quality figures for Phase 4
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns
import json
from pathlib import Path
from typing import Dict, List


# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")


def load_results() -> Dict:
    """Load results from all previous phases."""
    results = {}
    
    # Get the base directory (modeling/)
    base_dir = Path(__file__).parent.parent
    
    # Load Phase 1 results
    phase1_path = base_dir / "phase1_ode_results.json"
    with open(phase1_path) as f:
        results['phase1'] = json.load(f)
    
    # Load Phase 2 results
    phase2_path = base_dir / "phase2_brian2_results.json"
    with open(phase2_path) as f:
        results['phase2'] = json.load(f)
    
    # Load Phase 3 results
    phase3_path = base_dir / "phase3_vesicle_results.json"
    with open(phase3_path) as f:
        results['phase3'] = json.load(f)
    
    return results


def create_fig1_ode_dynamics(results: Dict, save_path: Path) -> None:
    """Figure 1: ODE dynamics showing material eligibility gating."""
    phase1 = results['phase1']
    
    fig = plt.figure(figsize=(12, 10))
    gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)
    
    # Panel A: Weight dynamics comparison
    ax1 = fig.add_subplot(gs[0, :])
    t = np.array(phase1['t'])
    ax1.plot(t, phase1['w_gated'], label='4-factor (with material gating)', 
             linewidth=2.5, color='#e74c3c')
    ax1.plot(t, phase1['w_nogated'], label='3-factor (no gating)', 
             linewidth=2.5, linestyle='--', color='#3498db')
    ax1.set_xlabel('Time (s)', fontsize=12)
    ax1.set_ylabel('Synaptic Weight', fontsize=12)
    ax1.set_title('A. Weight Dynamics: Material Gating Effect', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    
    # Panel B: Material state trajectory
    ax2 = fig.add_subplot(gs[1, :])
    ax2.plot(t, phase1['eta'], linewidth=2.5, color='#27ae60')
    ax2.axhline(y=0.5, color='#e74c3c', linestyle='--', label='Threshold', alpha=0.7)
    ax2.fill_between(t, 0, 1, where=np.array(phase1['eta']) > 0.5, 
                     alpha=0.2, color='#e74c3c', label='Gating active')
    ax2.set_xlabel('Time (s)', fontsize=12)
    ax2.set_ylabel('Material State (η)', fontsize=12)
    ax2.set_title('B. Condensate Material State', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    # Panel C: Phase portrait
    ax3 = fig.add_subplot(gs[2, 0])
    # Generate synthetic phase portrait data
    eta_range = np.linspace(0, 1, 20)
    E_range = np.linspace(0, 1, 20)
    ETA, E = np.meshgrid(eta_range, E_range)
    
    # Vector field
    dE = -E / 1.0 + 0.1  # Simplified dynamics
    deta = (0.5 - ETA) / 120.0 + 0.01
    
    ax3.quiver(ETA[::2, ::2], E[::2, ::2], deta[::2, ::2], dE[::2, ::2], 
               alpha=0.6, width=0.003)
    ax3.plot(phase1['eta'][:50], np.linspace(0, 1, 50), 'r-', linewidth=2, 
             label='Trajectory')
    ax3.axvline(x=0.5, color='k', linestyle='--', alpha=0.5)
    ax3.set_xlabel('Material State (η)', fontsize=12)
    ax3.set_ylabel('Eligibility (E)', fontsize=12)
    ax3.set_title('C. Phase Portrait', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # Panel D: Gating function
    ax4 = fig.add_subplot(gs[2, 1])
    eta_vals = np.linspace(0, 1, 100)
    gate_vals = 1 / (1 + np.exp(10 * (eta_vals - 0.5)))
    ax4.plot(eta_vals, gate_vals, linewidth=3, color='#9b59b6')
    ax4.axvline(x=0.5, color='k', linestyle='--', alpha=0.5, label='Threshold')
    ax4.fill_between(eta_vals, 0, gate_vals, alpha=0.3, color='#9b59b6')
    ax4.set_xlabel('Material State (η)', fontsize=12)
    ax4.set_ylabel('Gate Value', fontsize=12)
    ax4.set_title('D. Material Gating Function', fontsize=14, fontweight='bold')
    ax4.legend(fontsize=11)
    ax4.grid(True, alpha=0.3)
    
    plt.suptitle('Figure 1: Material Eligibility ODE Model', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def create_fig2_spiking_comparison(results: Dict, save_path: Path) -> None:
    """Figure 2: Spiking network comparison between 3-factor and 4-factor learning."""
    phase2 = results['phase2']
    
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)
    
    # Panel A: Learning curves
    ax1 = fig.add_subplot(gs[0, :])
    trials = np.arange(len(phase2['learning_curve_3factor']))
    ax1.plot(trials, phase2['learning_curve_3factor'], label='3-factor', 
             linewidth=2.5, color='#3498db', marker='o', markersize=4, alpha=0.8)
    ax1.plot(trials, phase2['learning_curve_4factor'], label='4-factor', 
             linewidth=2.5, color='#e74c3c', marker='s', markersize=4, alpha=0.8)
    ax1.set_xlabel('Trial', fontsize=12)
    ax1.set_ylabel('Performance', fontsize=12)
    ax1.set_title(f'A. Learning Curves (p = {phase2["learning_curve_difference_p"]:.4f})', 
                  fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    
    # Panel B: Weight trajectories
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(trials, phase2['weight_trajectory_3factor'], label='3-factor', 
             linewidth=2.5, color='#3498db', alpha=0.8)
    ax2.plot(trials, phase2['weight_trajectory_4factor'], label='4-factor', 
             linewidth=2.5, color='#e74c3c', alpha=0.8)
    ax2.set_xlabel('Trial', fontsize=12)
    ax2.set_ylabel('Mean Weight', fontsize=12)
    ax2.set_title('B. Weight Evolution', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    # Panel C: Eta trajectory (4-factor only)
    if phase2.get('eta_trajectory'):
        ax3 = fig.add_subplot(gs[1, 1])
        ax3.plot(trials[:len(phase2['eta_trajectory'])], phase2['eta_trajectory'], 
                 linewidth=2.5, color='#27ae60')
        ax3.axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='Threshold')
        ax3.set_xlabel('Trial', fontsize=12)
        ax3.set_ylabel('Material State (η)', fontsize=12)
        ax3.set_title('C. Material State Evolution', fontsize=14, fontweight='bold')
        ax3.legend(fontsize=11)
        ax3.grid(True, alpha=0.3)
    
    # Panel D: Raster plot (if spike data available)
    if 'spike_data' in phase2:
        ax4 = fig.add_subplot(gs[2, :])
        spike_data = phase2['spike_data']
        
        # Plot input spikes (subset)
        input_mask = np.array(spike_data['spike_indices_input']) < 20
        ax4.scatter(np.array(spike_data['spike_times_input'])[input_mask], 
                   np.array(spike_data['spike_indices_input'])[input_mask],
                   s=1, c='blue', alpha=0.5, label='Input')
        
        # Plot output spikes
        output_times = np.array(spike_data['spike_times_output'])
        output_indices = np.array(spike_data['spike_indices_output']) + 25
        ax4.scatter(output_times[output_times < 5], 
                   output_indices[output_times < 5],
                   s=2, c='red', alpha=0.7, label='Output')
        
        ax4.set_xlabel('Time (s)', fontsize=12)
        ax4.set_ylabel('Neuron Index', fontsize=12)
        ax4.set_title('D. Network Activity (First 5 seconds)', fontsize=14, fontweight='bold')
        ax4.set_xlim(0, 5)
        ax4.legend(fontsize=11)
    
    plt.suptitle('Figure 2: Spiking Network Learning Comparison', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def create_fig3_history_dependence(results: Dict, save_path: Path) -> None:
    """Figure 3: History-dependent plasticity outcomes."""
    phase2 = results['phase2']
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Panel A: Different initial conditions
    ax1 = axes[0, 0]
    if 'history_conditions' in phase2:
        conditions = phase2['history_conditions']
        initial_etas = [c['initial_eta'] for c in conditions]
        weight_changes = [c['weight_change'] for c in conditions]
        
        bars = ax1.bar(range(len(conditions)), weight_changes, 
                       color=['#3498db', '#e74c3c'])
        ax1.set_xticks(range(len(conditions)))
        ax1.set_xticklabels([f'η₀={eta:.1f}' for eta in initial_etas])
        ax1.set_ylabel('Weight Change', fontsize=12)
        ax1.set_title(f'A. History Effect (size = {phase2["history_effect_size"]:.2f})', 
                     fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')
    
    # Panel B: Conceptual illustration
    ax2 = axes[0, 1]
    t = np.linspace(0, 10, 1000)
    
    # Same input pattern
    input_pattern = np.zeros_like(t)
    input_pattern[(t > 2) & (t < 3)] = 1
    input_pattern[(t > 5) & (t < 6)] = 1
    input_pattern[(t > 8) & (t < 9)] = 1
    
    ax2.fill_between(t, 0, input_pattern, alpha=0.3, color='gray', label='Input')
    
    # Different outputs based on eta
    output1 = input_pattern * np.exp(-0.5 * (t - 2))
    output2 = input_pattern * np.exp(-0.2 * (t - 2))
    
    ax2.plot(t, output1 + 1.5, label='Low η₀', linewidth=2, color='#3498db')
    ax2.plot(t, output2 + 0.5, label='High η₀', linewidth=2, color='#e74c3c')
    
    ax2.set_xlabel('Time', fontsize=12)
    ax2.set_ylabel('Response', fontsize=12)
    ax2.set_title('B. Same Input, Different Outcomes', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.set_ylim(-0.1, 3)
    
    # Panel C: State space view
    ax3 = axes[1, 0]
    # Create synthetic trajectories
    theta = np.linspace(0, 4*np.pi, 200)
    
    # Trajectory 1 (low initial eta)
    r1 = 0.3 + 0.2 * np.exp(-theta/10)
    x1 = r1 * np.cos(theta) + 0.3
    y1 = r1 * np.sin(theta) + 0.3
    
    # Trajectory 2 (high initial eta)
    r2 = 0.5 + 0.1 * np.exp(-theta/10)
    x2 = r2 * np.cos(theta) + 0.7
    y2 = r2 * np.sin(theta) + 0.7
    
    ax3.plot(x1, y1, linewidth=2, color='#3498db', label='Low η₀')
    ax3.plot(x2, y2, linewidth=2, color='#e74c3c', label='High η₀')
    
    # Add start/end markers
    ax3.scatter([x1[0], x2[0]], [y1[0], y2[0]], s=100, c='green', 
                marker='o', label='Start', zorder=5)
    ax3.scatter([x1[-1], x2[-1]], [y1[-1], y2[-1]], s=100, c='red', 
                marker='s', label='End', zorder=5)
    
    ax3.set_xlabel('Weight', fontsize=12)
    ax3.set_ylabel('Material State (η)', fontsize=12)
    ax3.set_title('C. State Space Trajectories', fontsize=14, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(-0.1, 1.1)
    ax3.set_ylim(-0.1, 1.1)
    
    # Panel D: Memory effect
    ax4 = axes[1, 1]
    memory_times = np.array([1, 5, 10, 30, 60, 120, 300])  # seconds
    memory_effect = np.exp(-memory_times / 120)  # Decay with material time constant
    
    ax4.semilogx(memory_times, memory_effect, 'o-', linewidth=2.5, 
                 markersize=8, color='#9b59b6')
    ax4.set_xlabel('Time Since Perturbation (s)', fontsize=12)
    ax4.set_ylabel('Memory Strength', fontsize=12)
    ax4.set_title('D. Material State Memory', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3, which='both')
    ax4.set_ylim(0, 1.1)
    
    plt.suptitle('Figure 3: History-Dependent Plasticity', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def create_fig4_vesicle_pools(results: Dict, save_path: Path) -> None:
    """Figure 4: Vesicle pool dynamics with condensate coupling."""
    phase3 = results['phase3']
    
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)
    
    # Panel A: PPR vs eta
    ax1 = fig.add_subplot(gs[0, :])
    eta_dep = phase3['eta_dependence']
    ax1.plot(eta_dep['eta_values'], eta_dep['ppr_50ms_values'], 
             'o-', linewidth=2.5, markersize=8, color='#e74c3c')
    ax1.set_xlabel('Material State (η)', fontsize=12)
    ax1.set_ylabel('Paired-Pulse Ratio (50ms)', fontsize=12)
    ax1.set_title(f'A. PPR-η Correlation (r = {eta_dep["ppr_eta_correlation"]:.3f}, p = {eta_dep["ppr_eta_correlation_p"]:.4f})', 
                  fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Panel B: PPR heatmap
    ax2 = fig.add_subplot(gs[1, 0])
    ppr_matrix = np.array(eta_dep['ppr_matrix'])
    im = ax2.imshow(ppr_matrix, aspect='auto', cmap='coolwarm', origin='lower')
    ax2.set_xlabel('Inter-pulse Interval (ms)', fontsize=12)
    ax2.set_ylabel('Material State (η)', fontsize=12)
    ax2.set_title('B. PPR Dependence Map', fontsize=14, fontweight='bold')
    ax2.set_xticks(range(len(eta_dep['intervals_ms'])))
    ax2.set_xticklabels([f'{int(i)}' for i in eta_dep['intervals_ms']])
    ax2.set_yticks(range(0, len(eta_dep['eta_values']), 2))
    ax2.set_yticklabels([f'{eta:.1f}' for eta in eta_dep['eta_values'][::2]])
    plt.colorbar(im, ax=ax2, label='PPR')
    
    # Panel C: Release probability modulation
    ax3 = fig.add_subplot(gs[1, 1])
    pr_matrix = np.array(eta_dep['pr_matrix'])
    for i, freq in enumerate(eta_dep['frequencies_Hz']):
        ax3.plot(eta_dep['eta_values'], pr_matrix[:, i], 
                'o-', label=f'{freq} Hz', linewidth=2, markersize=6)
    ax3.set_xlabel('Material State (η)', fontsize=12)
    ax3.set_ylabel('Release Probability', fontsize=12)
    ax3.set_title(f'C. PR Modulation (range = {eta_dep["pr_modulation_range"]:.2f})', 
                  fontsize=14, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)
    
    # Panel D & E: STP protocols
    stp = phase3['stp_protocols']
    
    ax4 = fig.add_subplot(gs[2, 0])
    if 'low_eta' in stp:
        low_data = stp['low_eta']
        ax4.plot(low_data['pulse_numbers'], low_data['normalized_amplitudes'], 
                'o-', linewidth=2.5, markersize=8, color='#3498db',
                label=f'Low η ({low_data["eta"]}) - {low_data["stp_type"]}')
    
    if 'high_eta' in stp:
        high_data = stp['high_eta']
        ax4.plot(high_data['pulse_numbers'], high_data['normalized_amplitudes'], 
                's-', linewidth=2.5, markersize=8, color='#e74c3c',
                label=f'High η ({high_data["eta"]}) - {high_data["stp_type"]}')
    
    ax4.axhline(y=1, color='k', linestyle='--', alpha=0.3)
    ax4.set_xlabel('Pulse Number', fontsize=12)
    ax4.set_ylabel('Normalized Amplitude', fontsize=12)
    ax4.set_title('D. Short-Term Plasticity', fontsize=14, fontweight='bold')
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3)
    
    # Panel E: Dynamic eta effect
    ax5 = fig.add_subplot(gs[2, 1])
    if 'dynamic_eta' in phase3:
        dyn = phase3['dynamic_eta']
        mod_idx = np.array(dyn['modulation_index'])
        pulse_times = np.array(dyn['pulse_times'])
        
        # Show modulation over time
        ax5.plot(pulse_times, mod_idx, linewidth=2, color='#9b59b6')
        
        # Highlight activity periods
        for period in dyn['activity_periods']:
            ax5.axvspan(period[0], period[1], alpha=0.2, color='gray', label='Activity')
        
        ax5.set_xlabel('Time (s)', fontsize=12)
        ax5.set_ylabel('Release Modulation', fontsize=12)
        ax5.set_title(f'E. Activity-Dependent Modulation (max = {dyn["max_modulation"]:.2f})', 
                     fontsize=14, fontweight='bold')
        ax5.grid(True, alpha=0.3)
        
        # Remove duplicate labels in legend
        handles, labels = ax5.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax5.legend(by_label.values(), by_label.keys(), fontsize=10)
    
    plt.suptitle('Figure 4: Vesicle Pool Dynamics with Condensate Coupling', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def create_fig5_summary(results: Dict, save_path: Path) -> None:
    """Figure 5: Integrated summary figure."""
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(3, 3, figure=fig, hspace=0.4, wspace=0.3)
    
    # Panel A: Schematic
    ax1 = fig.add_subplot(gs[0, :])
    ax1.text(0.5, 0.9, 'Four-Factor Learning Rule', fontsize=16, 
             ha='center', transform=ax1.transAxes, fontweight='bold')
    
    # Draw schematic boxes
    boxes = [
        mpatches.FancyBboxPatch((0.05, 0.3), 0.15, 0.4, 
                                boxstyle="round,pad=0.05", 
                                facecolor='#3498db', alpha=0.7),
        mpatches.FancyBboxPatch((0.25, 0.3), 0.15, 0.4, 
                                boxstyle="round,pad=0.05", 
                                facecolor='#e74c3c', alpha=0.7),
        mpatches.FancyBboxPatch((0.45, 0.3), 0.15, 0.4, 
                                boxstyle="round,pad=0.05", 
                                facecolor='#f39c12', alpha=0.7),
        mpatches.FancyBboxPatch((0.65, 0.3), 0.15, 0.4, 
                                boxstyle="round,pad=0.05", 
                                facecolor='#27ae60', alpha=0.7),
    ]
    
    for box in boxes:
        ax1.add_patch(box)
    
    # Add labels
    labels = ['Pre/Post\nActivity', 'Eligibility\nTrace (E)', 'Reward\n(R)', 'Material\nGate g(η)']
    positions = [0.125, 0.325, 0.525, 0.725]
    
    for pos, label in zip(positions, labels):
        ax1.text(pos, 0.5, label, ha='center', va='center', 
                transform=ax1.transAxes, fontsize=11, fontweight='bold')
    
    # Add arrows
    arrow_props = dict(arrowstyle='->', lw=2, color='black')
    ax1.annotate('', xy=(0.21, 0.5), xytext=(0.19, 0.5),
                transform=ax1.transAxes, arrowprops=arrow_props)
    ax1.annotate('', xy=(0.41, 0.5), xytext=(0.39, 0.5),
                transform=ax1.transAxes, arrowprops=arrow_props)
    ax1.annotate('', xy=(0.61, 0.5), xytext=(0.59, 0.5),
                transform=ax1.transAxes, arrowprops=arrow_props)
    
    # Add equation
    ax1.text(0.85, 0.5, '→ Δw', ha='center', va='center',
            transform=ax1.transAxes, fontsize=14, fontweight='bold')
    
    ax1.text(0.5, 0.1, 'Δw = E × R × g(η),  where g(η) = 1/(1 + exp(k(η - θ)))',
            ha='center', transform=ax1.transAxes, fontsize=12, 
            style='italic', bbox=dict(boxstyle="round,pad=0.3", 
                                     facecolor='lightgray', alpha=0.5))
    
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.axis('off')
    ax1.set_title('A. Four-Factor Learning Architecture', fontsize=14, fontweight='bold', pad=20)
    
    # Panel B: Key results summary
    ax2 = fig.add_subplot(gs[1, :2])
    
    # Create summary metrics
    phase1 = results['phase1']
    phase2 = results['phase2']
    phase3 = results['phase3']
    
    metrics = {
        'ODE Dynamics\nDifference': phase1['dynamics_difference'],
        'Learning Curve\nDifference (p)': phase2['learning_curve_difference_p'],
        'History Effect\nSize': phase2['history_effect_size'],
        'PPR-η\nCorrelation': phase3['eta_dependence']['ppr_eta_correlation'],
        'PR Modulation\nRange': phase3['pr_modulation_range']
    }
    
    x_pos = np.arange(len(metrics))
    values = list(metrics.values())
    colors = ['#e74c3c' if i % 2 == 0 else '#3498db' for i in range(len(metrics))]
    
    bars = ax2.bar(x_pos, values, color=colors, alpha=0.7)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(list(metrics.keys()), rotation=45, ha='right')
    ax2.set_ylabel('Value', fontsize=12)
    ax2.set_title('B. Key Metrics Summary', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{val:.3f}', ha='center', va='bottom', fontsize=10)
    
    # Panel C: Time scales
    ax3 = fig.add_subplot(gs[1, 2])
    
    time_scales = {
        'Eligibility\n(E)': 1,  # seconds
        'Material State\n(η)': 120,  # seconds
        'Plasticity\nConsolidation': 600,  # seconds
    }
    
    y_pos = np.arange(len(time_scales))
    times = list(time_scales.values())
    
    ax3.barh(y_pos, np.log10(times), color=['#3498db', '#27ae60', '#9b59b6'], alpha=0.7)
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(list(time_scales.keys()))
    ax3.set_xlabel('Time Scale (log₁₀ seconds)', fontsize=12)
    ax3.set_title('C. Time Scales', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='x')
    
    # Add actual time labels
    for i, (y, time) in enumerate(zip(y_pos, times)):
        ax3.text(np.log10(time) + 0.1, y, f'{time}s', 
                va='center', fontsize=10)
    
    # Panel D: Predictions
    ax4 = fig.add_subplot(gs[2, :])
    
    predictions_text = """Key Predictions from Material Eligibility Model:

1. History-Dependent Learning: The same input pattern produces different plasticity outcomes 
   depending on the prior condensate material state (η)

2. Gated Plasticity Window: Synaptic weight changes are suppressed when η exceeds threshold,
   creating state-dependent learning windows

3. Vesicle Pool Coupling: Condensate state modulates vesicle mobilization rates, leading to
   η-dependent paired-pulse ratios and short-term plasticity patterns

4. Multi-timescale Dynamics: Fast eligibility traces (seconds) interact with slow material
   states (minutes) to create complex temporal filtering of plasticity signals

5. Activity-Dependent Regulation: High synaptic activity increases condensate levels,
   creating negative feedback that prevents runaway potentiation"""
    
    ax4.text(0.05, 0.95, predictions_text, transform=ax4.transAxes, 
             fontsize=11, va='top', ha='left',
             bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.3))
    ax4.axis('off')
    ax4.set_title('D. Model Predictions', fontsize=14, fontweight='bold', pad=20)
    
    plt.suptitle('Figure 5: Summary of Material Eligibility Modeling Results', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def generate_all_figures(figures_dir: Path) -> Dict:
    """Generate all required figures."""
    print("\nGenerating figures...")
    
    # Load results from previous phases
    results = load_results()
    
    # Generate each figure
    figures_generated = []
    
    try:
        create_fig1_ode_dynamics(results, figures_dir / "fig1_ode_dynamics.pdf")
        figures_generated.append("fig1_ode_dynamics.pdf")
        print("  ✓ Figure 1: ODE dynamics")
    except Exception as e:
        print(f"  ✗ Figure 1 failed: {e}")
    
    try:
        create_fig2_spiking_comparison(results, figures_dir / "fig2_spiking_comparison.pdf")
        figures_generated.append("fig2_spiking_comparison.pdf")
        print("  ✓ Figure 2: Spiking comparison")
    except Exception as e:
        print(f"  ✗ Figure 2 failed: {e}")
    
    try:
        create_fig3_history_dependence(results, figures_dir / "fig3_history_dependence.pdf")
        figures_generated.append("fig3_history_dependence.pdf")
        print("  ✓ Figure 3: History dependence")
    except Exception as e:
        print(f"  ✗ Figure 3 failed: {e}")
    
    try:
        create_fig4_vesicle_pools(results, figures_dir / "fig4_vesicle_pools.pdf")
        figures_generated.append("fig4_vesicle_pools.pdf")
        print("  ✓ Figure 4: Vesicle pools")
    except Exception as e:
        print(f"  ✗ Figure 4 failed: {e}")
    
    try:
        create_fig5_summary(results, figures_dir / "fig5_summary.pdf")
        figures_generated.append("fig5_summary.pdf")
        print("  ✓ Figure 5: Summary")
    except Exception as e:
        print(f"  ✗ Figure 5 failed: {e}")
    
    return {
        'figures_generated': figures_generated,
        'figure_count': len(figures_generated),
        'status': 'pass' if len(figures_generated) >= 5 else 'fail'
    }


if __name__ == "__main__":
    figures_dir = Path("../../figures")
    figures_dir.mkdir(exist_ok=True)
    
    results = generate_all_figures(figures_dir)
    
    # Save results
    base_dir = Path(__file__).parent.parent
    output_path = base_dir / "phase4_figures.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nGenerated {results['figure_count']} figures")
    print(f"Status: {results['status']}")