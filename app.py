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

    # Extract text with page numbers
    page_texts = {}
    try:
        reader = PyPDF2.PdfReader(spec_pdf)
        total_pages = min(len(reader.pages), 100)
        for i in range(total_pages):
            status.text(f"Reading page {i+1}/{total_pages}...")
            progress.progress((i+1)/total_pages)
            page_texts[i+1] = reader.pages[i].extract_text() or ""
    except:
        st.warning("PDF partially unreadable – still scoring")

    # Scoring + traceable comments
    comments = {}
    earned = {}

    def grade(row, max_pts, keyword, positive, negative):
        hits = [(p, text) for
