"""AI Investment Mentor - Entry Point.

Usage:
    python src/main.py                    # Print project info
    python src/main.py --run-morning-report  # Run daily analysis pipeline
"""

import argparse
import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def main():
    parser = argparse.ArgumentParser(description="AI Investment Mentor")
    parser.add_argument(
        "--run-morning-report",
        action="store_true",
        help="Run the daily morning analysis pipeline",
    )
    args = parser.parse_args()

    # Load config (always)
    from config import load_config

    try:
        cfg = load_config()
    except Exception as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    print(f"AI Investment Mentor v0.1.0")
    print(f"Config loaded: model={cfg.llm_model}, db={cfg.db_path}")

    if args.run_morning_report:
        print("Pipeline not yet implemented (Phase 4 Task TBD)")
    else:
        print("Ready. Use --run-morning-report to start daily analysis.")


if __name__ == "__main__":
    main()
