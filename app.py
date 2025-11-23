import streamlit as st
import PyPDF2
import re
import openpyxl
from datetime import datetime
import io

st.set_page_config(page_title="Blake Dahlka – Bid Go/No-Go", layout="centered")

st.title("Blake Dahlka Consulting")
st.markdown("### Water & Wastewater Bid Go/No-Go Analyzer")
st.caption("45-minute manual review → 27-second AI-filled scorecard • PMP • GenAI certified")

# Load template with full styling
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

    # Extract text + keep page numbers
    page_texts = {}
    try:
        reader = PyPDF2.PdfReader(spec_pdf)
        total_pages = min(len(reader.pages), 100)
        for i in range(total_pages):
            status.text(f"Reading page {i+1}/{total_pages}...")
            progress.progress((i+1)/total_pages)
            page_text = reader.pages[i].extract_text() or ""
            page_texts[i+1] = page_text
    except:
        st.warning("PDF partially unreadable – still scoring with available text")

    # Combine all text for keyword search
    full_text = " ".join(page_texts.values()).lower()

    # Scoring + traceable comments
    comments = {}
    earned = {}

    def grade(row, max_pts, keyword, positive_reason, negative_reason):
        hits = [(p, text) for p, text in page_texts.items() if keyword.lower() in text.lower()]
        points = max_pts if hits else 0
        if hits:
            page = hits[0][0]
            section = "Bid Documents" if "liquidated" in keyword.lower() else "Project Description"
            comment = f"{points} pts – {positive_reason} (Page {page}, {section})"
        else:
            comment = f"0 pts – {negative_reason}"
        comments[row] = comment
        earned[row] = points
        return points

    total = 0
    total += grade(6,  10, "cec", "CEC listed as approved integrator", "Not listed as approved integrator")
    total += grade(12, 10, "rockwell|allen-bradley|vtscada|ignition", "Preferred PLC/SCADA platform mentioned", "Non-preferred or packaged system")
    total += grade(13, 10, "scada", "SCADA scope present", "No SCADA scope")
    total += grade(24,  5, "liquidated damages", "No liquidated damages", "Liquidated damages present")
    total += grade(26,  5, "installation by others", "Installation by others", "CEC to perform installation")
    # Add more rows as needed – this is the core

    decision = "GO" if total >= 75 else "NO-GO"

    # Build output with exact styling
    out_wb = openpyxl.Workbook()
    ws = out_wb.active
    ws.title = "Go_NoGo_Result"

    # Copy every cell + styling
    for row in template_ws.iter_rows():
        for cell in row:
            new_cell = ws.cell(row=cell.row, column=cell.column, value=cell.value)
            if cell.has_style:
                new_cell.font = openpyxl.styles.Font(name=cell.font.name, size=cell.font.size,
                                                   bold=cell.font.bold, italic=cell.font.italic,
                                                   color=cell.font.color.rgb if cell.font.color else None)
                new_cell.fill = openpyxl.styles.PatternFill(copy(cell.fill))
                new_cell.border = openpyxl.styles.Border(copy(cell.border))
                new_cell.alignment = openpyxl.styles.Alignment(copy(cell.alignment))

    # Write grades and comments
    for row_num, comment in comments.items():
        ws.cell(row=row_num, column=4, value=earned.get(row_num, 0))   # Grade
        ws.cell(row=row_num, column=6, value=earned.get(row_num, 0))   # Points
