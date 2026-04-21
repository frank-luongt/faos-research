"""RA-6 Pilot Study: Experiment Orchestrator.

Runs the full pipeline: Generate → Assess Coverage → Detect Faults → Analyze.
Supports --dry-run for validation and --phase for running individual phases.
Supports cross-model generation via RA6_GENERATOR_BACKEND env var.

Usage:
  python run_experiment.py                    # Full run (Anthropic)
  python run_experiment.py --dry-run          # Validate harness (no API calls)
  python run_experiment.py --phase generate   # Only generation phase
  python run_experiment.py --phase assess     # Only coverage assessment
  python run_experiment.py --phase fdr        # Only fault detection
  python run_experiment.py --phase analyze    # Only analysis
  python run_experiment.py --output-suffix qwen72b   # Override output suffix

Cross-model:
  RA6_GENERATOR_BACKEND=openrouter python run_experiment.py
  RA6_GENERATOR_BACKEND=google python run_experiment.py
"""

import argparse
import os
import sys
import time

import config


def check_prerequisites():
    """Verify all required files and API keys exist."""
    issues = []

    # Check API keys based on backend
    if not config.ANTHROPIC_API_KEY:
        issues.append("ANTHROPIC_API_KEY not set (required for judge, always)")

    if config.GENERATOR_BACKEND == "openrouter" and not config.OPENROUTER_API_KEY:
        issues.append("OPENROUTER_API_KEY not set (required for openrouter backend)")

    if config.GENERATOR_BACKEND == "google" and not config.GOOGLE_API_KEY:
        issues.append("GOOGLE_API_KEY not set (required for google backend)")

    # Check checklists
    for industry in config.INDUSTRIES:
        path = os.path.join(config.CHECKLISTS_DIR, f"{industry}.json")
        if not os.path.exists(path):
            issues.append(f"Missing checklist: {path}")

    # Check faults
    faults_path = os.path.join(config.FAULTS_DIR, "faults.json")
    if not os.path.exists(faults_path):
        issues.append(f"Missing faults: {faults_path}")

    # Check ontology context
    for industry in config.INDUSTRIES:
        path = os.path.join(config.ONTOLOGY_DIR, f"{industry}.json")
        if not os.path.exists(path):
            issues.append(f"Missing ontology: {path}")

    return issues


def main():
    parser = argparse.ArgumentParser(description="RA-6 Pilot Study Orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="Validate without API calls")
    parser.add_argument("--phase", choices=["generate", "assess", "fdr", "analyze"],
                        help="Run only a specific phase")
    parser.add_argument("--output-suffix", type=str, default=None,
                        help="Override output suffix (e.g. qwen72b, gemma4)")
    args = parser.parse_args()

    # Apply output suffix override
    if args.output_suffix:
        config.OUTPUT_SUFFIX = config._normalize_suffix(args.output_suffix)
        # Recompute suffixed paths
        config.SCENARIOS_FILE = config._suffixed("generated_scenarios", ".json")
        config.COVERAGE_FILE = config._suffixed("coverage_results", ".json")
        config.FDR_FILE = config._suffixed("fdr_results", ".json")
        config.ANALYSIS_FILE = config._suffixed("analysis_summary", ".json")

    # Resolve generator model name for display
    gen_model = {
        "anthropic": config.GENERATOR_MODEL,
        "openrouter": config.OPENROUTER_MODEL,
        "google": config.GOOGLE_MODEL,
    }.get(config.GENERATOR_BACKEND, config.GENERATOR_BACKEND)

    print("=" * 60)
    print("RA-6 PILOT STUDY: Ontology-Powered Scenario Generation")
    print("=" * 60)
    print(f"Generator backend: {config.GENERATOR_BACKEND}")
    print(f"Generator model:   {gen_model}")
    print(f"Judge model:       {config.JUDGE_MODEL} (fixed)")
    print(f"Output suffix:     {config.OUTPUT_SUFFIX or '(none — baseline)'}")
    print(f"Conditions: {config.CONDITIONS}")
    print(f"Industries: {config.INDUSTRIES}")
    print(f"Repetitions: {config.REPETITIONS}")
    print(f"Scenarios/suite: {config.SCENARIOS_PER_SUITE}")
    print(f"Holdout fraction: {config.ONTOLOGY_HOLDOUT_FRACTION}")
    print(f"Dry run: {args.dry_run}")
    print()

    # Prerequisites
    issues = check_prerequisites()
    if issues and not args.dry_run:
        print("PREREQUISITE ISSUES:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)

    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    os.makedirs(config.FIGURES_DIR, exist_ok=True)

    phases = [args.phase] if args.phase else ["generate", "assess", "fdr", "analyze"]
    start_time = time.time()

    if "generate" in phases:
        print("\n" + "=" * 60)
        print("PHASE 1: SCENARIO GENERATION")
        print("=" * 60)
        from generate_scenarios import run_generation
        run_generation(dry_run=args.dry_run)

    if "assess" in phases:
        print("\n" + "=" * 60)
        print("PHASE 2: COVERAGE ASSESSMENT (RC, ISS, AC)")
        print("=" * 60)
        if not os.path.exists(config.SCENARIOS_FILE):
            print("ERROR: No scenarios file. Run --phase generate first.")
            sys.exit(1)
        from assess_coverage import run_assessment
        run_assessment(dry_run=args.dry_run)

    if "fdr" in phases:
        print("\n" + "=" * 60)
        print("PHASE 3: FAULT DETECTION (FDR-design + FDR-execution)")
        print("=" * 60)
        if not os.path.exists(config.SCENARIOS_FILE):
            print("ERROR: No scenarios file. Run --phase generate first.")
            sys.exit(1)
        from detect_faults import run_fault_detection
        run_fault_detection(dry_run=args.dry_run)

    if "analyze" in phases:
        print("\n" + "=" * 60)
        print("PHASE 4: STATISTICAL ANALYSIS")
        print("=" * 60)
        if not os.path.exists(config.COVERAGE_FILE):
            print("ERROR: No coverage results. Run --phase assess first.")
            sys.exit(1)
        from analyze_results import run_analysis
        run_analysis()

    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"COMPLETE. Total time: {elapsed/60:.1f} minutes")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
