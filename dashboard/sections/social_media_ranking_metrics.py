#!/usr/bin/env python3
"""
Social Media Ranking Metrics for Monthly Dashboard
Shows top 3 metrics: Engagement, Brand Strength, Creativity
"""

import streamlit as st
import pandas as pd
import os
import glob
from utils.file_io import load_monthly_social_media_data, get_selected_date_range, load_creativity_analysis, load_compos_analysis
from utils.config import normalize_brand_name, get_brand_column

def _format_simple_metric_card(label, val, pct=None, rank_now=None, total_ranks=None):
    """Format a metric card with optional percentage change and ranking."""
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

def _load_creativity_data():
    """Load creativity analysis data for social media - ONLY from selected month, no fallbacks."""
    try:
        creativity_data = load_creativity_analysis("social_media")
        if not creativity_data.empty:
            # Handle different column names between old and new formats
            if 'brand' in creativity_data.columns:
                # New format (September 2025+)
                creativity_data['normalized_brand'] = creativity_data['brand'].apply(lambda x: normalize_brand_name(x, "social_media"))
            elif 'Company' in creativity_data.columns:
                # Old format (August 2025 and earlier)
                creativity_data['brand'] = creativity_data['Company']  # Standardize to 'brand'
                creativity_data['normalized_brand'] = creativity_data['brand'].apply(lambda x: normalize_brand_name(x, "social_media"))
            else:
                # No brand column found
                return pd.DataFrame()
            return creativity_data
        return pd.DataFrame()
    except Exception as e:
        print(f"Error in _load_creativity_data: {e}")  # Debug print
        return pd.DataFrame()

def _load_brand_strength_data():
    """Load brand strength from compos analysis for social media - ONLY from selected month, no fallbacks."""
    try:
        compos_data = load_compos_analysis("social_media")
        if not compos_data.empty:
            # Calculate brand strength as percentage of dominant archetype
            strength_data = {}
            # Use 'Company' (capital C) instead of 'brand'
            company_col = 'Company' if 'Company' in compos_data.columns else 'brand'
            for brand in compos_data.get(company_col, []):
                brand_data = compos_data[compos_data[company_col] == brand]
                if 'Top Archetype' in brand_data.columns and len(brand_data.dropna(subset=['Top Archetype'])) > 0:
                    vc = brand_data['Top Archetype'].dropna().value_counts()
                    pct = float((vc.max() / vc.sum()) * 100) if vc.sum() > 0 else 0.0
                    # Normalize the brand name to match engagement data
                    normalized_brand = normalize_brand_name(brand, "social_media")
                    strength_data[normalized_brand] = pct
            return strength_data
        return {}
    except Exception as e:
        print(f"Error in _load_brand_strength_data: {e}")  # Debug print
        return {}

def _compute_social_engagement_totals():
    """Compute total engagement for each brand from social media data."""
    engagement_totals = {}
    
    # Load social media data
    df = load_monthly_social_media_data()
    if df is None or df.empty:
        return engagement_totals
    
    # Filter by date range
    start_date, end_date = get_selected_date_range()
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
    
    if not df_filtered.empty:
        # Calculate engagement using the same logic as data loading
        if "likes" in df_filtered.columns and "num_comments" in df_filtered.columns and "num_shares" in df_filtered.columns:
            # Calculate total engagement: likes + comments*3 + shares*5
            likes = pd.to_numeric(df_filtered["likes"], errors="coerce").fillna(0)
            comments = pd.to_numeric(df_filtered["num_comments"], errors="coerce").fillna(0)
            shares = pd.to_numeric(df_filtered["num_shares"], errors="coerce").fillna(0)
            df_filtered["calculated_engagement"] = likes + comments * 3 + shares * 5
        elif "total_engagement" in df_filtered.columns:
            df_filtered["calculated_engagement"] = pd.to_numeric(df_filtered["total_engagement"], errors="coerce").fillna(0)
        else:
            df_filtered["calculated_engagement"] = 0
        
        # Group by normalized company and sum engagement
        engagement_by_brand = df_filtered.groupby('normalized_company')['calculated_engagement'].sum()
        engagement_totals = engagement_by_brand.to_dict()
        
    
    return engagement_totals

def render():
    """Render the social media ranking metrics section."""
    st.markdown("### 📊 Social Media Performance Metrics")
    
    # Load data
    engagement_totals = _compute_social_engagement_totals()
    strength_data = _load_brand_strength_data()
    creativity_data = _load_creativity_data()
    
    # Get selected brands from session state (the "subset of companies")
    selected_brands = st.session_state.get("selected_brands", [])
    
    # Only show brands that are both selected AND have data
    available_brands = set(engagement_totals.keys()) | set(strength_data.keys())
    if not creativity_data.empty and 'normalized_brand' in creativity_data.columns:
        available_brands.update(creativity_data['normalized_brand'].unique())
    
    # Filter to only selected brands
    available_brands = [brand for brand in available_brands if brand in selected_brands]
    available_brands = sorted(available_brands)
    
    if not available_brands:
        st.info("No social media data available for the selected companies.")
        return
    
    # Calculate rankings and means
    engagement_series = pd.Series(engagement_totals)
    engagement_mean = engagement_series.mean() if len(engagement_series) else 0
    engagement_ranks = engagement_series.rank(ascending=False, method="min") if len(engagement_series) else pd.Series(dtype=float)
    
    strength_series = pd.Series(strength_data)
    strength_mean = strength_series.mean() if len(strength_series) else 0
    strength_ranks = strength_series.rank(ascending=False, method="min") if len(strength_series) else pd.Series(dtype=float)
    
    # Create brand tabs
    brand_tabs = st.tabs(available_brands)
    for i, brand_name in enumerate(available_brands):
        with brand_tabs[i]:
            col1, col2, col3 = st.columns(3)
            
            # Social Media Engagement
            with col1:
                total_engagement = int(engagement_totals.get(brand_name, 0))
                delta_mean_pct = ((total_engagement - (engagement_mean if engagement_mean != 0 else 1)) / (engagement_mean if engagement_mean != 0 else 1)) * 100 if engagement_mean != 0 else 0
                rank_now = engagement_ranks.get(brand_name, None) if len(engagement_ranks) else None
                _format_simple_metric_card(
                    label="Engagement",
                    val=f"{total_engagement:,}",
                    pct=delta_mean_pct,
                    rank_now=rank_now,
                    total_ranks=len(engagement_ranks) if len(engagement_ranks) else None
                )
            
            # Brand Strength
            with col2:
                if brand_name in strength_data:
                    strength = float(strength_data[brand_name])
                    rank_bs = int(strength_ranks.get(brand_name, 0))
                    delta_bs = ((strength - (strength_mean if strength_mean != 0 else 1)) / (strength_mean if strength_mean != 0 else 1)) * 100 if strength_mean != 0 else 0
                    _format_simple_metric_card(
                        label="Brand Strength",
                        val=f"{strength:.1f}%",
                        pct=delta_bs,
                        rank_now=rank_bs,
                        total_ranks=len(strength_ranks)
                    )
                else:
                    _format_simple_metric_card("Brand Strength", "N/A")
            
            # Creativity
            with col3:
                if not creativity_data.empty and 'normalized_brand' in creativity_data.columns:
                    brand_creativity = creativity_data[creativity_data['normalized_brand'] == brand_name]
                    if not brand_creativity.empty:
                        score = brand_creativity.iloc[0].get('originality_score', 0)
                        rank_cre = brand_creativity.iloc[0].get('rank', None)
                        
                        # Calculate delta vs mean since it's not provided in the data
                        creativity_scores = creativity_data['originality_score'].dropna()
                        creativity_mean = creativity_scores.mean() if len(creativity_scores) > 0 else 0
                        delta_cre = ((score - creativity_mean) / (creativity_mean if creativity_mean != 0 else 1)) * 100 if creativity_mean != 0 else 0
                        
                        _format_simple_metric_card(
                            label="Creativity",
                            val=f"{score:.2f}",
                            pct=delta_cre,
                            rank_now=rank_cre,
                            total_ranks=len(creativity_data)
                        )
                    else:
                        _format_simple_metric_card("Creativity", "N/A")
                else:
                    _format_simple_metric_card("Creativity", "N/A")
            
            # Creativity Analysis section (full width, outside columns)
            if not creativity_data.empty and 'normalized_brand' in creativity_data.columns:
                brand_creativity = creativity_data[creativity_data['normalized_brand'] == brand_name]
                if not brand_creativity.empty:
                    score = brand_creativity.iloc[0].get('originality_score', 0)
                    rank_cre = brand_creativity.iloc[0].get('rank', None)
                    just_text = str(brand_creativity.iloc[0].get('justification', '')) if pd.notna(brand_creativity.iloc[0].get('justification', '')) else ""
                    examples_text = str(brand_creativity.iloc[0].get('examples', '')) if pd.notna(brand_creativity.iloc[0].get('examples', '')) else ""
                    
                    if just_text or examples_text:
                        st.markdown("#### Creativity Analysis")
                        st.markdown(f"""
                        <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                            <h5 style="margin:0;">{brand_name} — {f'Rank {rank_cre} — ' if rank_cre is not None else ''}Score {score:.2f}</h5>
                            {f'<p style="margin:8px 0 0; color:#444;">{just_text}</p>' if just_text else ''}
                            {f'<p style="margin:8px 0 0; color:#444;">Examples: {examples_text}</p>' if examples_text else ''}
                        </div>
                        """, unsafe_allow_html=True)
