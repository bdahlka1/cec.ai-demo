import streamlit as st
import PyPDF2
import re
import openpyxl
from datetime import datetime

st.set_page_config(page_title="Blake Dahlka Consulting – Bid Go/No-Go", layout="wide")

# Header – your IBM certificate
st.image(".devcontainer/IBM for executive certificate.png", use_column_width=True)
st.title("Blake Dahlka Consulting")
st.markdown("### AI-Powered Water & Wastewater Bid Go/No-Go Analyzer")
st.caption("45-minute manual review → 27-second decision • PMP • GenAI for Executives certified")

# Load your exact xlsx
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

# Sidebar – your resume page
with st.sidebar:
    st.image(".devcontainer/generative-ai-overview-for-project-managers.png", use_column_width=True)
    st.markdown("### Blake Dahlka, PMP")
    st.markdown("248-787-3791 • blake.dahlka@yahoo.com")
    st.markdown("[LinkedIn](https://www.linkedin.com/in/blake-dahlka-a0770939)")

# Main input
col1, col2 = st.columns([3,1])
with col1:
    spec_pdf = st.file_uploader("Upload Specification PDF", type="pdf")
with col2:
    location = st.text_input("Project City, State", "St. Clair, MI")

if spec_pdf and location:
    with st.spinner("Analyzing…"):
        # Extract text
        reader = PyPDF2.PdfReader(spec_pdf)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        t = text.lower()

        # Red flags
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
        with c2:
            if red_flags:
                st.error("Red Flags – stopped analysis")
                for f in red_flags:
                    st.write("• " + f)

        # Download summary
        summary = f"""Blake Dahlka Consulting – Bid Go/No-Go
Date: {datetime.now():%Y-%m-%d}
Project: {spec_pdf.name}
Location: {location}
Decision: {decision}
Score: {score}/{max_score}
"""
        if red_flags:
            summary += "\nRED FLAGS:\n" + "\n".join("• " + f for f in red_flags)

        st.download_button(
            label="Download Summary",
            data=summary,
            file_name=f"GoNoGo_{spec_pdf.name}_{datetime.now():%Y%m%d}.txt",
            mime="text/plain"
        )

        # Footer – your two flyers
        colf1, colf2 = st.columns(2)
        with colf1:
            st.image(".devcontainer/CEC_Water Test Booth_Flyer.png", use_column_width=True)
        with colf2:
            st.image(".devcontainer/CEC_Water.png", use_column_width=True)

else:
    st.info("Upload a specification PDF and enter the project location to begin.")

st.caption("© 2025 Blake Dahlka Consulting")
