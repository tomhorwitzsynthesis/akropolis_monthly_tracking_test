import streamlit as st
from utils.date_utils import init_month_selector
from utils.config import AKROPOLIS_LOCATIONS, BIG_PLAYERS, SMALLER_PLAYERS, OTHER_CITIES, RETAIL

# --- Section Imports ---
from sections.compos_matrix import render as render_matrix
from sections.sentiment_analysis import render as render_sentiment
from sections.topical_analysis import render as render_topics
from sections.volume_trends import render as render_volume
from sections.media_coverage import render as render_media_shares

from sections.volume_engagement_trends import render as render_social_trends
from sections.social_media_top_posts import render as render_top_posts
from sections.social_media_clusters import render as render_social_clusters
from sections.pr_ranking_metrics import render as render_pr_ranking
from sections.social_media_ranking_metrics import render as render_social_ranking
from sections.pr_archetypes import render as render_pr_archetypes

from sections.content_pillars import render as render_content_pillars

from sections.audience_affinity import render as render_audience_affinity
from sections.ads_dashboard_new import render as render_ads_dashboard

#from sections.content_pillar_analysis import render as render_pillars  # If implemented
# from sections.audience_affinity import render as render_affinity     # Optional

# --- Page Configuration ---
st.set_page_config(page_title="Monthly Dashboard - Akropolis Intelligence", layout="wide")

# --- Company Cluster Selection ---
st.title("🏢 Monthly Dashboard - Akropolis Intelligence")

# --- Sidebar ---
st.sidebar.title("📁 Navigation")
section = st.sidebar.radio("Go to", [
    "Press Releases",
    "Social Media", 
    "Content Pillars",
    "Audience Affinity",
    "Ads Dashboard"
])

# Only show company selection UI for sections that need it (not Content Pillars or Audience Affinity)
if section not in ["Content Pillars", "Audience Affinity"]:
    # Company cluster selector at the top
    SUBSETS_CORE = {
        "Big players": BIG_PLAYERS,
        "Smaller players": SMALLER_PLAYERS,
        "Other cities": OTHER_CITIES,
    }
    SUBSETS_WITH_RETAIL = {
        **SUBSETS_CORE,
        "Retail": RETAIL,
    }

    st.markdown("**Select Akropolis locations (always included):**")
    ak_cols = st.columns(len(AKROPOLIS_LOCATIONS))
    ak_selected = []
    for i, loc in enumerate(AKROPOLIS_LOCATIONS):
        with ak_cols[i]:
            if st.checkbox(loc, value=True, key=f"ak_{i}"):
                ak_selected.append(loc)

    # Company cluster selector - full width at the top
    st.markdown("**Select company cluster to analyze:**")
    subset_name = st.selectbox(
        "Subset of companies",
        options=list(SUBSETS_WITH_RETAIL.keys()),
        index=0,
        help="Charts include the selected Akropolis locations **plus** this subset.",
    )

    # Store selected brands in session state for use by sections
    brands_universe = set(ak_selected) | set(SUBSETS_WITH_RETAIL.get(subset_name, []))
    st.session_state["selected_brands"] = sorted(list(brands_universe))

    st.markdown("---")

# --- Month Filter ---
init_month_selector()  # Sets start_date / end_date globally

# --- Section Routing ---
if section == "Press Releases":
    st.title("📰 Press Release Dashboard")
    
    # Check if Retail is selected and show notice
    if "Retail" in st.session_state.get("selected_brands", []):
        st.info("No PR data for Retail")
    else:
        render_pr_ranking()
        st.markdown("---")
        render_pr_archetypes()
        st.markdown("---")
        render_matrix()
        st.markdown("---")
        render_sentiment(mode="by_company")
        st.markdown("---")
        render_topics()
        st.markdown("---")
        render_volume(mode="by_company")
        st.markdown("---")
        render_media_shares(mode="by_brand")

elif section == "Social Media":
    st.title("📱 Social Media Dashboard")
    
    render_social_ranking()
    st.markdown("---")
    render_social_trends(selected_platforms=["facebook"])
    st.markdown("---")
    render_top_posts(selected_platforms=["facebook"])
    st.markdown("---")
    render_social_clusters()

elif section == "Content Pillars":
    st.title("🧱 Content Pillar Dashboard")
    render_content_pillars()

elif section == "Audience Affinity":
    st.title("🎯 Audience Affinity Dashboard")
    render_audience_affinity()

elif section == "Ads Dashboard":
    st.title("📣 Ad Intelligence Dashboard")
    render_ads_dashboard()
