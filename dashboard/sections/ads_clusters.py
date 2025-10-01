#!/usr/bin/env python3
"""
Ads Clusters Analysis for Monthly Dashboard
Shows top 3 clusters by reach for the selected month
"""

import streamlit as st
import pandas as pd
from utils.file_io import load_monthly_ads_data, get_selected_date_range
from utils.config import normalize_brand_name, get_brand_column

def create_cluster_card_with_examples(cluster_name, ads_count, total_reach, examples):
    """Create a card-style display for a cluster with examples"""
    examples_html = ""
    if not examples.empty:
        examples_html = "<div style='margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;'>"
        examples_html += "<p style='margin: 0 0 5px 0; color: #888; font-size: 12px; font-weight: bold;'>Examples:</p>"
        
        for idx, row in examples.iterrows():
            summary = str(row["ad_summary"]) if "ad_summary" in row else str(row.get("snapshot/body/text", ""))
            source_url = row["source_url"] if pd.notna(row.get("source_url")) else None
            
            # Truncate long summaries
            truncated_summary = summary[:150] + "..." if len(summary) > 150 else summary
            
            # Create clickable link if source_url is available
            if source_url and source_url != "":
                examples_html += f'<p style="margin: 2px 0; color: #666; font-size: 12px; font-style: italic;">• {truncated_summary} <a href="{source_url}" target="_blank" style="color: #007bff; text-decoration: none; font-size: 11px; margin-left: 5px;">🔗 View Ad</a></p>'
            else:
                examples_html += f'<p style="margin: 2px 0; color: #666; font-size: 12px; font-style: italic;">• {truncated_summary}</p>'
        
        examples_html += "</div>"
    
    return f"""
    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; background-color: #f9f9f9;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="flex: 1;">
                <h4 style="margin: 0; color: #333;">{cluster_name}</h4>
                <p style="margin: 5px 0; color: #666; font-size: 14px;">{ads_count} ads</p>
                {examples_html}
            </div>
            <div style="text-align: right; margin-left: 15px;">
                <h3 style="margin: 0; color: #2E8B57;">{int(total_reach):,}</h3>
                <p style="margin: 0; color: #666; font-size: 12px;">reach</p>
            </div>
        </div>
    </div>
    """

def render():
    """Render the Top 3 Clusters by Reach section"""
    st.subheader("🏆 Top 3 Clusters by Reach")
    
    # Load ads data
    df = load_monthly_ads_data()
    
    if df is None or df.empty:
        st.info("No ads data found.")
        return
    
    # Filter by date range - use the selected month
    start_date, end_date = get_selected_date_range()
    
    # Convert timezone-naive dates to UTC to match the data
    if df['startDateFormatted'].dt.tz is not None:
        start_date = pd.Timestamp(start_date).tz_localize('UTC')
        end_date = pd.Timestamp(end_date).tz_localize('UTC')
    
    df_filtered = df[(df['startDateFormatted'] >= start_date) & (df['startDateFormatted'] <= end_date)]
    
    # Always normalize company names for display
    brand_col = get_brand_column("ads")
    df_filtered['normalized_brand'] = df_filtered[brand_col].apply(lambda x: normalize_brand_name(x, "ads"))
    
    # Get selected brands from session state and filter
    selected_brands = st.session_state.get("selected_brands", [])
    
    if selected_brands:
        df_filtered = df_filtered[df_filtered['normalized_brand'].isin(selected_brands)]
    
    if df_filtered.empty:
        st.warning("No data available for the selected period.")
        return

    # Filter for ads with cluster_1 data
    df_with_clusters = df_filtered[df_filtered["cluster_1"].notna() & (df_filtered["cluster_1"] != "")]
    
    if df_with_clusters.empty:
        st.info("No cluster data available for the selected period.")
        return
    
    # Calculate reach using the same logic as data loading
    if "ad_details/aaa_info/eu_total_reach" in df_with_clusters.columns:
        df_with_clusters["calculated_reach"] = pd.to_numeric(df_with_clusters["ad_details/aaa_info/eu_total_reach"], errors="coerce").fillna(0)
    elif "reach" in df_with_clusters.columns:
        df_with_clusters["calculated_reach"] = pd.to_numeric(df_with_clusters["reach"], errors="coerce").fillna(0)
    else:
        df_with_clusters["calculated_reach"] = 0

    # Group by cluster only for overall view (aggregate across all brands)
    cluster_rollup_overall = (
        df_with_clusters.groupby(["cluster_1"], as_index=False)
        .agg(
            ads_count=("adArchiveID", "nunique"),
            total_reach=("calculated_reach", "sum")
        )
    )
    
    # Group by cluster and brand for individual brand views
    cluster_rollup_by_brand = (
        df_with_clusters.groupby(["cluster_1", "normalized_brand"], as_index=False)
        .agg(
            ads_count=("adArchiveID", "nunique"),
            total_reach=("calculated_reach", "sum")
        )
    )
    
    if cluster_rollup_overall.empty:
        st.info("No cluster data available after processing.")
        return
    
    brands_with_clusters = sorted(cluster_rollup_by_brand["normalized_brand"].unique())
    cluster_tabs = st.tabs(["Overall"] + brands_with_clusters)
    
    def top3_clusters(d):
        return d.sort_values("total_reach", ascending=False).head(3).reset_index(drop=True)
    
    with cluster_tabs[0]:
        top3_clusters_overall = top3_clusters(cluster_rollup_overall)
        if top3_clusters_overall.empty:
            st.info("No cluster data available overall.")
        else:
            for idx, row in top3_clusters_overall.iterrows():
                # Get examples for this cluster (using ad_summary and source_url)
                examples = (
                    df_with_clusters[df_with_clusters["cluster_1"] == row["cluster_1"]]
                    [["ad_summary", "source_url", "snapshot/body/text"]]
                    .dropna(subset=["ad_summary"])
                    .head(2)
                )
                st.markdown(create_cluster_card_with_examples(
                    row["cluster_1"], 
                    row["ads_count"], 
                    row["total_reach"], 
                    examples
                ), unsafe_allow_html=True)
    
    for i, b in enumerate(brands_with_clusters, start=1):
        with cluster_tabs[i]:
            top3_clusters_brand = top3_clusters(cluster_rollup_by_brand[cluster_rollup_by_brand["normalized_brand"] == b])
            if top3_clusters_brand.empty:
                st.info(f"No cluster data available for {b}.")
            else:
                for idx, row in top3_clusters_brand.iterrows():
                    # Get examples for this cluster and brand (using ad_summary and source_url)
                    examples = (
                        df_with_clusters[(df_with_clusters["cluster_1"] == row["cluster_1"]) & (df_with_clusters["normalized_brand"] == b)]
                        [["ad_summary", "source_url", "snapshot/body/text"]]
                        .dropna(subset=["ad_summary"])
                        .head(2)
                    )
                    st.markdown(create_cluster_card_with_examples(
                        row["cluster_1"], 
                        row["ads_count"], 
                        row["total_reach"], 
                        examples
                    ), unsafe_allow_html=True)
