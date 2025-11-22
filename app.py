import streamlit as st
import pdfplumber
import re
import openpyxl
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
import requests

# Password Protection (your choice – change "Water2025" to something private)
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("Enter Password to Access App", type="password")
    if password == "Water2025":
        st.session_state.authenticated = True
        st.experimental_rerun()
    else:
        st.error("Password required. Contact Blake for access.")
        st.stop()

# Page Config: Consulting-Branded
st.set_page_config(page_title="Blake Dahlka Consulting – Bid Go/No-Go", layout="wide")

# Header
st.title("🔵 Blake Dahlka Consulting")
st.markdown("### AI-Accelerated Bid Go/No-Go for Water & Wastewater")
st.markdown("_45-min manual review → <30-sec decision | PMP, GenAI for Executives Certified_")

# Load xlsx (Root File – Handles Your Sheet Structure)
@st.cache_data
def load_criteria():
    try:
        wb = openpyxl.load_workbook("Water Bid Go_NoGo Weighting Scale.xlsx")
        ws = wb.active
        criteria = {}
        for row in ws.iter_rows(min_row=5, max_row=26, min_col=1, max_col=6, values_only=True):
            if row[0] and row[1]:  # Item # and Description
                criteria[str(row[1])] = {"description": row[2], "possible_points": row[5] or 0, "red_flag": row[5] < 5}  # Flag if <5 points possible
        return criteria
    except FileNotFoundError:
        st.error("Upload 'Water Bid Go_NoGo Weighting Scale.xlsx' to repo root.")
        return {}

criteria = load_criteria()
if not criteria:
    st.stop()
max_score = sum(c["possible_points"] for c in criteria.values())

# Sidebar: Contact
with st.sidebar:
    st.markdown("### 📞 Contact Blake")
    st.markdown("248-787-3791")
    st.markdown("blake.dahlka@yahoo.com")
    st.markdown("[LinkedIn](https://www.linkedin.com/in/blake-dahlka-a0770939)")

# Main: Uploader + Location
col1, col2 = st.columns([3, 1])
with col1:
    spec_pdf = st.file_uploader("📁 Upload Spec PDF", type="pdf")
with col2:
    location = st.text_input("🏭 City, State", "St. Clair, MI")

if spec_pdf and location:
    with st.spinner("Analyzing..."):
        # Extract Text
        text = ""
        with pdfplumber.open(spec_pdf) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        text_lower = text.lower()

        # Keywords (Step 2)
        keywords = {
            "SCADA": bool(re.search(r"\bscada\b", text_lower)),
            "PLC": bool(re.search(r"\bplc\b", text_lower)),
            "Integrator": bool(re.search(r"system integrator|controls integrator", text_lower)),
            "Div 40/43/16": any(p in text_lower for p in ["division 40", "division 43", "div 40", "div 43", "div 16"])
        }

        # Red Flags & Highlights (Steps 3-4 – Stop Early)
        red_flags = []
        highlights = []
        if not any(keywords.values()):
            red_flags.append("No Technical Scope – NO-GO")
        if "liquidated damages" in text_lower:
            red_flags.append("LDs Present")
        if re.search(r"bond.{0,30}(1\.5|2|3|4|5)\%", text_lower):
            red_flags.append("High Bond")
        if keywords["Div 40/43/16"]:
            highlights.append("Div 40/43 OK – Deep Dive OK")

        # Scoring (xlsx – Early Stop on Flags)
        if red_flags:
            decision = "NO-GO"
            score = 0
        else:
            score = sum(c["possible_points"] * 0.9 for c in criteria.values())  # 90% base; tune
            score = round(score, 1)
            decision = "GO" if score >= 75 else "DISCUSS"

        # Map (Step 1)
        map_url = f"https://staticmap.openstreetmap.de/staticmap.php?center={location.replace(' ', '+')}&zoom=12&size=600x300&maptype=mapnik"
        st.image(map_url, caption=location)

        # Results
        colA, colB = st.columns(2)
        with colA:
            st.metric("Decision", decision)
            st.metric("Score", f"{score}/{max_score}")
        with colB:
            st.subheader("Keywords")
            for k, v in keywords.items():
                st.write(f"{k}: {'Yes' if v else 'No'}")

        if red_flags:
            st.error("Red Flags:")
            for f in red_flags: st.write(f"- {f}")
        if highlights:
            st.success("Highlights:")
            for h in highlights: st.write(f"- {h}")

        # PDF Summary (Yes, Real Download)
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("Blake Dahlka Consulting – Bid Summary", styles['Title']),
            Paragraph(f"Project: {spec_pdf.name}", styles['Heading2']),
            Paragraph(f"Decision: {decision} | Score: {score}/{max_score}", styles['Normal']),
        ]
        if red_flags:
            story.append(Paragraph("Red Flags:", styles['Heading3']))
            for f in red_flags: story.append(Paragraph(f"- {f}", styles['Normal']))
        doc.build(story)
        st.download_button("Download PDF Summary", buffer.getvalue(), f"GoNoGo_{spec_pdf.name}_{datetime.now().strftime('%Y%m%d')}.pdf", "application/pdf")

# Footer: Flyers (Repo Files in .devcontainer)
flyer1_url = "https://raw.githubusercontent.com/bdahlka1/cec-ai-demo/main/.devcontainer/CEC_Water%20Test%20Booth_Flyer.png"  # Convert PDF to PNG if needed
flyer2_url = "https://raw.githubusercontent.com/bdahlka1/cec-ai-demo/main/.devcontainer/CEC_Water.png"  # Assume PNG
st.image([flyer1_url, flyer2_url], caption=["Water Test Booth Flyer", "Water Controls Flyer"], width=300)

st.caption("© 2025 Blake Dahlka Consulting")
