#!/usr/bin/env python3
"""
Social Media Clusters Analysis for Monthly Dashboard
Shows top 3 clusters by engagement for the selected month
"""

import streamlit as st
import pandas as pd
from utils.file_io import load_monthly_social_media_data, get_selected_date_range
from utils.config import normalize_brand_name, get_brand_column

def create_cluster_card_with_examples(cluster_name, posts_count, total_engagement, examples):
    """Create a card-style display for a cluster with examples"""
    examples_html = ""
    if not examples.empty:
        examples_html = "<div style='margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;'>"
        examples_html += "<p style='margin: 0 0 5px 0; color: #888; font-size: 12px; font-weight: bold;'>Examples:</p>"
        
        for idx, row in examples.iterrows():
            summary = str(row["post_summary"]) if "post_summary" in row else str(row.get("content", ""))
            source_url = row["source_url"] if pd.notna(row.get("source_url")) else None
            
            # Truncate long summaries
            truncated_summary = summary[:150] + "..." if len(summary) > 150 else summary
            
            # Create clickable link if source_url is available
            if source_url and source_url != "":
                examples_html += f'<p style="margin: 2px 0; color: #666; font-size: 12px; font-style: italic;">• {truncated_summary} <a href="{source_url}" target="_blank" style="color: #007bff; text-decoration: none; font-size: 11px; margin-left: 5px;">🔗 View Post</a></p>'
            else:
                examples_html += f'<p style="margin: 2px 0; color: #666; font-size: 12px; font-style: italic;">• {truncated_summary}</p>'
        
        examples_html += "</div>"
    
    return f"""
    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; background-color: #f9f9f9;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="flex: 1;">
                <h4 style="margin: 0; color: #333;">{cluster_name}</h4>
                <p style="margin: 5px 0; color: #666; font-size: 14px;">{posts_count} posts</p>
                {examples_html}
            </div>
            <div style="text-align: right; margin-left: 15px;">
                <h3 style="margin: 0; color: #2E8B57;">{int(total_engagement):,}</h3>
                <p style="margin: 0; color: #666; font-size: 12px;">engagement</p>
            </div>
        </div>
    </div>
    """

def render():
    """Render the Top 3 Clusters by Engagement section"""
    st.subheader("🏆 Top 3 Clusters by Engagement")
    
    # Load social media data
    df = load_monthly_social_media_data()
    
    if df is None or df.empty:
        st.info("No social media data found.")
        return
    
    # Filter by date range - use the selected month
    start_date, end_date = get_selected_date_range()
    
    # Convert timezone-naive dates to UTC to match the data
    if df['date'].dt.tz is not None:
        start_date = pd.Timestamp(start_date).tz_localize('UTC')
        end_date = pd.Timestamp(end_date).tz_localize('UTC')
    
    df_filtered = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    # Always normalize company names for display
    brand_col = get_brand_column("social_media")
    df_filtered['normalized_company'] = df_filtered[brand_col].apply(lambda x: normalize_brand_name(x, "social_media"))
    
    # Get selected brands from session state and filter
    selected_brands = st.session_state.get("selected_brands", [])
    
    if selected_brands:
        df_filtered = df_filtered[df_filtered['normalized_company'].isin(selected_brands)]
    
    if df_filtered.empty:
        st.warning("No data available for the selected period.")
        return

    # Filter for posts with cluster_1 data
    df_with_clusters = df_filtered[df_filtered["cluster_1"].notna() & (df_filtered["cluster_1"] != "")]
    
    if df_with_clusters.empty:
        st.info("No cluster data available for the selected period.")
        return
    
    # Calculate engagement using the same logic as data loading
    if "likes" in df_with_clusters.columns and "num_comments" in df_with_clusters.columns and "num_shares" in df_with_clusters.columns:
        # Calculate total engagement: likes + comments*3 + shares*5
        likes = pd.to_numeric(df_with_clusters["likes"], errors="coerce").fillna(0)
        comments = pd.to_numeric(df_with_clusters["num_comments"], errors="coerce").fillna(0)
        shares = pd.to_numeric(df_with_clusters["num_shares"], errors="coerce").fillna(0)
        df_with_clusters["calculated_engagement"] = likes + comments * 3 + shares * 5
    elif "total_engagement" in df_with_clusters.columns:
        df_with_clusters["calculated_engagement"] = pd.to_numeric(df_with_clusters["total_engagement"], errors="coerce").fillna(0)
    else:
        df_with_clusters["calculated_engagement"] = 0

    # Group by cluster only for overall view (aggregate across all brands)
    cluster_rollup_overall = (
        df_with_clusters.groupby(["cluster_1"], as_index=False)
        .agg(
            posts_count=("post_id", "nunique"),
            total_engagement=("calculated_engagement", "sum")
        )
    )
    
    # Group by cluster and brand for individual brand views
    cluster_rollup_by_brand = (
        df_with_clusters.groupby(["cluster_1", "normalized_company"], as_index=False)
        .agg(
            posts_count=("post_id", "nunique"),
            total_engagement=("calculated_engagement", "sum")
        )
    )
    
    if cluster_rollup_overall.empty:
        st.info("No cluster data available after processing.")
        return
    
    brands_with_clusters = sorted(cluster_rollup_by_brand["normalized_company"].unique())
    cluster_tabs = st.tabs(["Overall"] + brands_with_clusters)
    
    def top3_clusters(d):
        return d.sort_values("total_engagement", ascending=False).head(3).reset_index(drop=True)
    
    with cluster_tabs[0]:
        top3_clusters_overall = top3_clusters(cluster_rollup_overall)
        if top3_clusters_overall.empty:
            st.info("No cluster data available overall.")
        else:
            for idx, row in top3_clusters_overall.iterrows():
                # Get examples for this cluster (using post_summary and source_url)
                examples = (
                    df_with_clusters[df_with_clusters["cluster_1"] == row["cluster_1"]]
                    [["post_summary", "source_url", "content"]]
                    .dropna(subset=["post_summary"])
                    .head(2)
                )
                st.markdown(create_cluster_card_with_examples(
                    row["cluster_1"], 
                    row["posts_count"], 
                    row["total_engagement"], 
                    examples
                ), unsafe_allow_html=True)
    
    for i, b in enumerate(brands_with_clusters, start=1):
        with cluster_tabs[i]:
            top3_clusters_brand = top3_clusters(cluster_rollup_by_brand[cluster_rollup_by_brand["normalized_company"] == b])
            if top3_clusters_brand.empty:
                st.info(f"No cluster data available for {b}.")
            else:
                for idx, row in top3_clusters_brand.iterrows():
                    # Get examples for this cluster and brand (using post_summary and source_url)
                    examples = (
                        df_with_clusters[(df_with_clusters["cluster_1"] == row["cluster_1"]) & (df_with_clusters["normalized_company"] == b)]
                        [["post_summary", "source_url", "content"]]
                        .dropna(subset=["post_summary"])
                        .head(2)
                    )
                    st.markdown(create_cluster_card_with_examples(
                        row["cluster_1"], 
                        row["posts_count"], 
                        row["total_engagement"], 
                        examples
                    ), unsafe_allow_html=True)
