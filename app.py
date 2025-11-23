import streamlit as st
import PyPDF2
import re
import openpyxl
from datetime import datetime
import pandas as pd
import io

st.set_page_config(page_title="Blake Dahlka – Bid Go/No-Go", layout="centered")

st.title("Blake Dahlka Consulting")
st.markdown("### Water & Wastewater Bid Go/No-Go Analyzer")
st.caption("45-minute manual review → 27-second decision • PMP • GenAI certified")

# Load your exact weighting file
@st.cache_data
def load_template():
    wb = openpyxl.load_workbook("Water Bid Go_NoGo Weighting Scale.xlsx", data_only=True)
    ws = wb.active
    data = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        data.append(row)
    return data, wb

template_data, template_wb = load_template()

# Input
col1, col2 = st.columns([3,1])
with col1:
    spec_pdf = st.file_uploader("Upload Specification PDF", type="pdf")
with col2:
    location = st.text_input("Project City, State", "St. Clair, MI")

if spec_pdf and location:
    with st.spinner("Analyzing specification…"):
        # Extract text
        reader = PyPDF2.PdfReader(spec_pdf)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        t = text.lower()

        # Red-flag detection
        red_flags = []
        if not any(x in t for x in ["scada", "plc", "system integrator", "controls integrator"]):
            red_flags.append("No SCADA/PLC/Integrator scope")
        if "liquidated damages" in t:
            red_flags.append("Liquidated damages present")
        if re.search(r"bond.{0,30}(1\.5|2|3|4|5)\%", t):
            red_flags.append("Bond rate >1%")

        # Decision
        if red_flags:
            decision = "NO-GO"
            final_score = 0
        else:
            decision = "GO"
            final_score = 92  # base score – you can adjust later

        # Build output workbook
        output_wb = openpyxl.Workbook()
        ws_out = output_wb.active
        ws_out.title = "Go_NoGo_Result"

        # Copy template structure
        for r_idx, row in enumerate(template_data, start=1):
            for c_idx, value in enumerate(row, start=1):
                ws_out.cell(row=r_idx, column=c_idx, value=value)

        # Fill in results
        ws_out["B35"] = final_score          # Total score
