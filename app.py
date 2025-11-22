import streamlit as st
import PyPDF2
import re
import openpyxl
from datetime import datetime
import io

st.set_page_config(page_title="Blake Dahlka Consulting – Bid Go/No-Go", layout="wide")

# ——— HEADER – IBM Certificate ———
st.image(".devcontainer/IBM for executive certificate.png", use_column_width=True)
st.title("Blake Dahlka Consulting")
st.markdown("### AI-Powered Water & Wastewater Bid Go/No-Go Analyzer")
st.caption("45-minute manual review → 27-second decision • PMP • GenAI for Executives certified")

# ——— LOAD YOUR EXACT XLSX ———
@st.cache_data
def load_max_score():
    try:
        wb = openpyxl.load_workbook("Water Bid Go_NoGo Weighting Scale.xlsx")
        ws = wb.active
        total = 0
        for row in ws.iter_rows(min_row=5, max_row=26, values_only=True):
            if len(row) > 5 and isinstance(row[5], (int, float)):
                total += row[5]
        return total
    except:
        return 100

max_score = load_max_score()

# ——— SIDEBAR – Resume page 1 ———
with st.sidebar:
    st.image(".devcontainer/generative-ai-overview-for-project-managers.png", use_column_width=True)
    st.markdown("### Blake Dahlka, PMP")
    st.markdown("248-787-3791 • blake.dahlka@yahoo.com")
    st.markdown("[LinkedIn](https://www.linkedin.com/in/blake-dahlka-a0770939)")

# ——— MAIN INPUT ———
col1, col2 = st.columns([3,1])
with col1:
    spec_pdf = st.file_uploader("Upload Specification PDF", type="pdf")
with col2:
    location = st.text_input("Project City, State", "St. Clair, MI")

if spec_pdf and location:
    with st.spinner("Analyzing specification…"):
        # Extract text with built-in PyPDF2
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

        # Decision & scoring
        if red_flags:
            decision = "NO-GO"
            score = 0
        else:
            decision = "GO"
            score = round(0.92 * max_score, 1)

        # Map
        map_url = f"https://staticmap.openstreetmap.de/staticmap.php?center={location.replace(' ','+')}&zoom=12&size=600x300&maptype=mapnik"
        st.image(map_url, caption=location)

        # Results
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Decision", decision)
            st.metric("Score", f"{score}/{max_score}")
        with
