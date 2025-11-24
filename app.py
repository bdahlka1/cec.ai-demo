import streamlit as st
import PyPDF2
import re
import openpyxl
from datetime import datetime
import io
from copy import copy
from openpyxl.styles import Alignment

st.set_page_config(page_title="CEC Water Bid Intelligence", layout="wide")

# CEC + SCIO Logo – perfect size
st.image("CEC + SCIO Image.png", width=450)

# Professional header
st.markdown("""
<div style="text-align: center; padding: 30px 0;">
    <h1 style="color: #003087; font-size: 48px; margin: 0;">Water Bid Intelligence</h1>
    <p style="font-size: 24px; color: #003087; margin: 10px 0;">
        AI-Powered Go/No-Go Decision Engine
    </p>
    <p style="font-size: 18px; color: #555;">
        Instantly transforms any RFP into your fully-filled CEC scorecard • Michigan Branch • Internal Tool
    p>
</div>
""", unsafe_allow_html=True)

# Professional description
st.markdown("""
<div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 30px; border-radius: 15px; border-left: 8px solid #003087; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
    <h3 style="color: #003087; margin-top: 0;">How It Works</h3>
    <p style="font-size: 18px; line-height: 1.8; color: #333;">
        Upload any water/wastewater RFP and receive an <strong>instant scorecard + evidence report</strong> showing every sentence that drove the decision.
    </p>
    <ul style="font-size: 17px; line-height: 1.8; color: #444;">
        <li>Analyzes all pages automatically</li>
        <li>Extracts project location</li>
        <li>Scores 15+ criteria</li>
        <li><strong>Fully customizable</strong> via <code>Bid_Scoring_Calibration.xls</code></li>
        <li>100% internal • Built by CEC Michigan</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Load template once
@st.cache_data
def load_template():
    wb = openpyxl.load_workbook("Water Bid Go_NoGo Weighting Scale.xlsx")
    return wb, wb.active

template_wb, template_ws = load_template()

spec_pdf = st.file_uploader("Upload Specification PDF", type="pdf")

if spec_pdf:
    progress = st.progress(0)

    full_text = ""
    page_texts = {}
    try:
        reader = PyPDF2.PdfReader(spec_pdf)
        total_pages = len(reader.pages)
        for i in range(total_pages):
            progress.progress((i + 1) / total_pages)
            txt = reader.pages[i].extract_text() or ""
            full_text += txt + "\n"
            page_texts[i + 1] = txt
    except Exception as e:
        st.error(f"PDF error: {e}")
        st.stop()

    # Auto-detect location
    location = "Not detected"
    city_state = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,\s*([A-Z]{2})\b", full_text, re.I)
    if city_state:
        location = f"{city_state.group(1)}, {city_state.group(2)}"
    st.success(f"**Project Location Detected:** {location}")

    # Scoring with evidence
    comments = {}
    earned = {}
    evidence = {}

    def grade(row, max_pts, keywords, positive, negative):
        hits = []
        for kw in keywords:
            for p, txt in page_texts.items():
                if kw.lower() in txt.lower():
                    sentence = next((s.strip() for s in txt.split('\n') if kw.lower() in s.lower()), txt[:300])
                    hits.append((p, sentence))
                    break
        points = max_pts if hits else 0
        if hits:
            page, sentence = hits[0]
            comment = f"{points} pts – {positive} (Page {page})"
            evidence[row] = (page, sentence.replace("\n", " ").replace("  ", " "))
        else
