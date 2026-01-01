import streamlit as st

from calc import render_calc_page
from history import render_history_page


# ---------- Page Config ----------
st.set_page_config(
    page_title="월별 영수증 관리",
    layout="centered"
)

# ---------- Global Style ----------
st.markdown(
    """
    <style>
    html, body, [class*="css"]  {
        font-size: 20px;
    }
    h1 {
        font-size: 2.2rem;
    }
    h2 {
        font-size: 1.8rem;
    }
    h3 {
        font-size: 1.5rem;
    }
    button {
        font-size: 1.1rem !important;
        padding: 0.6em 1.2em !important;
    }
    input, label, textarea, select {
        font-size: 1.1rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- App Title ----------
st.title("📄 월별 영수증 관리")
st.caption("영수증을 업로드하여 월별 합계를 계산하고, 과거 기록을 조회할 수 있습니다.")
st.divider()

# ---------- Tabs ----------
tabs = st.tabs(["🧮 계산하기", "📊 기록 보기"])

with tabs[0]:
    render_calc_page()

with tabs[1]:
    render_history_page()