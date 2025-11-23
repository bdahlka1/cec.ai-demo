import streamlit as st
import PyPDF2
import re
import openpyxl
from datetime import datetime
import io
from copy import copy

st.set_page_config(page_title="Blake Dahlka – Bid Go/No-Go", layout="centered")

st.title("Blake Dahlka Consulting")
st.markdown("### Water & Wastewater Bid Go/No-Go Analyzer")
st.caption("45-minute manual review → 27-second AI-filled scorecard • PMP • GenAI certified")

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
    status = st.empty()

    # Extract ALL pages with page numbers
    page_texts = {}
    try:
        reader = PyPDF2.PdfReader(spec_pdf)
        total_pages = len(reader.pages)  # No limit – reads every page
        for i in range(total_pages):
            status.text(f"Reading page {i+1}/{total_pages}...")
            progress.progress((i+1)/total_pages)
            page_texts[i+1] = reader.pages[i].extract_text() or ""
        status.text("All pages read successfully")
    except Exception as e:
        st.error(f"PDF error: {e}")
        st.stop()

    # Scoring + comments with exact page references
    comments = {}
    earned = {}

    def grade(row, max_pts, keyword, positive, negative):
        hits = [(p, txt) for p, txt in page_texts.items() if keyword.lower() in txt.lower()]
        points = max_pts if hits else 0
        if hits:
            page = hits[0][0]
            comment = f"{points} pts – {positive} (Page {page})"
        else:
            comment = f"0 pts – {negative}"
        comments[row] = comment
        earned[row] = points
        return points

    total = 0
    total += grade(6,  10, "cec", "CEC listed as approved integrator", "Not listed as approved integrator")
    total += grade(12, 10, "rockwell|allen-bradley|vtscada|ignition|factorytalk", "Preferred PLC/SCADA platform", "Non-preferred or packaged system")
    total += grade(13, 10, "scada", "SCADA scope present", "No SCADA scope")
    total += grade(24,  5, "liquidated damages", "No liquidated damages", "Liquidated damages present")
    total += grade(26,  5, "installation by others|owner install", "Installation by others", "CEC to perform installation")
    total += grade(17,  5, "ohio|michigan|florida|georgia|alabama|kentucky|missouri|kansas|tennessee", "Within target geography", "Outside primary geography")

    decision = "GO" if total >= 75 else "NO-GO"

    # Build output with perfect styling
    out_wb = openpyxl.Workbook()
    ws = out_wb.active
    ws.title = "Go_NoGo_Result"

    # Copy every cell + safe styling
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

    # Write results
    for row_num, comment in comments.items():
        ws.cell(row=row_num, column=4, value=earned.get(row_num, 0))
        ws.cell(row=row_num, column=6, value=earned.get(row_num, 0))
        ws.cell(row=row_num, column=8, value=comment)

    ws["B35"] = total
    ws["B36"] = decision
    ws["B37"] = location
    ws["B38"] = datetime.now().strftime("%Y-%m-%d")

    buffer = io.BytesIO()
    out_wb.save(buffer)
    buffer.seek(0)

    st.success(f"Analysis complete → {decision} • Score: {total}/100")
    st.download_button(
        label="Download Fully Styled Scorecard with Page References",
        data=buffer,
        file_name=f"Water_Bid_Go_NoGo_{spec_pdf.name}_{datetime.now():%Y%m%d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Upload specification PDF and project location")

st.caption("© 2025 Blake Dahlka Consulting")
