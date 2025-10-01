#!/usr/bin/env python3
"""
Ads Volume Trends Section for Monthly Dashboard
Shows in-depth volume trends and platform breakdowns
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import ast
from utils.file_io import load_monthly_ads_data
from utils.config import get_brand_column, get_brand_colors

DEFAULT_COLOR = "#BDBDBD"

def _parse_platforms(val):
    """Parse platform data from string or list format."""
    try:
        if isinstance(val, str):
            return ast.literal_eval(val)
        elif isinstance(val, list):
            return val
    except Exception:
        return []
    return []

def _present_color_map(present_brands, media_type="ads"):
    """Create color mapping for present brands."""
    brand_colors = get_brand_colors(media_type)
    m = dict(brand_colors)
    for b in present_brands:
        if b not in m:
            m[b] = DEFAULT_COLOR
    return m

def render():
    """Render the ads volume trends section."""
    st.markdown("### In-Depth View")
    
    df = load_monthly_ads_data()
    if df is None or df.empty:
        st.info("No ads data available.")
        return

    # Get selected brands from session state first
    selected_brands = st.session_state.get("selected_brands", [])
    
    brand_col = get_brand_column("ads")
    
    # Debug: Check if brand column exists
    if brand_col not in df.columns:
        st.warning(f"Brand column '{brand_col}' not found in data. Trying alternatives...")
        # Try common brand column names
        possible_brand_cols = ['page_name', 'brand', 'advertiser', 'pageName', 'advertiser_name']
        for col in possible_brand_cols:
            if col in df.columns:
                brand_col = col
                break
    
    # Use all available data - date filtering happens in analysis
    df_fixed = df.copy()
    
    # Add a 'brand' column to df_fixed for compatibility
    df_fixed['brand'] = df_fixed[brand_col]
    
    # Apply brand mapping to normalize brand names
    from utils.config import normalize_brand_name
    df_fixed['normalized_brand'] = df_fixed[brand_col].apply(lambda x: normalize_brand_name(x, "ads"))
    
    
    # Filter by selected brands from session state
    if selected_brands:
        # Filter the data to only include selected brands (using normalized names)
        df_fixed = df_fixed[df_fixed['normalized_brand'].isin(selected_brands)]
    
    # Set fixed date range based on analysis month
    from utils.config import ANALYSIS_YEAR, ANALYSIS_MONTH
    import calendar
    
    # Get the first and last day of the analysis month
    first_day = pd.Timestamp(ANALYSIS_YEAR, ANALYSIS_MONTH, 1)
    last_day = pd.Timestamp(ANALYSIS_YEAR, ANALYSIS_MONTH, calendar.monthrange(ANALYSIS_YEAR, ANALYSIS_MONTH)[1])
    

    # Ad Start Date Distribution
    st.markdown("Ad Start Date Distribution")
    _present = df_fixed["brand"].unique()
    hist = px.histogram(
        df_fixed,
        x="startDateFormatted",
        color="brand",
        nbins=60,
        barmode="overlay",
        color_discrete_map=_present_color_map(_present, "ads"),
        category_orders={"brand": list(get_brand_colors("ads").keys())},
        labels={"startDateFormatted": "Date"}
    )
    # Set fixed x-axis range to show full month
    hist.update_xaxes(range=[first_day, last_day])
    st.plotly_chart(hist, use_container_width=True)

    # Volume Trends
    st.markdown("### Volume Trends")
    tabs = st.tabs(["Total", "FACEBOOK", "INSTAGRAM", "MESSENGER", "THREADS", "AUDIENCE_NETWORK"])
    platforms = ["FACEBOOK", "INSTAGRAM", "MESSENGER", "THREADS", "AUDIENCE_NETWORK"]

    with tabs[0]:
        st.markdown("#### Reach (Total)")
        reach_trend = (
            df_fixed
            .groupby([pd.Grouper(key="startDateFormatted", freq="D"), "brand"])["reach"]
            .sum()
            .reset_index()
        )
        fig = px.line(
            reach_trend,
            x="startDateFormatted",
            y="reach",
            color="brand",
            color_discrete_map=_present_color_map(reach_trend["brand"].unique(), "ads"),
            category_orders={"brand": list(get_brand_colors("ads").keys())},
            labels={"startDateFormatted": "Date"}
        )
        # Set fixed x-axis range to show full month
        fig.update_xaxes(range=[first_day, last_day])
        st.plotly_chart(fig, use_container_width=True, key="total_reach")

        st.markdown("#### New Ads (Total)")
        ads_trend = (
            df_fixed
            .groupby([pd.Grouper(key="startDateFormatted", freq="D"), "brand"])
            .size()
            .reset_index(name="ads")
        )
        fig = px.line(
            ads_trend,
            x="startDateFormatted",
            y="ads",
            color="brand",
            color_discrete_map=_present_color_map(ads_trend["brand"].unique(), "ads"),
            category_orders={"brand": list(get_brand_colors("ads").keys())},
            labels={"startDateFormatted": "Date"}
        )
        # Set fixed x-axis range to show full month
        fig.update_xaxes(range=[first_day, last_day])
        st.plotly_chart(fig, use_container_width=True, key="total_ads")

    exploded = df_fixed.copy()
    exploded["platforms"] = exploded.get("publisherPlatform", exploded.get("platforms", None))
    exploded["platforms"] = exploded["platforms"].apply(_parse_platforms)
    exploded = exploded.explode("platforms")

    for i, platform in enumerate(platforms):
        with tabs[i + 1]:
            st.markdown(f"#### Reach – {platform}")
            pf = exploded[exploded["platforms"] == platform]
            if pf.empty:
                st.warning(f"No data available for {platform}.")
            else:
                pf_reach = (
                    pf.groupby([pd.Grouper(key="startDateFormatted", freq="D"), "brand"])["reach"]
                    .sum()
                    .reset_index()
                )
                fig = px.line(
                    pf_reach,
                    x="startDateFormatted",
                    y="reach",
                    color="brand",
                    color_discrete_map=_present_color_map(pf_reach["brand"].unique(), "ads"),
                    category_orders={"brand": list(get_brand_colors("ads").keys())},
                    labels={"startDateFormatted": "Date"}
                )
                # Set fixed x-axis range to show full month
                fig.update_xaxes(range=[first_day, last_day])
                st.plotly_chart(fig, use_container_width=True, key=f"reach_{platform}")

                st.markdown(f"#### New Ads – {platform}")
                pf_ads = (
                    pf.groupby([pd.Grouper(key="startDateFormatted", freq="D"), "brand"])
                    .size()
                    .reset_index(name="ads")
                )
                fig = px.line(
                    pf_ads,
                    x="startDateFormatted",
                    y="ads",
                    color="brand",
                    color_discrete_map=_present_color_map(pf_ads["brand"].unique(), "ads"),
                    category_orders={"brand": list(get_brand_colors("ads").keys())},
                    labels={"startDateFormatted": "Date"}
                )
                # Set fixed x-axis range to show full month
                fig.update_xaxes(range=[first_day, last_day])
                st.plotly_chart(fig, use_container_width=True, key=f"ads_{platform}")
