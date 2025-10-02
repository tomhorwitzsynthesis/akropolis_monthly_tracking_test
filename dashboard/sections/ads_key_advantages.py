#!/usr/bin/env python3
"""
Ads Key Advantages Section for Monthly Dashboard
Shows key advantages by brand with evidence and examples
"""

import streamlit as st
import pandas as pd
import os
from utils.config import DATA_ROOT

def _load_key_advantages():
    """Load key advantages data from key_advantages_ads.xlsx"""
    # Look for key advantages file in the current month's ads analysis folder
    from utils.file_io import get_month_folder_name
    from utils.config import normalize_brand_name, ANALYSIS_YEAR, ANALYSIS_MONTH
    
    # Use the analysis month from config
    month_folder = get_month_folder_name(ANALYSIS_YEAR, ANALYSIS_MONTH)
    path = os.path.join(DATA_ROOT, month_folder, "ads", "analysis", "key_advantages", "key_advantages_ads.xlsx")
    
    if not os.path.exists(path):
        return {}
    
    advantages = {}
    try:
        xls = pd.ExcelFile(path)
        
        for sheet_name in xls.sheet_names:
            # Skip summary and skipped companies sheets
            if sheet_name in ['Summary', 'Skipped Companies']:
                continue
                
            # Use the sheet name directly (it's already the brand name format used in key advantages)
            # Normalize the brand name using key advantages mapping
            normalized_brand_name = normalize_brand_name(sheet_name, "ads", is_key_advantages_data=True)
            
            df_adv = pd.read_excel(path, sheet_name=sheet_name)
            df_adv.columns = [str(col).lower().strip() for col in df_adv.columns]
            required_cols = ['advantage_id', 'title', 'evidence_list', 'example_index', 'example_quote']
            for col in required_cols:
                if col not in df_adv.columns:
                    df_adv[col] = ""
            # Use normalized brand name as key
            advantages[normalized_brand_name] = df_adv[required_cols]
    except Exception:
        pass
    return advantages

def _load_key_advantages_summary():
    """Load key advantages summary from key_advantages_ads.xlsx"""
    # Look for key advantages file in the current month's ads analysis folder
    from utils.file_io import get_month_folder_name
    from utils.config import ANALYSIS_YEAR, ANALYSIS_MONTH
    
    # Use the analysis month from config
    month_folder = get_month_folder_name(ANALYSIS_YEAR, ANALYSIS_MONTH)
    path = os.path.join(DATA_ROOT, month_folder, "ads", "analysis", "key_advantages", "key_advantages_ads.xlsx")
    
    if not os.path.exists(path):
        return ""
    try:
        # Try to read a summary sheet if it exists
        xls = pd.ExcelFile(path)
        if 'Summary' in xls.sheet_names:
            df_summary = pd.read_excel(path, sheet_name='Summary')
            summary_col = None
            for col in df_summary.columns:
                if 'summary' in str(col).lower():
                    summary_col = col
                    break
            if summary_col and len(df_summary) > 0:
                return str(df_summary[summary_col].iloc[0])
        return ""
    except Exception as e:
        st.error(f"Error loading key advantages summary: {e}")
        return ""

def render():
    """Render the key advantages section."""
    st.markdown("### Key Advantages")
    
    key_advantages_data = _load_key_advantages()
    
    if not key_advantages_data:
        st.info("No key advantages data loaded. Place key_advantages.xlsx in data/key_advantages.")
    else:
        # Filter by selected brands from session state
        selected_brands = st.session_state.get("selected_brands", [])
        
        if selected_brands:
            # Filter key advantages data to only include selected brands
            key_advantages_data = {brand: data for brand, data in key_advantages_data.items() if brand in selected_brands}
        
        if not key_advantages_data:
            st.info("No key advantages data available for selected brands.")
        else:
            brand_tabs = st.tabs(list(key_advantages_data.keys()))
            for i, brand_disp in enumerate(key_advantages_data.keys()):
                with brand_tabs[i]:
                    st.subheader(f"{brand_disp} Key Advantages")
                    brand_data = key_advantages_data.get(brand_disp)
                    if brand_data is None or brand_data.empty:
                        st.info(f"No specific key advantages found for {brand_disp}.")
                    else:
                        grouped_data = brand_data.groupby(['title', 'evidence_list']).agg({
                            'example_quote': lambda x: list(x)
                        }).reset_index()
                        col1, col2 = st.columns(2)
                        for idx, (_, row) in enumerate(grouped_data.iterrows()):
                            with (col1 if idx % 2 == 0 else col2):
                                examples_html = ""
                                for ii, example in enumerate(row['example_quote']):
                                    if example and str(example).strip():
                                        examples_html += f"<li style='margin:4px 0; color:#444;'>{example}</li>"
                                examples_html = f"<ul style='margin:4px 0 0; padding-left:20px;'>{examples_html}</ul>" if examples_html else "<p style='margin:4px 0 0; color:#444;'>No examples available</p>"
                                st.markdown(f"""
                                <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:10px; max-height:800px; overflow-y:auto;">
                                    <h5 style="margin:0; word-wrap:break-word;">{row['title']}</h5>
                                    <p style="margin:8px 0 0; font-weight:bold; color:#333;">Evidence:</p>
                                    <p style="margin:4px 0 8px; color:#444; word-wrap:break-word; white-space:pre-wrap;">{row['evidence_list']}</p>
                                    <p style="margin:8px 0 0; font-weight:bold; color:#333;">Examples:</p>
                                    {examples_html}
                                </div>
                                """, unsafe_allow_html=True)

            # st.subheader("Key Advantages Summary")
            summary_text = _load_key_advantages_summary()
            if isinstance(summary_text, str) and summary_text.strip():
                st.markdown(summary_text)
            else:
                # Fallback simple table if summary file absent: show companies only
                try:
                    summary_path = os.path.join("data", "key_advantages", "key_advantages_summary.xlsx")
                    if os.path.exists(summary_path):
                        summary_df = pd.read_excel(summary_path)
                        st.table(summary_df)
                except Exception:
                    pass
