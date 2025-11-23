import streamlit as st
import PyPDF2
import re
import openpyxl
from datetime import datetime
import io
from copy import copy

st.set_page_config(page_title="CEC Bid Go/No-Go", layout="centered")

st.title("CEC Controls – Water Bid Go/No-Go Analyzer")
st.caption("Branch Manager Michigan • Internal Tool")

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

    # Build output with perfect styling + column widths + row heights
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

    # Write grades and comments to Column G
    for row_num, comment in comments.items():
        ws.cell(row=row_num, column=4, value=earned.get(row_num, 0))  # Grade
        ws.cell(row=row_num, column=6, value=earned.get(row_num, 0))  # Points
        ws.cell(row=row_num, column=7, value=comment)                 # Comment in G

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
