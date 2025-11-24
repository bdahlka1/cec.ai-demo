import streamlit as st
import PyPDF2
import openpyxl
from datetime import datetime
import io
from copy import copy
from openpyxl.styles import Alignment

st.set_page_config(page_title="CEC Water Bid Intelligence", layout="wide")

# Elegant header
st.markdown("""
<style>
    .title {font-size: 48px; font-weight: 700; color: #003087; text-align: center; margin-bottom: 0px;}
    .subtitle {font-size: 26px; color: #003087; text-align: center; margin-top: -10px; margin-bottom: 30px;}
    .explanation {font-size: 18px; line-height: 1.8; color: #333; background-color: #f8f9fa; padding: 30px; border-radius: 12px; margin: 40px 0;}
    .footer {text-align: center; margin-top: 80px; font-size: 14px; color: #666;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="title">CEC Controls</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-Accelerated Bid Intelligence Engine</p>', unsafe_allow_html=True)

st.markdown("""
<div class="explanation">
<strong>Proprietary Scoring Engine — Built on 20+ Years of Water Controls Expertise</strong><br><br>
This internal system instantly analyzes any municipal water/wastewater specification package and returns a fully populated Go/No-Go scorecard — complete with risk flags, page references, and traceability.<br><br>
The engine reads every page of the RFP, applies CEC’s proven evaluation framework, and delivers a decision in under 30 seconds — eliminating 45+ minutes of manual review per bid.<br><br>
Scoring rules are fully configurable via Bid_Scoring_Calibration.xlsx — allowing leadership to adapt the model to changing market conditions and strategic priorities.
</div>
""", unsafe_allow_html=True)

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

# Load template
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

    comments = {}
    earned = {}
    total = 0
    full_text = " ".join(page_texts.values()).lower()

    for row_num, rule in rules.items():
        hits_pos = any(kw in full_text for kw in rule["pos_kw"])
        hits_neg = any(kw in full_text for kw in rule["neg_kw"])
        points = rule["pos_pts"] if hits_pos and not hits_neg else rule["neg_pts"] if hits_neg else 0
        total += points

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

    # Build perfect output
    out_wb = openpyxl.Workbook()
    ws = out_wb.active
    ws.title = "Go_NoGo_Result"

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
        rd = template_ws.row_dimensions.get(row[0].row)
        if rd and rd.height is not None:
            ws.row_dimensions[row[0].row].height = rd.height

    for col, dim in template_ws.column_dimensions.items():
        if dim.width is not None:
            ws.column_dimensions[col].width = dim.width

    for row_num, comment in comments.items():
        ws.cell(row=row_num, column=4, value=earned.get(row_num, 0))
        ws.cell(row=row_num, column=6, value=earned.get(row_num, 0))
        comment_cell = ws.cell(row=row_num, column=7, value=comment)
        comment_cell.alignment = Alignment(wrap_text=True, vertical="top")

    ws["B35"] = total
    ws["B36"] = decision
    ws["B39"] = location
    ws["B38"] = datetime.now().strftime("%Y-%m-%d")

    buffer = io.BytesIO()
    out_wb.save(buffer)
    buffer.seek(0)

    st.success(f"Analysis complete — {decision} • Score: {total}/100")
    st.download_button(
        label="Download Executive Scorecard",
        data=buffer,
        file_name=f"CEC_Water_Bid_Go_NoGo_{spec_pdf.name}_{datetime.now():%Y%m%d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Upload specification PDF and project location")

st.markdown('<div class="footer">© 2025 CEC Controls – Proprietary & Confidential</div>', unsafe_allow_html=True)
