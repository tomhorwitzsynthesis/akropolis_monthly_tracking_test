# comprehensive_metrics.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.date_utils import get_selected_date_range
from utils.file_io import load_monthly_ads_data, load_monthly_social_media_data, load_monthly_pr_data, load_creativity_analysis, load_compos_analysis
from utils.config import BRAND_COLORS, BRANDS, normalize_brand_name, get_brand_column

def _format_metric_card(label, val, pct=None, rank_now=None, total_ranks=None):
    """Format a metric card with optional percentage change and ranking"""
    rank_color = "gray"
    if rank_now is not None and total_ranks:
        if int(rank_now) == 1:
            rank_color = "green"
        elif int(rank_now) == int(total_ranks):
            rank_color = "red"
    
    pct_color = None
    if pct is not None:
        pct_color = "green" if pct > 0 else "red" if pct < 0 else "gray"
    
    pct_html = f'<p style="margin:0; color:{pct_color};">Δ {pct:.1f}%</p>' if pct is not None else ''
    rank_html = f'<p style="margin:0; color:{rank_color};">Rank {int(rank_now)}</p>' if rank_now is not None else ''
    
    st.markdown(
        f"""
        <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
            <h5 style="margin:0;">{label}</h5>
            <h3 style="margin:5px 0;">{val}</h3>
            {pct_html}
            {rank_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

def _normalize_brand(name: str) -> str:
    """Normalize brand name for matching"""
    if not isinstance(name, str):
        return ""
    base = name.split("|")[0].strip()
    cleaned = "".join(ch.lower() if (ch.isalnum() or ch.isspace()) else " " for ch in base)
    return " ".join(cleaned.split())

def _present_color_map(present_brands):
    """Get color map for present brands"""
    m = dict(BRAND_COLORS)
    for b in present_brands:
        if b not in m:
            m[b] = "#BDBDBD"  # Default gray
    return m

def render_ads_metrics():
    """Render ads metrics section"""
    st.subheader("📣 Ad Intelligence Metrics")
    
    # Load ads data
    df_ads = load_monthly_ads_data()
    if df_ads is None or df_ads.empty:
        st.info("No ads data available.")
        return
    
    # Get the correct brand column for ads
    brand_col = get_brand_column("ads")
    if brand_col not in df_ads.columns:
        st.error(f"Brand column '{brand_col}' not found in ads data. Available columns: {list(df_ads.columns)}")
        return
    
    # Normalize brand names
    df_ads["normalized_brand"] = df_ads[brand_col].apply(lambda x: normalize_brand_name(x, "ads"))
    
    # Get selected brands
    selected_brands = st.session_state.get("selected_brands", [])
    if selected_brands:
        df_ads = df_ads[df_ads["normalized_brand"].isin(selected_brands)]
    
    if df_ads.empty:
        st.info("No ads data available for selected brands.")
        return
    
    # Calculate reach metrics using normalized brand names
    reach_totals = df_ads.groupby("normalized_brand", as_index=False)["reach"].sum()
    reach_mean = reach_totals["reach"].mean() if not reach_totals.empty else 0
    reach_ranks = reach_totals.set_index("normalized_brand")["reach"].rank(ascending=False, method="min")
    
    # Load creativity analysis
    creativity_df = load_creativity_analysis("ads")
    
    # Load compos analysis for brand strength
    compos_df = load_compos_analysis("ads")
    
    # Create brand tabs
    available_brands = sorted(df_ads["normalized_brand"].unique())
    if not available_brands:
        st.info("No brands available to display.")
        return
    
    brand_tabs = st.tabs(available_brands)
    for i, brand_name in enumerate(available_brands):
        with brand_tabs[i]:
            col1, col2, col3 = st.columns(3)
            
            # Reach metric
            with col1:
                total_reach = int(reach_totals[reach_totals["brand"] == brand_name]["reach"].sum()) if not reach_totals.empty else 0
                delta_mean_pct = ((total_reach - reach_mean) / (reach_mean if reach_mean != 0 else 1)) * 100 if reach_mean != 0 else 0
                rank_now = reach_ranks.get(brand_name, None)
                _format_metric_card(
                    label="Reach (Selected Period)",
                    val=f"{total_reach:,}",
                    pct=delta_mean_pct,
                    rank_now=rank_now,
                    total_ranks=len(reach_ranks) if len(reach_ranks) else None
                )
            
            # Brand Strength (from compos analysis)
            with col2:
                if not compos_df.empty and "Top Archetype" in compos_df.columns:
                    brand_compos = compos_df[compos_df["brand"] == brand_name]
                    if not brand_compos.empty:
                        vc = brand_compos["Top Archetype"].dropna().value_counts()
                        if not vc.empty:
                            strength = float((vc.max() / vc.sum()) * 100)
                            # Calculate rank among all brands
                            all_strengths = []
                            for b in available_brands:
                                b_compos = compos_df[compos_df["brand"] == b]
                                if not b_compos.empty:
                                    b_vc = b_compos["Top Archetype"].dropna().value_counts()
                                    if not b_vc.empty:
                                        b_strength = float((b_vc.max() / b_vc.sum()) * 100)
                                        all_strengths.append((b, b_strength))
                            
                            if all_strengths:
                                all_strengths.sort(key=lambda x: x[1], reverse=True)
                                rank_bs = next((i+1 for i, (b, _) in enumerate(all_strengths) if b == brand_name), None)
                                strength_mean = sum(s for _, s in all_strengths) / len(all_strengths)
                                delta_bs = ((strength - strength_mean) / (strength_mean if strength_mean != 0 else 1)) * 100
                                
                                _format_metric_card(
                                    label="Brand Strength",
                                    val=f"{strength:.1f}%",
                                    pct=delta_bs,
                                    rank_now=rank_bs,
                                    total_ranks=len(all_strengths)
                                )
                            else:
                                _format_metric_card("Brand Strength", "N/A")
                        else:
                            _format_metric_card("Brand Strength", "N/A")
                    else:
                        _format_metric_card("Brand Strength", "N/A")
                else:
                    _format_metric_card("Brand Strength", "N/A")
            
            # Creativity metric
            with col3:
                if not creativity_df.empty and "brand" in creativity_df.columns:
                    cre_row = creativity_df[creativity_df["brand"].astype(str).str.lower() == brand_name.lower()]
                    if not cre_row.empty and "originality_score" in cre_row.columns:
                        score = cre_row["originality_score"].iloc[0]
                        if pd.notna(score):
                            # Calculate rank among all brands
                            all_scores = []
                            for b in available_brands:
                                b_cre = creativity_df[creativity_df["brand"].astype(str).str.lower() == b.lower()]
                                if not b_cre.empty and "originality_score" in b_cre.columns:
                                    b_score = b_cre["originality_score"].iloc[0]
                                    if pd.notna(b_score):
                                        all_scores.append((b, b_score))
                            
                            if all_scores:
                                all_scores.sort(key=lambda x: x[1], reverse=True)
                                rank_cre = next((i+1 for i, (b, _) in enumerate(all_scores) if b == brand_name), None)
                                score_mean = sum(s for _, s in all_scores) / len(all_scores)
                                delta_cre = ((score - score_mean) / (score_mean if score_mean != 0 else 1)) * 100
                                
                                _format_metric_card(
                                    label="Creativity",
                                    val=f"{score:.2f}",
                                    pct=delta_cre,
                                    rank_now=rank_cre,
                                    total_ranks=len(all_scores)
                                )
                            else:
                                _format_metric_card("Creativity", "N/A")
                        else:
                            _format_metric_card("Creativity", "N/A")
                    else:
                        _format_metric_card("Creativity", "N/A")
                else:
                    _format_metric_card("Creativity", "N/A")

def render_social_media_metrics():
    """Render social media metrics section"""
    st.subheader("📱 Social Media Metrics")
    
    # Load social media data
    df_social = load_monthly_social_media_data()
    if df_social is None or df_social.empty:
        st.info("No social media data available.")
        return
    
    # Get the correct brand column for social media
    brand_col = get_brand_column("social_media")
    if brand_col not in df_social.columns:
        st.error(f"Brand column '{brand_col}' not found in social media data. Available columns: {list(df_social.columns)}")
        return
    
    # Normalize brand names
    df_social["normalized_brand"] = df_social[brand_col].apply(lambda x: normalize_brand_name(x, "social_media"))
    
    # Get selected brands
    selected_brands = st.session_state.get("selected_brands", [])
    if selected_brands:
        df_social = df_social[df_social["normalized_brand"].isin(selected_brands)]
    
    if df_social.empty:
        st.info("No social media data available for selected brands.")
        return
    
    # Calculate engagement metrics (using likes as reach proxy)
    if "likes" in df_social.columns:
        engagement_totals = df_social.groupby("normalized_brand", as_index=False)["likes"].sum()
        engagement_mean = engagement_totals["likes"].mean() if not engagement_totals.empty else 0
        engagement_ranks = engagement_totals.set_index("normalized_brand")["likes"].rank(ascending=False, method="min")
    else:
        engagement_totals = pd.DataFrame()
        engagement_mean = 0
        engagement_ranks = pd.Series()
    
    # Load creativity analysis
    creativity_df = load_creativity_analysis("social_media")
    
    # Load compos analysis for brand strength
    compos_df = load_compos_analysis("social_media")
    
    # Create brand tabs
    available_brands = sorted(df_social["normalized_brand"].unique())
    if not available_brands:
        st.info("No brands available to display.")
        return
    
    brand_tabs = st.tabs(available_brands)
    for i, brand_name in enumerate(available_brands):
        with brand_tabs[i]:
            col1, col2, col3 = st.columns(3)
            
            # Engagement metric (using likes as reach proxy)
            with col1:
                if not engagement_totals.empty:
                    total_engagement = int(engagement_totals[engagement_totals["brand"] == brand_name]["likes"].sum())
                    delta_mean_pct = ((total_engagement - engagement_mean) / (engagement_mean if engagement_mean != 0 else 1)) * 100 if engagement_mean != 0 else 0
                    rank_now = engagement_ranks.get(brand_name, None)
                    _format_metric_card(
                        label="Engagement (Likes)",
                        val=f"{total_engagement:,}",
                        pct=delta_mean_pct,
                        rank_now=rank_now,
                        total_ranks=len(engagement_ranks) if len(engagement_ranks) else None
                    )
                else:
                    _format_metric_card("Engagement", "N/A")
            
            # Brand Strength (from compos analysis)
            with col2:
                if not compos_df.empty and "Top Archetype" in compos_df.columns:
                    brand_compos = compos_df[compos_df["brand"] == brand_name]
                    if not brand_compos.empty:
                        vc = brand_compos["Top Archetype"].dropna().value_counts()
                        if not vc.empty:
                            strength = float((vc.max() / vc.sum()) * 100)
                            # Calculate rank among all brands
                            all_strengths = []
                            for b in available_brands:
                                b_compos = compos_df[compos_df["brand"] == b]
                                if not b_compos.empty:
                                    b_vc = b_compos["Top Archetype"].dropna().value_counts()
                                    if not b_vc.empty:
                                        b_strength = float((b_vc.max() / b_vc.sum()) * 100)
                                        all_strengths.append((b, b_strength))
                            
                            if all_strengths:
                                all_strengths.sort(key=lambda x: x[1], reverse=True)
                                rank_bs = next((i+1 for i, (b, _) in enumerate(all_strengths) if b == brand_name), None)
                                strength_mean = sum(s for _, s in all_strengths) / len(all_strengths)
                                delta_bs = ((strength - strength_mean) / (strength_mean if strength_mean != 0 else 1)) * 100
                                
                                _format_metric_card(
                                    label="Brand Strength",
                                    val=f"{strength:.1f}%",
                                    pct=delta_bs,
                                    rank_now=rank_bs,
                                    total_ranks=len(all_strengths)
                                )
                            else:
                                _format_metric_card("Brand Strength", "N/A")
                        else:
                            _format_metric_card("Brand Strength", "N/A")
                    else:
                        _format_metric_card("Brand Strength", "N/A")
                else:
                    _format_metric_card("Brand Strength", "N/A")
            
            # Creativity metric
            with col3:
                if not creativity_df.empty and "brand" in creativity_df.columns:
                    cre_row = creativity_df[creativity_df["brand"].astype(str).str.lower() == brand_name.lower()]
                    if not cre_row.empty and "originality_score" in cre_row.columns:
                        score = cre_row["originality_score"].iloc[0]
                        if pd.notna(score):
                            # Calculate rank among all brands
                            all_scores = []
                            for b in available_brands:
                                b_cre = creativity_df[creativity_df["brand"].astype(str).str.lower() == b.lower()]
                                if not b_cre.empty and "originality_score" in b_cre.columns:
                                    b_score = b_cre["originality_score"].iloc[0]
                                    if pd.notna(b_score):
                                        all_scores.append((b, b_score))
                            
                            if all_scores:
                                all_scores.sort(key=lambda x: x[1], reverse=True)
                                rank_cre = next((i+1 for i, (b, _) in enumerate(all_scores) if b == brand_name), None)
                                score_mean = sum(s for _, s in all_scores) / len(all_scores)
                                delta_cre = ((score - score_mean) / (score_mean if score_mean != 0 else 1)) * 100
                                
                                _format_metric_card(
                                    label="Creativity",
                                    val=f"{score:.2f}",
                                    pct=delta_cre,
                                    rank_now=rank_cre,
                                    total_ranks=len(all_scores)
                                )
                            else:
                                _format_metric_card("Creativity", "N/A")
                        else:
                            _format_metric_card("Creativity", "N/A")
                    else:
                        _format_metric_card("Creativity", "N/A")
                else:
                    _format_metric_card("Creativity", "N/A")

def render_pr_metrics():
    """Render PR metrics section"""
    st.subheader("📰 PR Metrics")
    
    # Load PR data
    df_pr = load_monthly_pr_data()
    if df_pr is None or df_pr.empty:
        st.info("No PR data available.")
        return
    
    # Get the correct brand column for PR
    brand_col = get_brand_column("pr")
    if brand_col not in df_pr.columns:
        st.error(f"Brand column '{brand_col}' not found in PR data. Available columns: {list(df_pr.columns)}")
        return
    
    # Normalize brand names
    df_pr["normalized_brand"] = df_pr[brand_col].apply(lambda x: normalize_brand_name(x, "pr"))
    
    # Get selected brands
    selected_brands = st.session_state.get("selected_brands", [])
    if selected_brands:
        df_pr = df_pr[df_pr["normalized_brand"].isin(selected_brands)]
    
    if df_pr.empty:
        st.info("No PR data available for selected brands.")
        return
    
    # Calculate impressions metrics (using Impressions as reach proxy)
    if "Impressions" in df_pr.columns:
        impressions_totals = df_pr.groupby("normalized_brand", as_index=False)["Impressions"].sum()
        impressions_mean = impressions_totals["Impressions"].mean() if not impressions_totals.empty else 0
        impressions_ranks = impressions_totals.set_index("normalized_brand")["Impressions"].rank(ascending=False, method="min")
    else:
        impressions_totals = pd.DataFrame()
        impressions_mean = 0
        impressions_ranks = pd.Series()
    
    # Load creativity analysis
    creativity_df = load_creativity_analysis("pr")
    
    # Load compos analysis for brand strength
    compos_df = load_compos_analysis("pr")
    
    # Create brand tabs
    available_brands = sorted(df_pr["normalized_brand"].unique())
    if not available_brands:
        st.info("No brands available to display.")
        return
    
    brand_tabs = st.tabs(available_brands)
    for i, brand_name in enumerate(available_brands):
        with brand_tabs[i]:
            col1, col2, col3 = st.columns(3)
            
            # Impressions metric (using Impressions as reach proxy)
            with col1:
                if not impressions_totals.empty:
                    total_impressions = int(impressions_totals[impressions_totals["company"] == brand_name]["Impressions"].sum())
                    delta_mean_pct = ((total_impressions - impressions_mean) / (impressions_mean if impressions_mean != 0 else 1)) * 100 if impressions_mean != 0 else 0
                    rank_now = impressions_ranks.get(brand_name, None)
                    _format_metric_card(
                        label="Impressions (Reach)",
                        val=f"{total_impressions:,}",
                        pct=delta_mean_pct,
                        rank_now=rank_now,
                        total_ranks=len(impressions_ranks) if len(impressions_ranks) else None
                    )
                else:
                    _format_metric_card("Impressions", "N/A")
            
            # Brand Strength (from compos analysis)
            with col2:
                if not compos_df.empty and "Top Archetype" in compos_df.columns:
                    brand_compos = compos_df[compos_df["brand"] == brand_name]
                    if not brand_compos.empty:
                        vc = brand_compos["Top Archetype"].dropna().value_counts()
                        if not vc.empty:
                            strength = float((vc.max() / vc.sum()) * 100)
                            # Calculate rank among all brands
                            all_strengths = []
                            for b in available_brands:
                                b_compos = compos_df[compos_df["brand"] == b]
                                if not b_compos.empty:
                                    b_vc = b_compos["Top Archetype"].dropna().value_counts()
                                    if not b_vc.empty:
                                        b_strength = float((b_vc.max() / b_vc.sum()) * 100)
                                        all_strengths.append((b, b_strength))
                            
                            if all_strengths:
                                all_strengths.sort(key=lambda x: x[1], reverse=True)
                                rank_bs = next((i+1 for i, (b, _) in enumerate(all_strengths) if b == brand_name), None)
                                strength_mean = sum(s for _, s in all_strengths) / len(all_strengths)
                                delta_bs = ((strength - strength_mean) / (strength_mean if strength_mean != 0 else 1)) * 100
                                
                                _format_metric_card(
                                    label="Brand Strength",
                                    val=f"{strength:.1f}%",
                                    pct=delta_bs,
                                    rank_now=rank_bs,
                                    total_ranks=len(all_strengths)
                                )
                            else:
                                _format_metric_card("Brand Strength", "N/A")
                        else:
                            _format_metric_card("Brand Strength", "N/A")
                    else:
                        _format_metric_card("Brand Strength", "N/A")
                else:
                    _format_metric_card("Brand Strength", "N/A")
            
            # Creativity metric
            with col3:
                if not creativity_df.empty and "brand" in creativity_df.columns:
                    cre_row = creativity_df[creativity_df["brand"].astype(str).str.lower() == brand_name.lower()]
                    if not cre_row.empty and "originality_score" in cre_row.columns:
                        score = cre_row["originality_score"].iloc[0]
                        if pd.notna(score):
                            # Calculate rank among all brands
                            all_scores = []
                            for b in available_brands:
                                b_cre = creativity_df[creativity_df["brand"].astype(str).str.lower() == b.lower()]
                                if not b_cre.empty and "originality_score" in b_cre.columns:
                                    b_score = b_cre["originality_score"].iloc[0]
                                    if pd.notna(b_score):
                                        all_scores.append((b, b_score))
                            
                            if all_scores:
                                all_scores.sort(key=lambda x: x[1], reverse=True)
                                rank_cre = next((i+1 for i, (b, _) in enumerate(all_scores) if b == brand_name), None)
                                score_mean = sum(s for _, s in all_scores) / len(all_scores)
                                delta_cre = ((score - score_mean) / (score_mean if score_mean != 0 else 1)) * 100
                                
                                _format_metric_card(
                                    label="Creativity",
                                    val=f"{score:.2f}",
                                    pct=delta_cre,
                                    rank_now=rank_cre,
                                    total_ranks=len(all_scores)
                                )
                            else:
                                _format_metric_card("Creativity", "N/A")
                        else:
                            _format_metric_card("Creativity", "N/A")
                    else:
                        _format_metric_card("Creativity", "N/A")
                else:
                    _format_metric_card("Creativity", "N/A")

def render():
    """Main render function for comprehensive metrics"""
    st.title("📊 Comprehensive Metrics Dashboard")
    
    # Show selected date range
    try:
        start_date, end_date = get_selected_date_range()
        st.caption(f"Analysis period: {start_date.strftime('%B %Y')} - {end_date.strftime('%B %Y')}")
    except:
        st.caption("Select date range in sidebar")
    
    # Show selected brands
    selected_brands = st.session_state.get("selected_brands", [])
    if selected_brands:
        st.caption(f"Selected brands: {', '.join(selected_brands)}")
    
    # Create tabs for different media types
    tab1, tab2, tab3 = st.tabs(["📣 Ads", "📱 Social Media", "📰 PR"])
    
    with tab1:
        render_ads_metrics()
    
    with tab2:
        render_social_media_metrics()
    
    with tab3:
        render_pr_metrics()
