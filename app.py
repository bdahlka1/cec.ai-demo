import streamlit as st
import PyPDF2
import re
import openpyxl
from datetime import datetime
import io
from copy import copy

st.set_page_config(page_title="CEC Water Bid Intelligence", layout="wide")

# CEC + SCIO Logo – perfect size
st.image("CEC + SCIO Image.png", width=900)

# Professional header
st.markdown("""
<div style="text-align: center; padding: 30px 0;">
    <h1 style="color: #003087; font-size: 48px; margin: 0;">Water Bid Intelligence</h1>
    <p style="font-size: 24px; color: #003087; margin: 10px 0;">
        AI-Powered Go/No-Go Decision Engine
    </p>
    <p style="font-size: 18px; color: #555;">
        Instantly transforms any RFP into your fully-filled CEC scorecard • Michigan Branch • Internal Tool
    </p>
</div>
""", unsafe_allow_html=True)

# Professional description box
st.markdown("""
<div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
