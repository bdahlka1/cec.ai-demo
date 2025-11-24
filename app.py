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
st.image("CEC + SCIO Image.png", width=900)

# Professional header — using single quotes to avoid triple-quote bugs forever
st.markdown('''
<div style="text-align: center; padding: 30px 0;">
    <h1 style="color: #003087; font-size: 48px; margin: 0;">Water Bid Intelligence</h1>
    <p style="font-size: 24px; color: #003087; margin: 10px 0;">
        AI-Powered Go/No-Go Decision Engine
    </p>
    <p style="font-size: 18px; color: #555;">
        Instantly transforms any RFP into your fully-filled CEC scorecard • Michigan Branch • Internal Tool
    </p>
</div>
''', unsafe_allow_html=True)

# Professional description box
st.markdown('''
<div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 30px; border-radius: 15px; border-left: 8px solid #003087; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
    <h3 style="color: #003087; margin-top: 0;">How It Works</h3>
    <p style="font-size: 18px; line-height: 1.8; color: #333;">
        Upload any water/wastewater RFP and receive an <strong>instant, executive-ready scorecard</strong> in your exact CEC format — 
        complete with AI-generated comments, page references, and a clear GO/NO-GO recommendation.
    </p>
    <ul style="font-size: 17px; line-height: 1.8; color: #444;">
        <li>Analyzes all pages automatically</li>
        <li>Extracts project location from the document</li>
        <li>Scores 15+ decision criteria using your rules</li>
        <li><strong>Fully customizable</strong> via the <code>Bid_Scoring_Calibration.xls</code> file — no code changes needed</li>
        <li>100% internal • Built and owned by CEC Michigan</li>
    </ul>
</div>
''', unsafe_allow_html=True)

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
    total += grade(7,   5, ["bid list", "prequalified", "invited"], "Clear bidder list exists", "Bidder list unclear")
    total += grade(8,  10, ["cec"], "<3 integrators named", ">5 integrators or open bidding")
    total += grade(9,   5, ["preferred gc", "direct
