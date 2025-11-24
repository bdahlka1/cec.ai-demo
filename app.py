import streamlit as st
import PyPDF2
import re
import openpyxl
from datetime import datetime
import io
from copy import copy
from openpyxl.styles import Alignment

st.set_page_config(page_title="CEC Bid Go/No-Go", layout="centered")

st.title("CEC Controls – Water Bid Go/No-Go Analyzer")
st.caption("Branch Manager Michigan • Internal Tool")

# Load calibration rules
@st.cache_data
def load_calibration():
    wb = openpyxl.load_workbook("Bid_Scoring_Calibration.xlsx")
    ws = wb.active
    rules = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0]:
            rules[int(row[0])] = {
                "max": row[2] or 0,
                "pos_kw": [k.strip() for k in (row[3] or "").split(",") if k.strip()],
                "neg_kw": [k.strip() for k in (row[4] or "").split(",") if k.strip()],
                "pos_pts": row[5] or row[2],
                "neg_pts": row[6] or 0
            }
    return rules

rules = load_calibration()

# Load template for styling
@st.cache_data
def load_template():
    wb = openpyxl.load_workbook("Water Bid Go_NoGo Weighting Scale.xlsx")
    ws = wb.active
    return wb, ws

template_wb, template_ws = load_template()

col1, col2 = st.columns([3,1])
with col1:
    spec_pdf = st.file_uploader("Upload Specification PDF", type="pdf")
with col2:
    location = st.text_input("Project City, State", "Wauseon, OH")

if spec_pdf and location:
    progress = st.progress(0)

    # Extract all pages
    page_texts = {}
    try:
        reader = PyPDF2.PdfReader(spec_pdf)
        total_pages = len(reader.pages)
        for i in range(total_pages):
            progress.progress((i+1)/total_pages)
            page_texts[i+1] = reader.pages[i].extract_text() or ""
    except Exception as e:
        st.error(f"PDF error: {e}")
        st.stop()

    # Scoring from calibration
    comments = {}
    earned = {}
    total = 0
    full_text = " ".join(page_texts.values()).lower()

    for row_num, rule in rules.items():
        hits_pos = any(kw in full_text for kw in rule["pos_kw"])
        hits_neg = any(kw in full_text for kw in rule["neg_kw"])
        points = rule["pos_pts"] if hits_pos and not hits_neg else rule["neg_pts"] if hits_neg else 0
        total += points
        
        # Find exact page and sentence
        hit_page = 0
        hit_sentence = ""
        for p, txt in page_texts.items():
            txt_lower = txt.lower()
            if any(kw in txt_lower for kw in rule["pos_kw"]) or any(kw in txt_lower for kw in rule["neg_kw"]):
                hit_page = p
                for line in txt.split('\n'):
                    if any(kw in line.lower() for kw in rule["pos_kw"] + rule["neg_kw"]):
                        hit_sentence = line.strip()
                        break
                if hit_sentence:
                    break
        
        comment = f"{points} pts"
        if hit_page:
            comment += f" – Page {hit_page}"
            if hit_sentence:
                short = hit_sentence[:120] + ("..." if len(hit_sentence) > 120 else "")
                comment += f": \"{short}\""
        
        comments[row_num] = comment
        earned[row_num] = points

    decision = "GO" if total >= 75 else "NO-GO"

    # Build output with perfect styling + wrap text in G
    out_wb = openpyxl.Workbook()
    ws = out_wb.active
    ws.title = "Go_NoGo_Result"

    # Copy every cell + full styling
    for row in template_ws.iter_rows():
        for cell in row:
            new_cell = ws.cell(row=cell.row, column=cell.column, value=cell.value)
            if cell.has_style:
                new_cell.font = copy(cell.font)
                new_cell.border = copy(cell.border)
                new_cell.fill = copy(cell.fill)
                new_cell.number_format = cell.number_format
                new_cell.protection = copy(cell.protection)
                new_cell.alignment = copy(cell.alignment)
        # Copy row height safely
        rd = template_ws.row_dimensions.get(row[0].row)
        if rd and rd.height is not None:
            ws.row_dimensions[row[0].row].height = rd.height

    # Copy column widths safely
    for col, dim in template_ws.column_dimensions.items():
        if dim.width is not None:
            ws.column_dimensions[col].width = dim.width

    # Write grades and comments to Column G (wrap text)
    for row_num, comment in comments.items():
        ws.cell(row=row_num, column=4, value=earned.get(row_num, 0))  # Grade
        ws.cell(row=row_num, column=6, value=earned.get(row_num, 0))  # Points
        comment_cell = ws.cell(row=row_num, column=7, value=comment)  # Comment in G
        comment_cell.alignment = Alignment(wrap_text=True, vertical="top")

    ws["B35"] = total
    ws["B36"] = decision
    ws["B37"] = location
    ws["B38"] = datetime.now().strftime("%Y-%m-%d")

    buffer = io.BytesIO()
    out_wb.save(buffer)
    buffer.seek(0)

    st.success(f"Analysis complete → {decision} • Score: {total}/100")
    st.download_button(
        label="Download Filled Scorecard",
        data=buffer,
        file_name=f"Water_Bid_Go_NoGo_{spec_pdf.name}_{datetime.now():%Y%m%d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Upload specification PDF and project location")

st.caption("© 2025 CEC Controls – Internal Tool")
