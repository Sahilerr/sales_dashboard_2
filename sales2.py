import streamlit as st
import pandas as pd
from PIL import Image
import plotly.express as px
import numpy as np

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Sales Dashboard",
    layout="wide"
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
df = pd.read_csv("retail_sales_dataset.csv")
df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
df = df.dropna(subset=['Date'])

# --------------------------------------------------
# FEATURE ENGINEERING
# --------------------------------------------------
df['Month_Period'] = df['Date'].dt.to_period('M').dt.to_timestamp()
df['Month_Label'] = df['Month_Period'].dt.strftime('%b %Y')
df['Month_Name'] = df['Month_Period'].dt.strftime('%B')

# --------------------------------------------------
# HEADER
# --------------------------------------------------
logo = Image.open("download (1).jpg")

c1, c2 = st.columns([1, 6])
with c1:
    st.image(logo, width=110)
with c2:
    st.markdown(
        "<h1 style='margin-top:25px;'>Sales Prediction Dashboard</h1>",
        unsafe_allow_html=True
    )

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------
st.sidebar.header("Dashboard Controls 📊")

category_filter = st.sidebar.multiselect(
    "Product Category",
    sorted(df['Product Category'].unique()),
    default=sorted(df['Product Category'].unique())
)

gender_filter = st.sidebar.multiselect(
    "Gender",
    sorted(df['Gender'].unique()),
    default=sorted(df['Gender'].unique())
)

month_filter = st.sidebar.multiselect(
    "Month",
    df.sort_values('Month_Period')['Month_Name'].unique(),
    default=df.sort_values('Month_Period')['Month_Name'].unique()
)

# --------------------------------------------------
# FILTERED DATA
# --------------------------------------------------
filtered_df = df[
    (df['Product Category'].isin(category_filter)) &
    (df['Gender'].isin(gender_filter)) &
    (df['Month_Name'].isin(month_filter))
]

# --------------------------------------------------
# MONTHLY BASE (FOR GROWTH)
# --------------------------------------------------
monthly_base = (
    df[
        (df['Product Category'].isin(category_filter)) &
        (df['Gender'].isin(gender_filter))
    ]
    .groupby('Month_Period')['Total Amount']
    .sum()
    .reset_index()
    .sort_values('Month_Period')
)

monthly_base['Growth_Rate'] = monthly_base['Total Amount'].pct_change()

# --------------------------------------------------
# MONTHLY SALES (DISPLAY)
# --------------------------------------------------
monthly_sales = (
    filtered_df
    .groupby('Month_Period')['Total Amount']
    .sum()
    .reset_index()
    .sort_values('Month_Period')
)

monthly_sales['Month_Label'] = monthly_sales['Month_Period'].dt.strftime('%b %Y')

# --------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------
total_revenue = monthly_sales['Total Amount'].sum()
avg_monthly_revenue = monthly_sales['Total Amount'].mean()

previous_month_revenue = 0
next_month_revenue = 0
expected_growth = 0

previous_month_label = "N/A"
next_month_label = "N/A"

if not monthly_sales.empty:
    selected_month = monthly_sales.iloc[-1]['Month_Period']
    prev_month = selected_month - pd.DateOffset(months=1)

    prev_row = monthly_base[monthly_base['Month_Period'] == prev_month]
    curr_row = monthly_base[monthly_base['Month_Period'] == selected_month]

    if not prev_row.empty and not curr_row.empty:
        previous_month_revenue = prev_row.iloc[0]['Total Amount']
        growth_rate = curr_row.iloc[0]['Growth_Rate']

        if pd.notna(growth_rate):
            next_month_revenue = previous_month_revenue * (1 + growth_rate)
            expected_growth = growth_rate * 100

        previous_month_label = prev_month.strftime('%B %Y')
        next_month_label = (selected_month + pd.DateOffset(months=1)).strftime('%B %Y')

# --------------------------------------------------
# KPI DISPLAY
# --------------------------------------------------
st.markdown("## 📌 Key Performance Indicators")

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Revenue", f"₹{total_revenue:,.0f}")
k2.metric("Avg Monthly Revenue", f"₹{avg_monthly_revenue:,.0f}")
k3.metric("Previous Month Revenue", f"₹{previous_month_revenue:,.0f}")
k4.metric("Next Month Revenue", f"₹{next_month_revenue:,.0f}")
k5.metric("Expected Growth (%)", f"{expected_growth:.2f}%")

# --------------------------------------------------
# 📈 MONTHLY REVENUE TREND
# --------------------------------------------------
st.markdown("## 📈 Monthly Revenue Trend")

fig = px.line(
    monthly_sales,
    x="Month_Label",
    y="Total Amount",
    markers=True
)

fig.update_layout(
    xaxis_title="Month",
    yaxis_title="Revenue",
    xaxis=dict(type="category"),
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# 🧠 INSIGHTS & DECISION SUPPORT
# --------------------------------------------------
st.markdown("## 🧠 Insights & Decision Support")

if len(monthly_sales) >= 2:
    best_month = monthly_sales.loc[monthly_sales['Total Amount'].idxmax()]
    worst_month = monthly_sales.loc[monthly_sales['Total Amount'].idxmin()]

    revenue_std = monthly_sales['Total Amount'].std()
    avg_growth_rate = monthly_base['Growth_Rate'].mean() * 100

    st.markdown(f"""
- **Overall Trend:** Revenue shows a **{'positive' if avg_growth_rate > 0 else 'negative'} growth trend** with an average monthly growth of **{avg_growth_rate:.2f}%**.
- **Best Performing Month:** **{best_month['Month_Label']}** generated the highest revenue of **₹{best_month['Total Amount']:,.0f}**.
- **Lowest Performing Month:** **{worst_month['Month_Label']}** recorded the lowest revenue at **₹{worst_month['Total Amount']:,.0f}**.
- **Revenue Stability:** Monthly revenue variation (volatility) is **₹{revenue_std:,.0f}**, indicating **{'stable' if revenue_std < avg_monthly_revenue else 'fluctuating'} sales behavior**.
- **Growth Outlook:** Based on recent growth, the **next month is expected to reach ₹{next_month_revenue:,.0f}**, assuming current trends continue.
- **Business Recommendation:**  
  - Focus marketing efforts during **high-performing months**  
  - Investigate causes for dips in **low-performing months**  
  - Plan inventory based on **predicted growth direction**
""")
else:
    st.info("Not enough data to generate insights.")
