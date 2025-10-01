#!/usr/bin/env python3
"""
Ads Top Archetypes Section for Monthly Dashboard
Shows top 3 archetypes by company from compos analysis
"""

import streamlit as st
import pandas as pd
import os
import glob
from utils.config import DATA_ROOT

def _load_top_archetypes_from_summary():
    """Load top archetypes from compos analysis file."""
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
        archetypes = {}
        
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
                # Group by brand and get top 3 archetypes for each brand
                for brand in df[brand_col].unique():
                    if pd.notna(brand):
                        brand_data = df[df[brand_col] == brand]
                        archetype_counts = brand_data['Top Archetype'].value_counts()
                        total_ads = len(brand_data)
                        
                        if total_ads > 0:
                            # Get top 3 archetypes
                            top3 = archetype_counts.head(3)
                            items = []
                            for archetype, count in top3.items():
                                pct = (count / total_ads) * 100
                                items.append({'archetype': archetype, 'percentage': pct, 'count': int(count)})
                            
                            if items:
                                normalized_brand = normalize_brand_name(brand, "ads")
                                archetypes[normalized_brand] = items
        return archetypes
    except Exception:
        return {}

def _load_top_archetypes_from_agility():
    """Load top archetypes from agility data as fallback."""
    # This would need to be implemented if agility data is available
    # For now, return empty dict
    return {}

def render():
    """Render the top archetypes by company section."""
    st.markdown("### Top Archetypes by Company")
    
    archetypes_data = _load_top_archetypes_from_summary()
    if not archetypes_data:
        archetypes_data = _load_top_archetypes_from_agility()
    
    # Debug: Show loaded archetypes data
    # Filter by selected brands from session state
    selected_brands = st.session_state.get("selected_brands", [])
    
    if selected_brands and archetypes_data:
        # Filter archetypes data to only include selected brands
        archetypes_data = {brand: data for brand, data in archetypes_data.items() if brand in selected_brands}
    
    if archetypes_data:
        # Compute overall top archetypes
        overall_counts = {}
        overall_total = 0
        for archetypes in archetypes_data.values():
            for item in archetypes:
                archetype = item['archetype']
                count = item['count']
                overall_counts[archetype] = overall_counts.get(archetype, 0) + count
                overall_total += count
        
        overall_top3 = sorted(overall_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        overall_items = []
        for archetype, count in overall_top3:
            pct = (count / overall_total) * 100 if overall_total > 0 else 0
            overall_items.append({'archetype': archetype, 'percentage': pct, 'count': count})

        tab_labels = ["🌍 Overall"] + list(archetypes_data.keys())
        company_tabs = st.tabs(tab_labels)
        
        # Overall tab
        with company_tabs[0]:
            st.subheader("Overall - Top 3 Archetypes")
            col1, col2, col3 = st.columns(3)
            for j, archetype_info in enumerate(overall_items):
                col = col1 if j == 0 else col2 if j == 1 else col3
                with col:
                    st.markdown(f"""
                    <div style="border:1px solid #ddd; border-radius:10px; padding:10px; margin-bottom:10px; text-align:center;">
                        <h4 style="margin:0; color:#333;">{archetype_info['archetype']}</h4>
                        <h2 style="margin:5px 0; color:#333; font-size:2.0em;">{archetype_info['percentage']:.1f}%</h2>
                        <p style="margin:0; color:#666; font-size:0.9em;">{archetype_info['count']} items</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Company tabs
        for i, (company, archetypes) in enumerate(archetypes_data.items()):
            with company_tabs[i + 1]:
                st.subheader(f"{company} - Top 3 Archetypes")
                col1, col2, col3 = st.columns(3)
                for j, archetype_info in enumerate(archetypes):
                    col = col1 if j == 0 else col2 if j == 1 else col3
                    with col:
                        st.markdown(f"""
                        <div style="border:1px solid #ddd; border-radius:10px; padding:10px; margin-bottom:10px; text-align:center;">
                            <h4 style="margin:0; color:#333;">{archetype_info['archetype']}</h4>
                            <h2 style="margin:5px 0; color:#333; font-size:2.0em;">{archetype_info['percentage']:.1f}%</h2>
                            <p style="margin:0; color:#666; font-size:0.9em;">{archetype_info['count']} items</p>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("No archetype data available. Ensure compos files are in data/ads/compos or Agility files contain 'Top Archetype'.")

    st.markdown('Read more about brand archetypes here: [Brandtypes](https://www.comp-os.com/brandtypes)')
