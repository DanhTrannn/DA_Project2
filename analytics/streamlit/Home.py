import streamlit as st

st.set_page_config(page_title="AdventureWorks Analytics", layout="wide")

st.title("AdventureWorks Analytics")
st.page_link(
    "pages/1_Customer_Analytics.py",
    label="Customer Analytics",
)
st.page_link(
    "pages/3_Sales_Intelligence.py",
    label="Sales Forecast Analytics",
)
