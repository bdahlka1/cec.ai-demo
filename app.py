import streamlit as st
import PyPDF2
import re
import openpyxl
from datetime import datetime
import io
from copy import copy
from openpyxl.styles import Alignment

st.set_page_config(page_title="CEC Bid Go/No-Go", layout="centered")

st.title("CEC Controls – Water Bid Go/No-Go Analyzer")
st.caption("Branch Manager Michigan • Internal Tool")

# Load calibration rules
@st.cache_data
def load_calibration():
    wb = openpyxl.load_workbook("Bid_Scoring_Calibration.xlsx")
    ws = wb.active
    rules = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0]:
            rules[int(row[0])] = {
                "max": row[2] or 0,
                "pos_kw": [k.strip() for k in (row[3] or "").split(",") if k.strip()],
                "neg_kw": [k.strip() for k in (row[4] or "").split(",") if k.strip()],
                "pos_pts": row[5] or row[2],
                "neg_pts": row[6] or 0
            }
    return
