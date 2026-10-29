"""Run the full analysis pipeline in order. Usage (from anywhere):

    python src/run_all.py                      # core pipeline
    python src/run_all.py --with-diagnostics   # also run the investigation scripts
"""
import subprocess
import sys
import time
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent  # scripts use relative paths (data/raw, outputs, figures)

REQUIRED_DATA = [
    "olist_order_items_dataset.csv",
    "olist_products_dataset.csv",
    "olist_orders_dataset.csv",
    "product_category_name_translation.csv",
]

CORE = [
    "metrics.py",              # Milestone 3: core metrics
    "monthly.py",              # Milestone 4: monthly trend
    "product_performance.py",  # Milestone 5: categories and products
    "product_recency.py",      # Milestone 5.1: recency (writes outputs/product_recency.csv)
    "charts.py",               # Milestone 6: figures/
]

DIAGNOSTICS = [
    "category_check.py",
    "tail_diagnostic.py",
    "verify_claims.py",
    "recency_baseline.py",     # needs outputs/product_recency.csv, so it runs after recency
]


def main() -> int:
    missing = [f for f in REQUIRED_DATA if not (ROOT / "data" / "raw" / f).exists()]
    if missing:
        print("Missing data files in data/raw/:")
        for f in missing:
            print(f"  - {f}")
        print("Download the Olist dataset from Kaggle (see README).")
        return 1

    steps = list(CORE)
    if "--with-diagnostics" in sys.argv:
        steps = CORE[:4] + DIAGNOSTICS + CORE[4:]

    for i, script in enumerate(steps, 1):
        print(f"\n{'#' * 70}\n# [{i}/{len(steps)}] {script}\n{'#' * 70}", flush=True)
        start = time.time()
        result = subprocess.run([sys.executable, str(SRC / script)], cwd=ROOT)
        if result.returncode != 0:
            print(f"\nFAILED: {script} (exit code {result.returncode}). Stopping.")
            return result.returncode
        print(f"-- {script} finished in {time.time() - start:.1f}s")

    print("\nPipeline complete. Charts are in figures/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())