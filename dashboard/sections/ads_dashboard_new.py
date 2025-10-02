#!/usr/bin/env python3
"""
New Ads Dashboard Section for Monthly Dashboard
Consolidates all ads-related sections into a single dashboard
"""

import streamlit as st

# Import all the separate ads sections
from sections.ads_volume_share import render as render_volume_share
from sections.ads_brand_summary import render as render_brand_summary
from sections.ads_archetypes import render as render_archetypes
from sections.ads_key_advantages import render as render_key_advantages
from sections.ads_volume_trends import render as render_volume_trends
from sections.ads_clusters import render as render_clusters

def render():
    """Render the complete ads dashboard with all sections."""
    
    # Render all the separate sections
    render_volume_share()
    st.markdown("---")
    render_brand_summary()
    st.markdown("---")
    render_archetypes()
    st.markdown("---")
    render_key_advantages()
    st.markdown("---")
    render_clusters()
    st.markdown("---")
    render_volume_trends()
