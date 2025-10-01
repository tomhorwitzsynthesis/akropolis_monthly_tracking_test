#!/usr/bin/env python3
"""
PR Ranking Metrics for Monthly Dashboard
Shows top 3 metrics: Reach, Brand Strength, Creativity
"""

import streamlit as st
import pandas as pd
import os
import glob
from utils.file_io import load_monthly_pr_data, get_selected_date_range, load_creativity_analysis, load_compos_analysis
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
    """Load creativity analysis data for PR - ONLY from selected month, no fallbacks."""
    try:
        creativity_data = load_creativity_analysis("pr")
        if not creativity_data.empty:
            # Handle different column names between old and new formats
            if 'brand' in creativity_data.columns:
                # New format (September 2025+)
                creativity_data['normalized_brand'] = creativity_data['brand'].apply(lambda x: normalize_brand_name(x, "pr"))
            elif 'Company' in creativity_data.columns:
                # Old format (August 2025 and earlier)
                creativity_data['brand'] = creativity_data['Company']  # Standardize to 'brand'
                creativity_data['normalized_brand'] = creativity_data['brand'].apply(lambda x: normalize_brand_name(x, "pr"))
            else:
                # No brand column found
                return pd.DataFrame()
            return creativity_data
        return pd.DataFrame()
    except Exception as e:
        print(f"Error in _load_creativity_data: {e}")  # Debug print
        return pd.DataFrame()

def _load_brand_strength_data():
    """Load brand strength from PR master data, calculating percentage of dominant archetype per brand (same as Volume vs Quality matrix)."""
    try:
        # Load PR data (same as Volume vs Quality matrix)
        df = load_monthly_pr_data()
        if df is None or df.empty:
            return {}
        
        # Filter data for the selected date range (same as Volume vs Quality matrix)
        start_date, end_date = get_selected_date_range()
        df_filtered = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        # Get selected brands from session state (same as Volume vs Quality matrix)
        selected_brands = st.session_state.get("selected_brands", [])
        
        # Filter by selected brands using normalized names (same as Volume vs Quality matrix)
        if selected_brands:
            # Normalize the company names in the data and filter
            df_filtered['normalized_company'] = df_filtered['company'].apply(lambda x: normalize_brand_name(x, "pr"))
            df_filtered = df_filtered[df_filtered['normalized_company'].isin(selected_brands)]
        
        # Get unique companies from the filtered data (same as Volume vs Quality matrix)
        companies = df_filtered['company'].unique()
        
        strength_data = {}
        for company in companies:
            company_df = df_filtered[df_filtered['company'] == company]
            
            # Get normalized company name for display
            normalized_company = normalize_brand_name(company, "pr")
            
            if "Top Archetype" in company_df.columns and not company_df.empty:
                # Calculate percentage of the most common archetype (same logic as Volume vs Quality matrix)
                archetype_counts = company_df["Top Archetype"].value_counts()
                if len(archetype_counts) > 0:
                    dominant_count = archetype_counts.iloc[0]  # Most common archetype count
                    total_count = archetype_counts.sum()
                    pct = float((dominant_count / total_count) * 100) if total_count > 0 else 0.0
                    strength_data[normalized_company] = pct
        
        return strength_data
        
    except Exception:
        return {}

def _compute_pr_reach_totals():
    """Compute total impressions (reach) for each brand from PR data."""
    reach_totals = {}
    
    # Load PR data
    df = load_monthly_pr_data()
    if df is None or df.empty:
        return reach_totals
    
    # # Debug: Show raw data info
    # st.write("🔍 Debug - Raw PR Data:")
    # st.write(f"Total rows loaded: {len(df)}")
    # st.write(f"Columns: {df.columns.tolist()}")
    # if 'reach' in df.columns:
    #     st.write(f"Reach column stats: min={df['reach'].min()}, max={df['reach'].max()}, sum={df['reach'].sum()}")
    
    # Filter by date range
    start_date, end_date = get_selected_date_range()
    if df['date'].dt.tz is not None:
        start_date = pd.Timestamp(start_date).tz_localize('UTC')
        end_date = pd.Timestamp(end_date).tz_localize('UTC')
    
    df_filtered = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    # st.write(f"Rows after date filtering: {len(df_filtered)}")
    
    # Get selected brands from session state and filter
    selected_brands = st.session_state.get("selected_brands", [])
    
    if selected_brands:
        # Get the correct brand column for PR
        brand_col = get_brand_column("pr")
        
        # # Debug: Show brands before normalization
        # st.write(f"🔍 Debug - Before brand filtering:")
        # st.write(f"Brand column: {brand_col}")
        # st.write(f"Unique brands in data: {df_filtered[brand_col].unique().tolist()}")
        
        # Normalize the company names in the data and filter
        df_filtered['normalized_company'] = df_filtered[brand_col].apply(lambda x: normalize_brand_name(x, "pr"))
        
        # st.write(f"Normalized companies: {df_filtered['normalized_company'].unique().tolist()}")
        # st.write(f"Selected brands: {selected_brands}")
        
        # df_filtered = df_filtered[df_filtered['normalized_company'].isin(selected_brands)]
        # st.write(f"Rows after brand filtering: {len(df_filtered)}")
    
    if not df_filtered.empty and 'reach' in df_filtered.columns:
        # Debug: Show detailed reach calculation
        # st.write("🔍 Debug - PR Reach Computation:")
        # st.write(f"Selected brands: {selected_brands}")
        # st.write(f"Brand column: {brand_col}")
        # st.write(f"Total rows after filtering: {len(df_filtered)}")
        # st.write(f"Unique brands in data: {df_filtered[brand_col].unique().tolist()}")
        # st.write(f"Normalized companies: {df_filtered['normalized_company'].unique().tolist()}")
        
        # # Show reach values by raw brand name
        # st.write("🔍 Debug - Reach by raw brand name:")
        reach_by_raw_brand = df_filtered.groupby(brand_col)['reach'].sum()
        # st.write(reach_by_raw_brand.to_dict())
        
        # # Show reach values by normalized brand name
        # st.write("🔍 Debug - Reach by normalized brand name:")
        reach_by_brand = df_filtered.groupby('normalized_company')['reach'].sum()
        reach_totals = reach_by_brand.to_dict()
        # st.write(reach_totals)
        
        # # Show sample data for each brand
        # st.write("🔍 Debug - Sample data by brand:")
        # for brand in df_filtered['normalized_company'].unique():
        #     brand_data = df_filtered[df_filtered['normalized_company'] == brand]
        #     st.write(f"{brand}: {len(brand_data)} rows, reach sum: {brand_data['reach'].sum()}")
        #     if len(brand_data) > 0:
        #         st.write(f"  Sample reach values: {brand_data['reach'].head(3).tolist()}")
    
    return reach_totals

def render():
    """Render the PR ranking metrics section."""
    st.markdown("### 📊 PR Performance Metrics")
    
    # Load data
    reach_totals = _compute_pr_reach_totals()
    strength_data = _load_brand_strength_data()
    creativity_data = _load_creativity_data()
    
    # # Debug: Show what data was loaded
    # st.write("🔍 Debug - PR Data Loading:")
    # st.write(f"Reach totals: {reach_totals}")
    # st.write(f"Strength data: {strength_data}")
    # st.write(f"Creativity data shape: {creativity_data.shape if not creativity_data.empty else 'Empty'}")
    # if not creativity_data.empty:
    #     st.write(f"Creativity brands: {creativity_data['brand'].unique().tolist()}")
    
    # Get selected brands from session state (the "subset of companies")
    selected_brands = st.session_state.get("selected_brands", [])
    
    # Only show brands that are both selected AND have data
    available_brands = set(reach_totals.keys()) | set(strength_data.keys())
    if not creativity_data.empty and 'normalized_brand' in creativity_data.columns:
        available_brands.update(creativity_data['normalized_brand'].unique())
    
    # Filter to only selected brands
    available_brands = [brand for brand in available_brands if brand in selected_brands]
    available_brands = sorted(available_brands)
    
    # st.write(f"🔍 Debug - Selected brands: {selected_brands}")
    # st.write(f"🔍 Debug - Available brands with data: {available_brands}")
    
    if not available_brands:
        st.info("No PR data available for the selected companies.")
        return
    
    # Calculate rankings and means
    reach_series = pd.Series(reach_totals)
    reach_mean = reach_series.mean() if len(reach_series) else 0
    reach_ranks = reach_series.rank(ascending=False, method="min") if len(reach_series) else pd.Series(dtype=float)
    
    strength_series = pd.Series(strength_data)
    strength_mean = strength_series.mean() if len(strength_series) else 0
    strength_ranks = strength_series.rank(ascending=False, method="min") if len(strength_series) else pd.Series(dtype=float)
    
    # Calculate creativity mean and rankings
    creativity_mean = 0
    creativity_ranks = pd.Series(dtype=float)
    if not creativity_data.empty and 'normalized_brand' in creativity_data.columns and 'originality_score' in creativity_data.columns:
        # Group by normalized_brand and take the first score for each brand (in case of duplicates)
        creativity_scores = creativity_data.groupby('normalized_brand')['originality_score'].first()
        creativity_mean = creativity_scores.mean() if len(creativity_scores) else 0
        creativity_ranks = creativity_scores.rank(ascending=False, method="min") if len(creativity_scores) else pd.Series(dtype=float)
    
    # Create brand tabs
    brand_tabs = st.tabs(available_brands)
    for i, brand_name in enumerate(available_brands):
        with brand_tabs[i]:
            col1, col2, col3 = st.columns(3)
            
            # PR Reach (Impressions)
            with col1:
                total_reach = int(reach_totals.get(brand_name, 0))
                delta_mean_pct = ((total_reach - (reach_mean if reach_mean != 0 else 1)) / (reach_mean if reach_mean != 0 else 1)) * 100 if reach_mean != 0 else 0
                rank_now = reach_ranks.get(brand_name, None) if len(reach_ranks) else None
                _format_simple_metric_card(
                    label="Reach",
                    val=f"{total_reach:,}",
                    pct=delta_mean_pct,
                    rank_now=rank_now,
                    total_ranks=len(reach_ranks) if len(reach_ranks) else None
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
                        rank_cre = int(creativity_ranks[brand_name]) if brand_name in creativity_ranks and len(creativity_ranks) else None
                        delta_cre = ((score - (creativity_mean if creativity_mean != 0 else 1)) / (creativity_mean if creativity_mean != 0 else 1)) * 100 if creativity_mean != 0 else 0
                        _format_simple_metric_card(
                            label="Creativity",
                            val=f"{score:.2f}",
                            pct=delta_cre,
                            rank_now=rank_cre,
                            total_ranks=len(creativity_ranks) if len(creativity_ranks) else None
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
                    rank_cre = int(creativity_ranks[brand_name]) if brand_name in creativity_ranks and len(creativity_ranks) else None
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
