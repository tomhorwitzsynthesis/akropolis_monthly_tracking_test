# sections/audience_affinity.py

import streamlit as st
import pandas as pd
from utils.config import BRAND_NAME_MAPPING
from utils.file_io import load_audience_affinity_outputs

def format_percentage(series):
    return series.round(0).astype(int).astype(str) + "%"

def prettify_column(col):
    # Remove '_%High' and prettify
    col = col.replace("_%High", "")
    col = col.replace("_", " ")
    
    # New audience affinity column mappings
    col = col.replace("Family Kids Products", "Kids' Products Relevance")
    col = col.replace("Family Kids Events", "Kids' Events & Activities")
    col = col.replace("Family Household Discounts", "Household Savings & Discounts")
    col = col.replace("Young Tech Gaming", "Technology & Gaming Relevance")
    col = col.replace("Young Fashion Style", "Fashion & Style for Young Adults")
    col = col.replace("Young Social Events", "Social & Youth-Oriented Events")
    col = col.replace("Store Business Growth", "Business Growth Opportunities")
    col = col.replace("Store Partnership CoMarketing", "Partnership & Co-Marketing Potential")
    col = col.replace("Store Market Insights", "Market Insights & Strategic Positioning")
    col = col.replace("Experience Accessibility Comfort", "Accessibility & Comfort")
    col = col.replace("Experience Ambience Design", "Ambience & Design Quality")
    col = col.replace("Experience Mallwide Events", "Mall-Wide Events & Services")
    
    # Legacy mappings (commented out but kept for reference)
    # col = col.replace("Customer", "Customer")
    # col = col.replace("Talent", "Talent")
    # col = col.replace("Investor", "Investor")
    # col = col.replace("Employer Branding", "Employer Branding")
    # col = col.replace("Career Growth", "Career Growth")
    # col = col.replace("Market Impact", "Market Impact")
    # col = col.replace("Problem Solving", "Problem Solving")
    # col = col.replace("Clarity Offerings", "Clarity of Offerings")
    # col = col.replace("Innovation", "Innovation")
    # col = col.replace("Expertise", "Expertise")
    # col = col.replace("Industry Relevance", "Industry Relevance")
    # col = col.replace("Long Term", "Long-Term Vision")
    # col = col.replace("Positioning", "Positioning")
    # col = col.replace("Market Influence", "Market Influence")
    
    return col

def render():
    try:
        affinity_data = load_audience_affinity_outputs()
        if affinity_data is None:
            st.error("❌ No audience affinity data available.")
            return

        summary_df = affinity_data.get("summary_df")
        gpt_summary = affinity_data.get("gpt_summary")

        if summary_df is None or summary_df.empty:
            st.error("❌ No summary data available.")
            return

        summary_df["Brand"] = summary_df["Brand"].map(
            lambda x: BRAND_NAME_MAPPING.get(x, x)
        )

        view_option = st.selectbox(
            "Select View",
            ["Audience Averages", "Families & Household Shoppers", "Young Adults – Tech & Fashion", "Store Owners & Business Partners", "Shopping Experience & Mall Environment"]
        )

        st.subheader(f"🔍 {view_option} View")

        # Overview text
        st.markdown(
            "Percentages below represent the share of respondents who rated each aspect in the top 2 boxes (6 or 7) on a 1–7 scale."
        )

        audience_map = {
            "Families & Household Shoppers": {
                "pct_col": "Families & Household Shoppers_%High",
                "detail_cols": ["Family_Kids_Products", "Family_Kids_Events", "Family_Household_Discounts"]
            },
            "Young Adults – Tech & Fashion": {
                "pct_col": "Young Adults – Tech & Fashion_%High",
                "detail_cols": ["Young_Tech_Gaming", "Young_Fashion_Style", "Young_Social_Events"]
            },
            "Store Owners & Business Partners": {
                "pct_col": "Store Owners & Business Partners_%High",
                "detail_cols": ["Store_Business_Growth", "Store_Partnership_CoMarketing", "Store_Market_Insights"]
            },
            "Shopping Experience & Mall Environment": {
                "pct_col": "Shopping Experience & Mall Environment_%High",
                "detail_cols": ["Experience_Accessibility_Comfort", "Experience_Ambience_Design", "Experience_Mallwide_Events"]
            }
        }

        if view_option == "Audience Averages":
            cols_to_show = [col for col in summary_df.columns if col.endswith("_%High")]
            display_df = summary_df[["Brand"] + cols_to_show].copy()
            # Format all percentage columns
            for col in cols_to_show:
                display_df[col] = format_percentage(display_df[col])
        else:
            mapping = audience_map.get(view_option, {})
            pct_col = mapping.get("pct_col")
            detail_cols = mapping.get("detail_cols", [])
            cols_to_show = [pct_col] + detail_cols
            display_df = summary_df[["Brand"] + cols_to_show].copy()
            display_df = display_df.rename(columns={pct_col: "Average Value"})
            # Format all percentage columns (including detail columns)
            for col in ["Average Value"] + detail_cols:
                display_df[col] = format_percentage(display_df[col])

        # Prettify column names (remove % High)
        display_df.columns = [prettify_column(col) if col != "Brand" else "Brand" for col in display_df.columns]

        st.dataframe(display_df.set_index("Brand"), use_container_width=True)

        # GPT Summary
        if gpt_summary:
            st.markdown("---")
            st.subheader("🧠 Summary")
            st.markdown(gpt_summary)

    except Exception as e:
        st.error("🚨 Failed to load audience affinity data.")
        st.exception(e)
