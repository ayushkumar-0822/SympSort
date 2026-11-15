"""
SympSort — Entry Point
========================
Run this file to start the Flask development server, or pass ``--cli`` to
print the analysis to the console and save a chart without launching a server.

Usage::

    python main.py          # start web server on port 5000
    python main.py --cli    # CLI mode: print results, save chart, exit
"""

from __future__ import annotations

import argparse
import logging
import socket
import sys

# WSGI application instance export for Vercel / serverless runtimes
from app import app


# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sympsort")


def _find_open_port(start: int = 5000, attempts: int = 20) -> int:
    """Return *start* if available, otherwise scan upward."""
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start  # fallback


def _run_cli() -> None:
    """CLI mode: load data, print analysis, save chart."""
    from analysis import calculate_smoker_charges
    from data_loader import load_dataset
    from visualization import save_default_chart

    logger.info("Running in CLI mode")

    df, _raw, report = load_dataset()
    if not report.is_valid:
        logger.error("Dataset is not valid — aborting.")
        sys.exit(1)

    result = calculate_smoker_charges(df)

    print("\n" + "=" * 60)
    print("  SympSort — Smoker vs Non-Smoker Charge Analysis")
    print("=" * 60)
    print(f"\n  Total valid records : {result.total_valid_records:,}")
    print(f"  Smokers             : {result.smoker_count:,}")
    print(f"  Non-smokers         : {result.non_smoker_count:,}")
    print(f"\n  Smoker mean charge  : ${result.smoker_mean:>12,.2f}")
    print(f"  Non-smoker mean     : ${result.non_smoker_mean:>12,.2f}")
    print(f"  Difference          : ${result.absolute_difference:>12,.2f}")
    print(f"  Multiplier          : {result.multiplier:.2f}×")
    print(f"\n  {result.dynamic_statement}")
    print("\n  Groupby output:")
    print(f"  {result.groupby_text}")
    print("=" * 60 + "\n")

    chart_path = save_default_chart(result.df_grouped)
    if chart_path:
        print(f"  Chart saved → {chart_path}\n")


def _run_server() -> None:
    """Start the Flask development server."""
    from config import DEFAULT_PORT

    port = _find_open_port(DEFAULT_PORT)
    logger.info("Starting SympSort web server …")

    from app import app

    print("\n" + "=" * 60)
    print("  SympSort — Medical Cost & Lifestyle Factors")
    print("=" * 60)
    print(f"\n  🌐  http://127.0.0.1:{port}")
    print("  Press Ctrl+C to stop.\n")

    app.run(host="127.0.0.1", port=port, debug=False)


def main() -> None:
    """Parse arguments and dispatch."""
    parser = argparse.ArgumentParser(
        description="SympSort — Medical Cost & Lifestyle Factors Analysis",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in CLI mode (print analysis, save chart, then exit).",
    )
    args = parser.parse_args()

    if args.cli:
        _run_cli()
    else:
        _run_server()


if __name__ == "__main__":
    main()
