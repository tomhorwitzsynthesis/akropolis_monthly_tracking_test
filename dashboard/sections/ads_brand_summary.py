#!/usr/bin/env python3
"""
Ads Brand Summary Section for Monthly Dashboard
Shows metric cards for Reach, Brand Strength, and Creativity by brand
"""

import streamlit as st
import pandas as pd
import os
import glob
from utils.file_io import load_monthly_ads_data, get_selected_date_range, load_creativity_analysis, load_compos_analysis
from utils.config import BRAND_COLORS, get_brand_column, DATA_ROOT

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

def _normalize_brand(name: str) -> str:
    """Normalize brand name for matching across data sources."""
    if not isinstance(name, str):
        return ""
    base = name.split("|")[0].strip()
    cleaned = "".join(ch.lower() if (ch.isalnum() or ch.isspace()) else " " for ch in base)
    return " ".join(cleaned.split())

def _load_brand_strength_from_summary():
    """Load brand strength from compos analysis file."""
    # Look for compos analysis file in the current month's ads analysis folder
    from utils.file_io import get_month_folder_name
    from utils.config import normalize_brand_name, ANALYSIS_YEAR, ANALYSIS_MONTH
    
    # Use the analysis month from config
    month_folder = get_month_folder_name(ANALYSIS_YEAR, ANALYSIS_MONTH)
    compos_analysis_path = os.path.join(DATA_ROOT, month_folder, "ads", "analysis", "compos", "compos_analysis_ads.xlsx")
    
    if not os.path.exists(compos_analysis_path):
        return {}
    
    try:
        df = pd.read_excel(compos_analysis_path)
        strength = {}
        
        # Check if the data has a 'Top Archetype' column (from compos analysis)
        if 'Top Archetype' in df.columns:
            # Find the brand column - try different possible column names
            brand_col = None
            possible_brand_cols = ['pageName', 'page_name', 'brand', 'advertiser', 'ad_details/advertiser/ad_library_page_info/page_info/page_name']
            
            for col in possible_brand_cols:
                if col in df.columns:
                    brand_col = col
                    break
            
            if brand_col:
                # Group by brand and calculate archetype dominance
                for brand in df[brand_col].unique():
                    if pd.notna(brand):
                        brand_data = df[df[brand_col] == brand]
                        archetype_counts = brand_data['Top Archetype'].value_counts()
                        total_ads = len(brand_data)
                        if total_ads > 0:
                            dominant_archetype_count = archetype_counts.iloc[0] if len(archetype_counts) > 0 else 0
                            strength_percentage = (dominant_archetype_count / total_ads) * 100
                            normalized_brand = normalize_brand_name(brand, "ads")
                            strength[normalized_brand] = strength_percentage
        return strength
    except Exception:
        return {}

def _load_creativity():
    """Load creativity analysis data."""
    try:
        creativity_data = load_creativity_analysis("ads")
        if not creativity_data.empty:
            creativity_data['rank'] = pd.to_numeric(creativity_data['rank'], errors='coerce')
            creativity_data['originality_score'] = pd.to_numeric(creativity_data['originality_score'], errors='coerce')
            cre_mean = creativity_data['originality_score'].mean()
            denom = cre_mean if cre_mean != 0 else 1
            creativity_data['delta_vs_mean_pct'] = ((creativity_data['originality_score'] - denom) / denom) * 100
            return creativity_data
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def render():
    """Render the ads brand summary section with metric cards."""
    st.markdown("### Brand Summary")
    
    df = load_monthly_ads_data()
    if df is None or df.empty:
        st.info("No ads data available.")
        return

    # Get selected brands from session state first
    selected_brands = st.session_state.get("selected_brands", [])
    
    brand_col = get_brand_column("ads")
    
    # Check if brand column exists
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
    

    # Compute 6-month reach totals and ranks using normalized brands
    reach_6m = df_fixed.groupby('normalized_brand')['reach'].sum() if not df_fixed.empty else pd.Series(dtype=float)
    reach_mean = reach_6m.mean() if len(reach_6m) else 0
    reach_ranks = reach_6m.rank(ascending=False, method="min") if len(reach_6m) else pd.Series(dtype=float)

    # Brand strength from compos files
    strength_map = _load_brand_strength_from_summary()
    if strength_map:
        bs_df = pd.DataFrame({'brand': list(strength_map.keys()), 'strength': list(strength_map.values())})
        bs_df['brand_norm'] = bs_df['brand'].apply(_normalize_brand)
        bs_df['rank'] = bs_df['strength'].rank(ascending=False, method='min')
        bs_mean = bs_df['strength'].mean() if len(bs_df) else 0
        bs_df['delta_vs_mean_pct'] = ((bs_df['strength'] - bs_mean) / (bs_mean if bs_mean != 0 else 1)) * 100
    else:
        bs_df = pd.DataFrame(columns=['brand', 'brand_norm', 'strength', 'rank', 'delta_vs_mean_pct'])
        bs_mean = 0

    creativity_df = _load_creativity()

    # Filter ads data by selected brands using normalized names
    if selected_brands:
        df_fixed = df_fixed[df_fixed['normalized_brand'].isin(selected_brands)]
    
    # Build brand tabs from union of brands across sources, but only include selected brands
    ads_brands = set(df_fixed['normalized_brand'].dropna().unique())  # Use normalized brands
    compos_brands = set(bs_df['brand'].unique()) if len(bs_df) else set()
    creativity_brands = set(creativity_df['brand'].dropna().unique()) if not creativity_df.empty else set()

    # Normalize for matching, but display original preferred names
    norm_to_display = {}
    for b in compos_brands.union(ads_brands).union(creativity_brands):
        norm = _normalize_brand(b)
        if norm not in norm_to_display:
            if b in ads_brands:
                norm_to_display[norm] = b
            else:
                norm_to_display[norm] = b

    # Filter to only include selected brands
    if selected_brands:
        available_brands = [brand for brand in norm_to_display.values() if brand in selected_brands]
    else:
        available_brands = sorted(list(norm_to_display.values()))

    if not available_brands:
        st.info("No brands available to display.")
    else:
        brand_tabs = st.tabs(available_brands)
        for i, brand_name in enumerate(available_brands):
            with brand_tabs[i]:
                col1, col2, col3 = st.columns(3)

                # Reach 6 months
                with col1:
                    total_reach = int(reach_6m.get(brand_name, 0)) if len(reach_6m) else 0
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
                    row = bs_df[bs_df['brand_norm'] == _normalize_brand(brand_name)]
                    if not row.empty:
                        strength = float(row['strength'].iloc[0])
                        rank_bs = int(row['rank'].iloc[0])
                        delta_bs = float(row['delta_vs_mean_pct'].iloc[0])
                        _format_simple_metric_card(
                            label="Brand Strength",
                            val=f"{strength:.1f}%",
                            pct=delta_bs,
                            rank_now=rank_bs,
                            total_ranks=len(bs_df)
                        )
                    else:
                        _format_simple_metric_card("Brand Strength", "N/A")

                # Creativity
                with col3:
                    # Use creativity-specific brand mapping for matching
                    from utils.config import normalize_brand_name
                    normalized_creativity_brands = creativity_df['brand'].apply(lambda x: normalize_brand_name(x, "ads", is_creativity_data=True)) if not creativity_df.empty else pd.Series()
                    cre_row = creativity_df[normalized_creativity_brands == brand_name] if not creativity_df.empty else pd.DataFrame()
                    if not cre_row.empty:
                        score = cre_row['originality_score'].iloc[0]
                        rank_cre = int(cre_row['rank'].iloc[0]) if pd.notna(cre_row['rank'].iloc[0]) else None
                        delta_cre = float(cre_row['delta_vs_mean_pct'].iloc[0]) if pd.notna(cre_row['delta_vs_mean_pct'].iloc[0]) else None
                        _format_simple_metric_card(
                            label="Creativity",
                            val=f"{score:.2f}",
                            pct=delta_cre,
                            rank_now=rank_cre,
                            total_ranks=creativity_df['brand'].nunique() if not creativity_df.empty else None
                        )
                    else:
                        _format_simple_metric_card("Creativity", "N/A")

                # Creativity Analysis section
                if not creativity_df.empty:
                    # Use creativity-specific brand mapping for matching
                    normalized_creativity_brands = creativity_df['brand'].apply(lambda x: normalize_brand_name(x, "ads", is_creativity_data=True))
                    cre_row = creativity_df[normalized_creativity_brands == brand_name]
                    if not cre_row.empty:
                        score = cre_row['originality_score'].iloc[0]
                        rank_cre = int(cre_row['rank'].iloc[0]) if pd.notna(cre_row['rank'].iloc[0]) else None
                        just_text = str(cre_row['justification'].iloc[0]) if pd.notna(cre_row['justification'].iloc[0]) else ""
                        examples_text = str(cre_row['examples'].iloc[0]) if pd.notna(cre_row['examples'].iloc[0]) else ""
                        if just_text or examples_text:
                            st.markdown("#### Creativity Analysis")
                            st.markdown(f"""
                            <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px;">
                                <h5 style="margin:0;">{brand_name} — {f'Rank {rank_cre} — ' if rank_cre is not None else ''}Score {score:.2f}</h5>
                                {f'<p style="margin:8px 0 0; color:#444;">{just_text}</p>' if just_text else ''}
                                {f'<p style="margin:8px 0 0; color:#444;">Examples: {examples_text}</p>' if examples_text else ''}
                            </div>
                            """, unsafe_allow_html=True)
