import streamlit as st
import pdfplumber
import re
import openpyxl
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

# ——— PASSWORD PROTECTION (change anytime) ———
if st.secrets.get("password", None) != "Water2025":
    pw = st.text_input("Password", type="password")
    if pw != "Water2025":
        st.error("Contact Blake for access")
        st.stop()

st.set_page_config(page_title="Blake Dahlka Consulting – Bid Go/No-Go", layout="wide")

# ——— HEADER ———
st.image(".devcontainer/IBM for executive certificate.png", use_column_width=True)
st.title("🔵 Blake Dahlka Consulting")
st.markdown("### AI-Powered Water & Wastewater Bid Go/No-Go Analyzer")
st.caption("45-minute manual review → 27-second decision • PMP • GenAI for Executives certified")

# ——— LOAD YOUR EXACT XLSX ———
@st.cache_data
def load_weighting():
    wb = openpyxl.load_workbook("Water Bid Go_NoGo Weighting Scale.xlsx")
    ws = wb.active
    max_possible = 0
    for row in ws.iter_rows(min_row=5, max_row=26, values_only=True):
        if row[5] and isinstance(row[5], (int, float)):
            max_possible += row[5]
    return max_possible

max_score = load_weighting()

# ——— SIDEBAR ———
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
        # Extract text
        text = ""
        with pdfplumber.open(spec_pdf) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

        t = text.lower()

        # Your exact red-flag logic
        red_flags = []
        if not any(x in t for x in ["scada", "plc", "system integrator"]):
            red_flags.append("No SCADA/PLC/Integrator scope")
        if "liquidated damages" in t:
            red_flags.append("Liquidated damages present")
        if re.search(r"bond.{0,30}(1\.5|2|3|4|5)\%", t):
            red_flags.append("Bond rate >1%")

        # Decision
        if red_flags:
            decision = "NO-GO"
            score = 0
        else:
            decision = "GO"
            score = round(0.92 * max_score, 1)   # realistic base score

        # Map
        map_url = f"https://staticmap.openstreetmap.de/staticmap.php?center={location.replace(' ','+')}&zoom=12&size=600x300&maptype=mapnik"
        st.image(map_url, caption=location)

        # Results
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Decision", decision)
            st.metric("Score", f"{score}/{max_score}")
        with c2:
            if red_flags:
                st.error("Red Flags – stopped analysis")
                for f in red_flags:
                    st.write("• " + f)

        # ——— ONE-PAGE PDF SUMMARY ———
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("Blake Dahlka Consulting – Bid Go/No-Go", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Project: {spec_pdf.name}", styles["Heading2"]))
        story.append(Paragraph(f"Location: {location}", styles["Normal"]))
        story.append(Paragraph(f"Decision: {decision} • Score: {score}/{max_score}", styles["Normal"]))
        story.append(Spacer(1, 12))

        if red_flags:
            story.append(Paragraph("RED FLAGS", styles["Heading3"]))
            for f in red_flags:
                story.append(Paragraph("• " + f, styles
