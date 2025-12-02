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
import PyPDF2
import re

# -------- Modify this path if needed --------
DATA_DIR = Path(__file__).resolve().parent / "data"
RFP_DIR = DATA_DIR / "rfps"
SCORECARD_DIR = DATA_DIR / "scorecards"
MAPPING_FILE = DATA_DIR / "mapping.csv"
# --------------------------------------------

def score_rfp_files(pdf_paths):
    """
    Pure-Python version of your scoring logic, adapted from app.py.

    pdf_paths: list of file paths (strings) to one or more PDFs that
               together represent a single RFP (spec + addenda, etc.)

    Returns:
      {
        "total": <total score>,
        "earned": { row_number: points },
        "comments": { row_number: comment_text },
      }
    """

    # 1) Read all PDFs and build full text + page-wise text like your app does
    page_texts = {}
    full_text = ""
    page_index = 1

    for pdf_path in pdf_paths:
        reader = PyPDF2.PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            page_texts[page_index] = txt
            full_text += txt + "\n"
            page_index += 1

    # 2) Helper to search pages and assign score (copied from your app style)
    comments = {}
    earned = {}

    def grade(row, max_pts, keywords, positive, negative):
        hits = []
        for kw in keywords:
            for p, txt in page_texts.items():
                if kw.lower() in txt.lower():
                    # pick a line containing the keyword
                    sentence = next(
                        (s.strip() for s in txt.split('\n') if kw.lower() in s.lower()),
                        txt[:300]
                    )
                    hits.append((p, sentence))
                    break
        points = max_pts if hits else 0
        if hits:
            page, sentence = hits[0]
            comment = f"{points} pts – {positive} (Page {page})"
        else:
            comment = f"0 pts – {negative}"

        comments[row] = comment
        earned[row] = points
        return points

    # 3) Apply the same scoring rules as your Streamlit app
    total = 0
    total += grade(6, 10, ["cec", "cec controls"], "CEC listed as approved integrator", "Not listed as approved integrator")
    total += grade(7, 5, ["bid list", "prequalified", "invited bidders"], "Clear bidder list exists", "Bidder list unclear")
    total += grade(8, 10, ["cec"], "<3 integrators named", ">5 integrators or open bidding")
    total += grade(9, 5, ["preferred gc", "direct municipal"], "Preferred relationship", "Not preferred")
    total += grade(11, 5, ["scada", "hmi", "software platform"], "SCADA system clearly defined", "SCADA requirements vague")
    total += grade(12, 10, ["rockwell", "allen-bradley", "siemens"], "Preferred PLC brand", "Non-preferred or packaged PLC")
    total += grade(13, 10, ["vtscada", "ignition", "wonderware", "factorytalk"], "Preferred SCADA brand", "Non-preferred SCADA")
    total += grade(14, 10, ["instrument list", "schedule of values"], "Instrumentation clearly defined", "Instrumentation vague or high-risk")
    total += grade(15, 5, ["schedule", "milestone", "gantt"], "Schedule realistic", "Schedule missing or unrealistic")
    total += grade(22, 5, ["wauseon", "fulton", "ohio"], "Within target geography", "Outside primary geography")
    total += grade(23, 5, ["bid due"], "Bid timing appropriate", "Bid timing rushed")
    total += grade(24, 5, [], "Strategic value present", "Low strategic value")
    total += grade(25, 5, ["liquidated damages"], "No liquidated damages", "Liquidated damages present")
    total += grade(26, 5, ["design-build", "design build"], "Construction only", "Design-Build")
    total += grade(27, 5, ["installation", "field wiring"], "Installation by others", "CEC to perform installation")

    return {
        "total": total,
        "earned": earned,
        "comments": comments,
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
