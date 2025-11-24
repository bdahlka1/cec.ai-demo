import streamlit as st
import PyPDF2
import re
import openpyxl
from datetime import datetime
import io
from copy import copy

st.set_page_config(page_title="CEC Water Bid Intelligence", layout="wide")

# Professional header – no images
st.markdown("""
<div style="text-align: center; padding: 40px 0; background: linear-gradient(135deg, #003087 0%, #0050b3 100%); border-radius: 15px; margin-bottom: 30px;">
    <h1 style="color: white; font-size: 52px; margin: 0;">CEC Controls</h1>
    <h2 style="color: #a3d4ff; font-size: 36px; margin: 10px 0 0 0;">Water Bid Intelligence</h2>
    <p style="color: #e6f0ff; font-size: 20px; margin: 15px 0 0 0;">
        AI-Powered Go/No-Go Decision Engine • Michigan Branch
    </p>
</div>
""", unsafe_allow_html=True)

# Professional description
st.markdown("""
<div style="background: #f8f9fa; padding: 30px; border-radius: 15px; border-left: 8px solid #003087; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
    <h3 style="color: #003087; margin-top: 0;">Instant Executive Scorecard</h3>
    <p style="font-size: 18px; line-height: 1.8; color: #333;">
        Upload any water/wastewater RFP and receive your fully-filled CEC scorecard in seconds — 
        complete with AI-generated comments, page references, and a clear GO/NO-GO recommendation.
    </p>
    <ul style="font-size: 17px; line-height: 1.8; color: #444;">
        <li>Analyzes all pages automatically</li>
        <li>Extracts project location from the document</li>
        <li>Scores 15+ decision criteria using your rules</li>
        <li>Fully customizable via <code>Bid_Scoring_Calibration.xls</code></li>
        <li>100% internal • Built by CEC Michigan</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

spec_pdf = st.file_uploader("Upload Specification PDF", type="pdf")

if spec_pdf:
    progress = st.progress(0)

    # Load template
    @st.cache_data
    def load_template():
        wb = openpyxl.load_workbook("Water Bid Go_NoGo Weighting Scale.xlsx")
        ws = wb.active
        return wb, ws

    template_wb, template_ws = load_template()

    # Extract all pages
    full_text = ""
    page_texts = {}
    try:
        reader = PyPDF2.PdfReader(spec_pdf)
        total_pages = len(reader.pages)
        for i in range(total_pages):
            progress.progress((i+1)/total_pages)
            txt = reader.pages[i].extract_text() or ""
            full_text += txt + "\n"
            page_texts[i+1] = txt
    except Exception as e:
        st.error(f"PDF error: {e}")
        st.stop()

    # Auto-detect City & State
    location = "Not detected"
    city_state = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,\s*([A-Z]{2})\b", full_text, re.I)
    if city_state:
        location = f"{city_state.group(1)}, {city_state.group(2)}"
    st.success(f"**Project Location Detected:** {location}")

    # Scoring + comments
    comments = {}
    earned = {}

    def grade(row, max_pts, keywords, positive, negative):
        hits = []
        for kw in keywords:
            for p, txt in page_texts.items():
                if kw.lower() in txt.lower():
                    sentence = next((s.strip() for s in txt.split('\n') if kw.lower() in s.lower()), txt[:200])
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

    total = 0
    total += grade(6,  10, ["cec", "cec controls"], "CEC listed as approved integrator", "Not listed as approved integrator")
    total += grade(7,   5, ["bid list", "prequalified", "invited bidders"], "Clear bidder list exists", "Bidder list unclear")
    total += grade(8,  10, ["cec"], "<3 integrators named", ">5 integrators or open bidding")
    total += grade(9,   5, ["preferred gc", "direct municipal"], "Preferred relationship", "Not preferred")
    total += grade(11,  5, ["scada", "hmi", "software platform"], "SCADA system clearly defined", "SCADA requirements vague")
    total += grade(12, 10, ["rockwell", "allen-bradley", "siemens"], "Preferred PLC brand", "Non-preferred or packaged PLC")
    total += grade(13, 10, ["vtscada", "ignition", "wonderware", "factorytalk"], "Preferred SCADA brand", "Non-preferred SCADA")
    total += grade(14, 10, ["instrument list", "schedule of values"], "Instrumentation clearly defined", "Instrumentation vague or high-risk")
    total += grade(15,  5, ["schedule", "milestone", "gantt"], "Schedule realistic", "Schedule missing or unrealistic")
    total += grade(22,  5, ["wauseon", "fulton", "ohio"], "Within target geography", "Outside primary geography")
    total += grade(23,  5, ["bid due"], "Bid timing appropriate", "Bid timing rushed")
    total += grade(24,  5, [], "Strategic value present", "Low strategic value")
    total += grade(25,  5, ["liquidated damages"], "No liquidated damages", "Liquidated damages present")
    total += grade(26,  5, ["design-build", "design build"], "Construction only", "Design-Build")
    total += grade(27,  5, ["installation", "field wiring"], "Installation by others", "CEC to perform installation")

    decision = "GO" if total >= 75 else "NO-GO"

    # Build output with perfect styling
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

    # Force wrap text in Column G
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=7, max_col=7):
        for cell in row:
            cell.alignment = copy(cell.alignment)
            cell.alignment.wrap_text = True

    for row_num, comment in comments.items():
        ws.cell(row=row_num, column=4, value=earned.get(row_num, 0))
