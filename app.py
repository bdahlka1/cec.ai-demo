import streamlit as st
import PyPDF2
import re
import openpyxl
from datetime import datetime
import io
from copy import copy

st.set_page_config(page_title="CEC Water Bid AI", layout="wide")

# Hero branding
st.image("CEC + SCIO Image.png", use_column_width=True)

st.markdown("""
<div style="text-align: center; padding: 20px;">
    <h1 style="color: #003087; font-size: 42px;">CEC Controls – Water Bid Intelligence</h1>
    <p style="font-size: 22px; color: #444;">
        AI-Powered Go/No-Go Decision Engine • Michigan Branch
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: #f8f9fa; padding: 25px; border-radius: 12px; border-left: 6px solid #003087;">
    <h3 style="color: #003087;">What this tool does</h3>
    <p style="font-size: 18px; line-height: 1.7;">
        Upload any water/wastewater RFP and receive an <strong>instant, fully-filled Go/No-Go scorecard</strong> 
        in your exact CEC format — complete with AI-generated comments, page references, and a clear recommendation.
    </p>
    <p style="font-size: 16px; color: #555;">
        • Scores 15+ decision criteria automatically<br>
        • Extracts project location from the RFP<br>
        • Fully customizable via the <code>Bid_Scoring_Calibration.xls</code> file (no code changes required)<br>
        • 100% internal tool – built and owned by CEC Michigan
    </p>
</div>
""", unsafe_allow_html=True)

spec_pdf = st.file_uploader("Upload Specification PDF", type="pdf")

if spec_pdf:
    progress = st.progress(0)
    status = st.empty()

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
    location = "Unknown"
    city_state = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,\s*([A-Z]{2})\b", full_text, re.I)
    if city_state:
        location = f"{city_state.group(1)}, {city_state.group(2)}"
    st.info(f"**Detected Project Location:** {location}")

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

    # Build output
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
        ws.cell(row=row_num, column=7, value=comment)

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
    st.info("Upload specification PDF")

st.caption("© 2025 CEC Controls – Internal Tool")
