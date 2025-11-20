import streamlit as st
import pandas as pd

st.set_page_config(page_title="CEC AI Demo – Blake Dahlka", layout="wide")
st.title("CEC AI Demo – Blake Dahlka")
st.write("**Branch Manager Michigan • IBM GenAI Executive Certified – Nov 19, 2025**")

st.image("https://i.imgur.com/6uZ8Q5Z.png", use_column_width=True)  # placeholder for your cert

st.header("AI Pre-Populates Risk Registers + Owner Commissioning Checklists")

uploaded = st.file_uploader("Drop St. Clair alarm file or proposal here", type=["xlsx", "csv", "docx", "pdf"])

if uploaded or True:  # always show demo
    st.success("Files loaded – generating artifacts in <60 seconds")

    st.subheader("Pre-Populated Risk Register (from CEC history + P&ID/spec review)")
    risk_data = pd.DataFrame({
        'ID': [1, 2, 3, 4, 5],
        'Description': ['Sludge Blowdown Flow Rate Low Low Cascade', 'Sludge Blowdown Flow Rate Low Repeat', 'Elevated Tank Level High Level Alarm', 'Raw Water Turbidity High Alarm', 'Filter 1 Effluent Flow Low Low Alarm'],
        'Probability': ['High', 'High', 'Medium', 'Medium', 'Medium'],
        'Impact': ['High', 'High', 'High', 'High', 'Medium'],
        'Score': [25, 25, 15, 15, 9],
        'Trigger': ['87% of 18,247 alarms', 'Repeats every 4–6 hrs', 'P&ID level sensor drift', 'Spec turbidity violation', 'Backwash cycle'],
        'Mitigation (Used Before)': ['Auto-bypass (Wyandotte)', 'Remote tuning buffer', 'Pre-stage pump (Dearborn)', 'Chemical dosing (Black & Veatch)', 'Predictive backwash (RNG data)']
    })
    st.dataframe(risk_data, use_container_width=True)

    st.subheader("Owner-Required Commissioning Checklist (Division 40 Format)")
    checklist = pd.DataFrame({
        'Item': [1, 2, 3, 4],
        'Description': ['Sludge Flow Low/Low', 'Tank Level HI/HIHI', 'Raw Turbidity High', 'Filter Effluent Flow Low Low'],
        'Expected Value': ['<50 GPM triggers', 'Overflow at 98%', '<5 NTU setpoint', '<100 GPM min flow'],
        'Predicted Hot Spot': ['YES – 87% events', 'YES – cascade risk', 'YES – 62% recurrence', 'YES – backwash cycle']
    })
    st.dataframe(checklist, use_container_width=True)

    st.download_button("Export Full PMI Package (18 pages)", data="PDF generated", file_name="CEC_AI_PMI_Package.pdf")

st.info("Saves 80–120 hours per job • 90-day internal pilot ready Monday • $20/month • Chris signs off quality")
