import streamlit as st
import pandas as pd
import plotly.express as px
from utils.config import BRAND_COLORS, normalize_brand_name, get_brand_column
from utils.file_io import load_monthly_social_media_data
from utils.date_utils import get_selected_date_range

PLATFORMS = ["facebook"]  # Only Facebook available

# --- color helpers ---
_ALL_BRANDS = "All Brands"
_FALLBACK = "#BDBDBD"
_CATEGORY_ORDER = list(BRAND_COLORS.keys())

def _present_color_map(present_labels) -> dict:
    m = dict(BRAND_COLORS)
    for b in present_labels:
        if b not in m:
            m[b] = _FALLBACK
    return m

# -----------------------------------------------------------------------

def render(selected_platforms=None):
    st.subheader("📈 Social Media Volume & Engagement Trends")

    # Default to all supported platforms if none provided
    if not selected_platforms:
        selected_platforms = PLATFORMS

    # Load social media data
    df = load_monthly_social_media_data()
    
    if df is None or df.empty:
        st.info("No social media data found.")
        return
    
    # Check if we have the required columns
    if "date" not in df.columns:
        st.error("No 'date' column found in social media data")
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

    # Get date range from the filtered data
    all_dates = pd.to_datetime(df_filtered["date"], errors="coerce").dropna().tolist()
    
    if not all_dates:
        st.warning("No valid dates found in social media data.")
        return

    # Initialize data structures
    volume_data, engagement_data = [], []

    # Get unique companies from the filtered data
    brand_col = get_brand_column("social_media")
    companies = df_filtered[brand_col].unique()
    
    for company in companies:
        company_df = df_filtered[df_filtered[brand_col] == company]
        
        if company_df.empty:
            continue

        # Get normalized company name for display
        normalized_company = normalize_brand_name(company, "social_media")

        # Group by day - ensure timezone-naive
        company_df["Day"] = company_df["date"].dt.date

        # Volume (post count) - group by day
        daily_counts = company_df.groupby("Day").size()

        # Engagement - use the same logic as data loading
        if "likes" in company_df.columns and "num_comments" in company_df.columns and "num_shares" in company_df.columns:
            # Calculate total engagement: likes + comments*3 + shares*5
            likes = pd.to_numeric(company_df["likes"], errors="coerce").fillna(0)
            comments = pd.to_numeric(company_df["num_comments"], errors="coerce").fillna(0)
            shares = pd.to_numeric(company_df["num_shares"], errors="coerce").fillna(0)
            company_df["calculated_engagement"] = likes + comments * 3 + shares * 5
            daily_engagement = company_df.groupby("Day")["calculated_engagement"].sum()
        elif "total_engagement" in company_df.columns:
            company_df["total_engagement"] = pd.to_numeric(company_df["total_engagement"], errors="coerce").fillna(0)
            daily_engagement = company_df.groupby("Day")["total_engagement"].sum()
        else:
            daily_engagement = pd.Series(dtype=float)

        for day, count in daily_counts.items():
            volume_data.append({"Day": day, "Company": normalized_company, "Volume": count})
        for day, engagement in daily_engagement.items():
            engagement_data.append({"Day": day, "Company": normalized_company, "Engagement": engagement})

    # Create tabs for Volume and Engagement
    tab1, tab2 = st.tabs(["📊 Volume", "💬 Engagement"])

    # Volume Tab
    with tab1:
        if volume_data:
            volume_df = pd.DataFrame(volume_data)
            # Convert Day to proper datetime for better x-axis display
            volume_df["Day"] = pd.to_datetime(volume_df["Day"])
            fig = px.line(
                volume_df,
                x="Day",
                y="Volume",
                color="Company",
                title="Daily Post Volume",
                color_discrete_map=_present_color_map(volume_df["Company"].unique())
            )
            fig.update_layout(
                xaxis_title="Date", 
                yaxis_title="Number of Posts",
                xaxis=dict(
                    type='date',
                    tickformat='%b %d'  # Show day format like "Sep 01"
                )
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No volume data available.")

    # Engagement Tab
    with tab2:
        if engagement_data:
            engagement_df = pd.DataFrame(engagement_data)
            # Convert Day to proper datetime for better x-axis display
            engagement_df["Day"] = pd.to_datetime(engagement_df["Day"])
            fig = px.line(
                engagement_df,
                x="Day",
                y="Engagement",
                color="Company",
                title="Daily Engagement",
                color_discrete_map=_present_color_map(engagement_df["Company"].unique())
            )
            fig.update_layout(
                xaxis_title="Date", 
                yaxis_title="Total Engagement",
                xaxis=dict(
                    type='date',
                    tickformat='%b %d'  # Show day format like "Sep 01"
                )
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No engagement data available.")