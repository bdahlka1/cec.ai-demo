"""
Evaluate the scoring model against historical RFP + scorecard pairs.

This script:
  - loads mapping.csv
  - loads each historical XLSX scorecard (ground truth)
  - processes the corresponding RFP PDF(s)
  - runs your scoring model (you will plug in your rules)
  - compares predicted scores to human-entered scores
  - prints accuracy + per-criterion error
"""

import csv
from pathlib import Path
from parse_scorecard import load_scorecard, CRITERIA

# -------- Modify this path if needed --------
DATA_DIR = Path(__file__).resolve().parent / "data"
RFP_DIR = DATA_DIR / "rfps"
SCORECARD_DIR = DATA_DIR / "scorecards"
MAPPING_FILE = DATA_DIR / "mapping.csv"
# --------------------------------------------

def score_rfp_files(pdf_paths):
    """
    This function SHOULD call your existing scoring logic.

    You will:
      1. import your scoring routine from app.py or another file
      2. pass the PDF paths to it
      3. return a dict matching this format:

        {
          "total": 78,
          "earned": { row_number: points },
          "comments": { row_number: "..." },
        }

    For now, this function is a placeholder that MUST BE UPDATED by you.
    """
    raise NotImplementedError(
        "TODO: Connect your actual scoring logic to this function."
    )


def main():
    if not MAPPING_FILE.exists():
        raise FileNotFoundError(f"Mapping file not found: {MAPPING_FILE}")

    with open(MAPPING_FILE, "r", newline="", encoding="utf-8") as f:
        mapping = list(csv.DictReader(f))

    total_abs_error = 0
    project_count = 0
    per_criterion_errors = { name: [] for name in CRITERIA.values() }

    print("\n=== Running Model Evaluation on Historical Projects ===\n")

    for item in mapping:
        project_name = item["project_name"]
        scorecard_file = item["scorecard_file"]
        rfp_files = [x.strip() for x in item["rfp_files"].split("|")]

        # Resolve paths
        scorecard_path = SCORECARD_DIR / scorecard_file
        rfp_paths = [str(RFP_DIR / name) for name in rfp_files]

        print(f"\n--- Project: {project_name} ---")
        print(f"Scorecard: {scorecard_file}")
        print(f"RFP PDFs: {rfp_files}")

        # 1. Load ground truth
        truth = load_scorecard(scorecard_path)
        truth_total = truth["total_score"]

        # 2. Run your model prediction
        #    (you will implement score_rfp_files)
        try:
            pred = score_rfp_files(rfp_paths)
        except NotImplementedError:
            print("\n[ERROR] scoring logic not yet connected.\n")
            return

        pred_total = pred["total"]
        diff = pred_total - truth_total

        total_abs_error += abs(diff)
        project_count += 1

        print(f"Human total: {truth_total:.1f}")
        print(f"Model total: {pred_total:.1f}")
        print(f"Difference: {diff:+.1f}")

        # 3. Compare each criterion
        for row, crit_name in CRITERIA.items():
            truth_pts = truth["criteria"][crit_name]["points"]
            pred_pts = pred["earned"].get(row, 0)

            per_criterion_errors[crit_name].append(abs(truth_pts - pred_pts))

    # Summary results
    if project_count > 0:
        avg_error = total_abs_error / project_count
    else:
        avg_error = 0

    print("\n=== Summary ===")
    print(f"Projects evaluated: {project_count}")
    print(f"Average total score error: {avg_error:.2f} points\n")

    print("Per-criterion average absolute error:\n")
    for crit_name, errs in per_criterion_errors.items():
        if errs:
            avg = sum(errs) / len(errs)
            print(f"  {crit_name}: {a_
