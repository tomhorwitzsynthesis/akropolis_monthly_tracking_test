#!/usr/bin/env python3
"""
Ads Volume Share Section for Monthly Dashboard
Shows pie charts for ad count and reach share by brand
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.file_io import load_monthly_ads_data, get_selected_date_range
from utils.config import get_brand_column, get_brand_colors

DEFAULT_COLOR = "#BDBDBD"  # used for any brand not in brand colors

def render():
    """Render the ads volume share section with pie charts."""
    st.markdown("### Ad Volume Share (Selected Months)")
    
    df = load_monthly_ads_data()
    if df is None or df.empty:
        st.info("No ads data available.")
        return

    # Use global selected date range
    start_date, end_date = get_selected_date_range()
    
    # Get the correct brand column name
    brand_col = get_brand_column("ads")
    
    # Debug: Show available columns and brand column
    
    # Check if the brand column exists, if not try common alternatives
    if brand_col not in df.columns:
        st.warning(f"Brand column '{brand_col}' not found in data. Trying alternatives...")
        # Try common brand column names
        possible_brand_cols = ['page_name', 'brand', 'advertiser', 'pageName', 'advertiser_name']
        brand_col = None
        for col in possible_brand_cols:
            if col in df.columns:
                brand_col = col
                break
        
        if brand_col is None:
            st.error("No suitable brand column found in ads data!")
            return
    
    # Filter data to selected date range
    if "date" in df.columns:
        df_filtered = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] < pd.to_datetime(end_date))].copy()
    elif "startDateFormatted" in df.columns:
        df_filtered = df[(df['startDateFormatted'] >= pd.to_datetime(start_date)) & (df['startDateFormatted'] < pd.to_datetime(end_date))].copy()
    else:
        df_filtered = df.copy()
    
    # Debug: Show unique brands in data with counts
    unique_brands = df_filtered[brand_col].unique() if brand_col in df_filtered.columns else []
    brand_counts = df_filtered[brand_col].value_counts() if brand_col in df_filtered.columns else pd.Series()
    
    # Apply brand mapping to normalize brand names
    from utils.config import normalize_brand_name
    df_filtered['normalized_brand'] = df_filtered[brand_col].apply(lambda x: normalize_brand_name(x, "ads"))
    
    # Filter by selected brands from session state
    selected_brands = st.session_state.get("selected_brands", [])
    
    if selected_brands:
        # Filter the data to only include selected brands (using normalized names)
        df_filtered = df_filtered[df_filtered['normalized_brand'].isin(selected_brands)]
        filtered_brands = df_filtered[brand_col].unique() if brand_col in df_filtered.columns else []

    sub_tabs = st.tabs(["Number of Ads", "Reach"])
    
    with sub_tabs[0]:
        ad_counts = df_filtered[brand_col].value_counts().reset_index()
        if not ad_counts.empty:
            ad_counts.columns = ["brand", "count"]

            # Build a color map that covers all present brands (unknowns -> gray)
            ads_brand_colors = get_brand_colors("ads")
            color_map_ads = {**ads_brand_colors}
            for b in ad_counts["brand"].unique():
                color_map_ads.setdefault(b, DEFAULT_COLOR)

            fig = px.pie(
                ad_counts,
                values="count",
                names="brand",
                title=f'Ad Count Share – {start_date.strftime("%b %Y")} to {end_date.strftime("%b %Y")}',
                color="brand",
                color_discrete_map=color_map_ads,
                category_orders={"brand": list(ads_brand_colors.keys())},
            )
            st.plotly_chart(fig, use_container_width=True, key="pie_ads_selected")
        else:
            st.info("No ads in selected months.")

    with sub_tabs[1]:
        reach_totals = df_filtered.groupby(brand_col, as_index=False)["reach"].sum()
        if not reach_totals.empty:
            # Rename the brand column to 'brand' for consistency
            reach_totals = reach_totals.rename(columns={brand_col: "brand"})

            ads_brand_colors = get_brand_colors("ads")
            color_map_reach = {**ads_brand_colors}
            for b in reach_totals["brand"].unique():
                color_map_reach.setdefault(b, DEFAULT_COLOR)

            fig = px.pie(
                reach_totals,
                values="reach",
                names="brand",
                title=f'Reach Share – {start_date.strftime("%b %Y")} to {end_date.strftime("%b %Y")}',
                color="brand",
                color_discrete_map=color_map_reach,
                category_orders={"brand": list(ads_brand_colors.keys())},
            )
            st.plotly_chart(fig, use_container_width=True, key="pie_reach_selected")
        else:
            st.info("No reach data in selected months.")
