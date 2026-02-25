#!/usr/bin/env python3
import argparse
import datetime as dt
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def sim_ids_for(registry: dict, predicate) -> list[str]:
    sims = []
    for sim_id, entry in registry.get("sims", {}).items():
        if predicate(entry):
            sims.append(sim_id)
    return sorted(sims, key=lambda x: int(x))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build figure manifest")
    parser.add_argument("--analysis-registry", required=True, help="Path to analysis_registry.json")
    parser.add_argument("--fene-summary-json", required=True, help="Path to fene_warning_summary.json")
    parser.add_argument("--output", required=True, help="Output figure manifest JSON")
    args = parser.parse_args()

    registry = load_json(Path(args.analysis_registry))
    fene_summary = load_json(Path(args.fene_summary_json))

    fig2_a4 = sim_ids_for(
        registry,
        lambda e: e.get("stage") == 2 and e.get("arch_a") == 4 and e.get("arch_b") == 20
        and e.get("analysis", {}).get("concentration"),
    )
    fig2_a8 = sim_ids_for(
        registry,
        lambda e: e.get("stage") == 4 and e.get("arch_a") == 8 and e.get("arch_b") == 16
        and e.get("analysis", {}).get("concentration"),
    )

    fig3_t300_e5 = sim_ids_for(
        registry,
        lambda e: e.get("stage") == 3 and e.get("temp") == 300 and e.get("eps") == 5
        and e.get("analysis", {}).get("concentration"),
    )
    fig3_t300_e8 = sim_ids_for(
        registry,
        lambda e: e.get("stage") == 3 and e.get("temp") == 300 and e.get("eps") == 8
        and e.get("analysis", {}).get("concentration"),
    )

    stage5_sims = sim_ids_for(registry, lambda e: e.get("stage") == 5)

    fene_sims = sim_ids_for(
        registry,
        lambda e: e.get("analysis", {}).get("fene", {}).get("relax_warnings", 0)
        + e.get("analysis", {}).get("fene", {}).get("prd_warnings", 0)
        > 0,
    )

    manifest = {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "analysis_registry": "rerun_v2/analysis_registry.json",
        "figures": [
            {
                "figure_id": "Fig2",
                "title": "Phase diagram (A4B20 vs A8B16)",
                "files": [
                    "rerun_v2/figures/fig2_phase_diagram.png",
                    "rerun_v2/figures/fig2_phase_diagram.pdf",
                ],
                "source_sims": {
                    "A4B20_stage2": fig2_a4,
                    "A8B16_stage4": fig2_a8,
                },
                "analysis_source": "analysis_registry.json: concentration K",
                "manuscript_location": "Results 2.1 (Figure 2)",
            },
            {
                "figure_id": "Fig3",
                "title": "Valency comparison (Stage 3)",
                "files": [
                    "rerun_v2/figures/fig3_valency_comparison.png",
                    "rerun_v2/figures/fig3_valency_comparison.pdf",
                ],
                "source_sims": {
                    "T300_eps5": fig3_t300_e5,
                    "T300_eps8": fig3_t300_e8,
                },
                "analysis_source": "analysis_registry.json: concentration K",
                "manuscript_location": "Results 2.2 (Figure 3)",
            },
            {
                "figure_id": "Fig4",
                "title": "1-1 vs 1-2 interaction comparison (Stage 5)",
                "files": [
                    "rerun_v2/figures/fig4_interaction_comparison.png",
                    "rerun_v2/figures/fig4_interaction_comparison.pdf",
                ],
                "source_sims": {
                    "stage5_expected": stage5_sims,
                },
                "analysis_source": "analysis_registry.json (stage5 missing trajectories)",
                "manuscript_location": "Results 2.3 (Figure 4)",
                "notes": "Figure is a placeholder because Stage 5 trajectories are missing from results/",
            },
            {
                "figure_id": "FigS2",
                "title": "FENE warning distribution",
                "files": [
                    "rerun_v2/figures/figS2_fene_warnings.png",
                    "rerun_v2/figures/figS2_fene_warnings.pdf",
                ],
                "source_sims": {
                    "warnings_detected": fene_sims,
                },
                "analysis_source": "fene_warning_summary.json",
                "manuscript_location": "Supplementary S1.6 (Figure S2)",
                "notes": f"sims_with_warnings={fene_summary.get('sims_with_warnings')}",
            },
        ],
    }

    write_json(Path(args.output), manifest)


if __name__ == "__main__":
    main()
