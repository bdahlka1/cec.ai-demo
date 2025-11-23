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
        st.error
