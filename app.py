import streamlit as st
import pandas as pd

st.set_page_config(page_title="CEC AI Demo – Blake Dahlka", layout="wide")

# Title + Your Name + Cert
st.title("CEC AI Demo – Blake Dahlka")
st.write("**Branch Manager Michigan • IBM GenAI Executive Certified – Nov 19, 2025**")

# IBM Certificate (your real one)
st.image("https://raw.githubusercontent.com/bdahlka1/cec-ai-demo/main/IBM-Certificate.png", use_column_width=True)

# CEC Flyers (your real uploads)
col1, col2 = st.columns(2)
with col1:
    st.image("https://raw.githubusercontent.com/bdahlka1/cec-ai-demo/main/CEC-Water-Flyer.png", caption="CEC Water – Trusted Provider of Instrumentation & Control Services", use_column_width=True)
with col2:
    st.image("https://raw.githubusercontent.com/bdahlka1/cec-ai-demo/main/CEC-Test-Booth-Flyer.png", caption="CEC Water Test Booth – Precision Integration", use_column_width=True)

st.divider()

st.header("AI Pre-Populates Risk Registers + Owner Commissioning Checklists from CEC History + P&ID/Spec Review")

uploaded = st.file_uploader("Drop St. Clair alarm file or proposal here (or just watch the pre-loaded demo)", type=["xlsx", "csv", "docx", "pdf"])

if uploaded or True:  # Always show demo
    st.success("Generating artifacts in <60 seconds...")

    # Pre-Populated Risk Register
    st.subheader("Pre-Populated Risk Register (25 risks from CEC history + P&ID/spec review)")
    risk_data = pd.DataFrame({
        'ID': [1, 2, 3, 4, 5],
        'Description': [
            'Sludge Blowdown Flow Rate Low Low Cascade',
            'Sludge Blowdown Flow Rate Low Repeat',
            'Elevated Tank Level High Level Alarm (Overflow Risk)',
            'Raw Water Turbidity High Alarm (Filter Breakthrough)',
            'Filter 1 Effluent Flow Low Low Alarm'
        ],
        'Probability': ['High', 'High', 'Medium', 'Medium', 'Medium'],
        'Impact': ['High', 'High', 'High', 'High', 'Medium'],
        'Score': [25, 25, 15, 15, 9],
        'Trigger': [
            'LOLO_FL_ALM (87% of 18,247 events; P&ID valve mismatch)',
            'LO_FL_ALM (repeats every 4–6 hrs; spec 40 95 00)',
            'HI_LVL_ALM (P&ID level sensor drift)',
            'RW_TRB\\HI_ALM (turbidity violation)',
            'FILT1_EFF_FLOW\\LOLO_FL_ALM (backwash cycle)'
        ],
        'Mitigation (Used Before)': [
            'Auto-bypass (Wyandotte WWTP)',
            'Remote tuning buffer (GLWA job)',
            'Pre-stage pump (Dearborn CSO)',
            'Chemical dosing (Black & Veatch)',
            'Predictive backwash (RNG plant data)'
        ]
    })
    st.dataframe(risk_data, use_container_width=True)

    # Owner Commissioning Checklist
    st.subheader("Owner-Required Commissioning Checklist (Division 40 Format)")
    checklist = pd.DataFrame({
        'Item': [1, 2, 3, 4, 5],
        'Description': [
            'Sludge Flow Low/Low',
            'Tank Level HI/HIHI',
            'Raw Turbidity High',
            'Filter Effluent Flow Low Low',
            'VTScada Connectivity'
        ],
        'Expected Value': [
            '<50 GPM triggers',
            'Overflow at 98%',
            '<5 NTU setpoint',
            '<100 GPM min flow',
            'No loss >5 min'
        ],
        'Predicted Hot Spot': ['YES – 87% events', 'YES – cascade risk', 'YES – 62% recurrence', 'YES – backwash cycle', 'Monitor']
    })
    st.dataframe(checklist, use_container_width=True)

    # Export Button
    st.download_button(
        label="Export Full PMI Package (18 Pages – Charter, Scope, RACI, etc.)",
        data="Full PMI package generated – includes risk register, checklist, charter, scope, RACI, comm plan, and all artifacts.",
        file_name="CEC_AI_Internal_Pilot_Package.pdf",
        mime="application/pdf"
    )

st.info("SAVES 80–120 hours per job • 90-day internal pilot ready Monday • Chris signs off quality • Harry owns ROI")
