#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import csv


def load_registry(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_k(entry: dict) -> float | None:
    return entry.get("analysis", {}).get("concentration", {}).get("k_mean")


def phase_diagram_data(registry: dict, stage: int, arch_a: int, arch_b: int):
    rows = []
    for entry in registry.get("sims", {}).values():
        if entry.get("stage") != stage:
            continue
        if entry.get("arch_a") != arch_a or entry.get("arch_b") != arch_b:
            continue
        k_val = get_k(entry)
        if k_val is None:
            continue
        rows.append(
            {
                "eps": entry.get("eps"),
                "temp": entry.get("temp"),
                "k": k_val,
                "sim_id": entry.get("sim_id"),
            }
        )
    return rows


def plot_phase_diagram(a4_rows: list, a8_rows: list, output_dir: Path) -> list[str]:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    all_k = [r["k"] for r in a4_rows + a8_rows if r["k"] is not None and r["k"] > 0]
    if all_k:
        log_k = np.log10(all_k)
        vmin, vmax = float(np.min(log_k)), float(np.max(log_k))
    else:
        vmin, vmax = 0, 1

    def scatter_panel(ax, rows, title):
        eps = [r["eps"] for r in rows]
        temp = [r["temp"] for r in rows]
        k_vals = [r["k"] for r in rows]
        colors = np.log10(k_vals)
        sc = ax.scatter(eps, temp, c=colors, cmap="viridis", vmin=vmin, vmax=vmax, s=80)
        ax.set_title(title)
        ax.set_xlabel("epsilon")
        ax.set_ylabel("Temperature (K)")
        ax.set_xticks(sorted(set(eps)))
        ax.set_yticks(sorted(set(temp)))
        ax.grid(True, alpha=0.2)
        return sc

    sc1 = scatter_panel(axes[0], a4_rows, "A4B20 (Stage 2)")
    sc2 = scatter_panel(axes[1], a8_rows, "A8B16 (Stage 4)")

    fig.colorbar(sc2, ax=axes, label="log10(K)")
    fig.suptitle("Phase diagram (partition coefficient K)")

    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / "fig2_phase_diagram.png"
    pdf_path = output_dir / "fig2_phase_diagram.pdf"
    fig.tight_layout()
    fig.savefig(png_path, dpi=200)
    fig.savefig(pdf_path)
    plt.close(fig)
    return [str(png_path), str(pdf_path)]


def plot_valency_comparison(registry: dict, output_dir: Path) -> list[str]:
    arch_order = ["A2B22", "A6B18", "A8B16", "A12B12", "A8B40", "A16B80"]
    conditions = [(300, 5), (300, 8)]
    k_by_arch = {cond: [] for cond in conditions}

    for arch in arch_order:
        arch_a = int(arch.split("B")[0][1:])
        arch_b = int(arch.split("B")[1])
        for cond in conditions:
            temp, eps = cond
            k_val = None
            for entry in registry.get("sims", {}).values():
                if entry.get("stage") != 3:
                    continue
                if entry.get("arch_a") != arch_a or entry.get("arch_b") != arch_b:
                    continue
                if entry.get("temp") != temp or entry.get("eps") != eps:
                    continue
                k_val = get_k(entry)
                break
            k_by_arch[cond].append(k_val if k_val is not None else np.nan)

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(arch_order))
    for cond, marker in zip(conditions, ["o", "s"]):
        label = f"T={cond[0]}K, eps={cond[1]}"
        ax.plot(x, k_by_arch[cond], marker=marker, label=label)

    ax.set_xticks(x)
    ax.set_xticklabels(arch_order)
    ax.set_yscale("log")
    ax.set_ylabel("Partition coefficient K")
    ax.set_title("Valency comparison (Stage 3)")
    ax.grid(True, alpha=0.2)
    ax.legend()

    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / "fig3_valency_comparison.png"
    pdf_path = output_dir / "fig3_valency_comparison.pdf"
    fig.tight_layout()
    fig.savefig(png_path, dpi=200)
    fig.savefig(pdf_path)
    plt.close(fig)
    return [str(png_path), str(pdf_path)]


def plot_interaction_comparison(registry: dict, output_dir: Path) -> list[str]:
    stage5_k = [
        get_k(e) for e in registry.get("sims", {}).values()
        if e.get("stage") == 5 and get_k(e) is not None
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / "fig4_interaction_comparison.png"
    pdf_path = output_dir / "fig4_interaction_comparison.pdf"

    fig, ax = plt.subplots(figsize=(8, 4))
    if not stage5_k:
        ax.text(
            0.5,
            0.5,
            "Stage 5 trajectories missing\nK values unavailable",
            ha="center",
            va="center",
            fontsize=12,
        )
        ax.axis("off")
        ax.set_title("1-1 vs 1-2 interaction comparison (placeholder)")
    else:
        ax.hist(stage5_k, bins=10, color="steelblue", alpha=0.8)
        ax.set_xlabel("Partition coefficient K")
        ax.set_ylabel("Count")
        ax.set_title("Stage 5 K distribution (1-1 attraction)")

    fig.tight_layout()
    fig.savefig(png_path, dpi=200)
    fig.savefig(pdf_path)
    plt.close(fig)
    return [str(png_path), str(pdf_path)]


def plot_fene_warnings(summary_csv: Path, output_dir: Path) -> list[str]:
    warn_rows = []
    with summary_csv.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                relax = int(row.get("relax_warnings", 0))
                prd = int(row.get("prd_warnings", 0))
            except ValueError:
                continue
            if relax + prd > 0:
                warn_rows.append({"sim_id": row.get("sim_id"), "relax": relax, "prd": prd})

    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / "figS2_fene_warnings.png"
    pdf_path = output_dir / "figS2_fene_warnings.pdf"

    fig, ax = plt.subplots(figsize=(10, 4))
    if not warn_rows:
        ax.text(0.5, 0.5, "No FENE warnings detected", ha="center", va="center")
        ax.axis("off")
        ax.set_title("FENE warnings (S5)")
    else:
        sim_ids = [row["sim_id"] for row in warn_rows]
        relax = [row["relax"] for row in warn_rows]
        prd = [row["prd"] for row in warn_rows]
        x = np.arange(len(sim_ids))
        ax.bar(x, relax, label="Relax warnings")
        ax.bar(x, prd, bottom=relax, label="Production warnings")
        ax.set_xticks(x)
        ax.set_xticklabels(sim_ids, rotation=45)
        ax.set_ylabel("Warning count")
        ax.set_title("FENE warnings by sim (S5)")
        ax.legend()
        ax.grid(True, axis="y", alpha=0.2)

    fig.tight_layout()
    fig.savefig(png_path, dpi=200)
    fig.savefig(pdf_path)
    plt.close(fig)
    return [str(png_path), str(pdf_path)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate canonical figures")
    parser.add_argument("--analysis-registry", required=True, help="Path to analysis_registry.json")
    parser.add_argument("--fene-summary-csv", required=True, help="Path to fene_warning_summary.csv")
    parser.add_argument("--output-dir", required=True, help="Output directory for figures")
    args = parser.parse_args()

    registry = load_registry(Path(args.analysis_registry))
    output_dir = Path(args.output_dir)

    a4_rows = phase_diagram_data(registry, stage=2, arch_a=4, arch_b=20)
    a8_rows = phase_diagram_data(registry, stage=4, arch_a=8, arch_b=16)

    plot_phase_diagram(a4_rows, a8_rows, output_dir)
    plot_valency_comparison(registry, output_dir)
    plot_interaction_comparison(registry, output_dir)
    plot_fene_warnings(Path(args.fene_summary_csv), output_dir)


if __name__ == "__main__":
    main()
