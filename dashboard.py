"""
NovaMart Sales Dashboard — Version 1: Category & Sub-Category Sales Explorer
Project 2 (Streamlit) — Virtual OJT Programme, Semester 2
"""
from pathlib import Path
import pandas as pd
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

@st.cache_data
def load_data():
    base_dir = Path("monthly_orders/novamart_clean.csv").resolve().parent
    csv_file = base_dir / "monthly_orders" / "novamart_clean.csv"

    st.write("Current folder:", base_dir)
    st.write("CSV path:", csv_file)
    st.write("CSV exists:", csv_file.exists())

    if not csv_file.exists():
        st.stop()

    df = pd.read_csv(
        csv_file,
        parse_dates=["order_date", "ship_date"]
    )

    return df

df = load_data()
# ----------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------
st.sidebar.header("Filters")

categories = sorted(df["category"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Category", options=categories, default=categories
)

months = sorted(df["order_month"].dropna().unique())
selected_months = st.sidebar.select_slider(
    "Month range",
    options=months,
    value=(months[0], months[-1]),
)

# Apply filters
mask = (
    df["category"].isin(selected_categories)
    & (df["order_month"] >= selected_months[0])
    & (df["order_month"] <= selected_months[1])
)
filtered = df.loc[mask].copy()

if filtered.empty:
    st.warning("No orders match the current filters. Widen your selection.")
    st.stop()

# ----------------------------------------------------------------------
# KPI cards
# ----------------------------------------------------------------------
total_sales = filtered["sales"].sum()
total_orders = filtered["order_id"].nunique()
avg_order_value = total_sales / total_orders if total_orders else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Sales", f"${total_sales:,.2f}")
col2.metric("Total Orders", f"{total_orders:,}")
col3.metric("Average Order Value", f"${avg_order_value:,.2f}")

st.divider()

# ----------------------------------------------------------------------
# NumPy alert — flag orders above the 90th percentile of sales
# ----------------------------------------------------------------------
p90 = np.percentile(filtered["sales"], 90)
high_value_orders = filtered[filtered["sales"] > p90]

st.success(
    f"{len(high_value_orders)} orders are above the 90th percentile "
    f"of sales value (> ${p90:,.2f}) in the current filter selection."
)

st.divider()

# ----------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Sales by Category")
    sales_by_category = (
        filtered.groupby("category")["sales"].sum().sort_values(ascending=False)
    )
    st.bar_chart(sales_by_category)

with right:
    st.subheader("Top 10 Sub-Categories by Sales")
    top_subcats = (
        filtered.groupby("sub_category")["sales"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    fig, ax = plt.subplots()
    top_subcats.sort_values().plot(kind="barh", ax=ax, color="#4C72B0")
    ax.set_xlabel("Sales ($)")
    ax.set_ylabel("Sub-Category")
    st.pyplot(fig)

st.subheader("Monthly Sales Trend")
monthly_sales = filtered.groupby("order_month")["sales"].sum().sort_index()
st.line_chart(monthly_sales)

st.subheader("Sub-Category Sales & Profit")
subcat_table = (
    filtered.groupby("sub_category")[["sales", "profit"]]
    .sum()
    .sort_values("sales", ascending=False)
    .reset_index()
)
st.dataframe(subcat_table, use_container_width=True)

st.divider()

# ----------------------------------------------------------------------
# Download filtered data
# ----------------------------------------------------------------------
csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download filtered data as CSV",
    data=csv_bytes,
    file_name="novamart_filtered.csv",
    mime="text/csv",
)