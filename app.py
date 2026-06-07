import streamlit as st

st.set_page_config(
    page_title="Doradca Finansowy",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.switch_page("pages/01_klienci.py")
