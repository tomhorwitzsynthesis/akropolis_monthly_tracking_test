import streamlit as st
import pandas as pd
import plotly.express as px
from utils.file_io import load_monthly_pr_data
from utils.date_utils import get_selected_date_range
from utils.config import BRANDS, BRAND_COLORS, normalize_brand_name   # <-- long-key palette, e.g., "SEB Lietuvoje"
from pandas.tseries.offsets import MonthEnd

# --- name normalization: short -> long (matches BRAND_COLORS keys) ---
NAME_MAP = {
    "Swedbank": "Swedbank Lietuvoje",
    "SEB": "SEB Lietuvoje",
    "Luminor": "Luminor Lietuva",
    "Citadele": "Citadele bankas",
    "Artea": "Artea",
}

# --- color helpers ---
_ALL_BRANDS_LABEL = "All Brands"
_FALLBACK = "#BDBDBD"

def _normalized(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with Company values mapped to BRAND_COLORS keys."""
    if "Company" not in df.columns:
        return df
    out = df.copy()
    out["Company"] = out["Company"].replace(NAME_MAP)
    return out

def _present_color_map(present_labels) -> dict:
    """Color map covering present labels + neutral for 'All Brands'."""
    m = dict(BRAND_COLORS)
    if _ALL_BRANDS_LABEL in present_labels:
        m[_ALL_BRANDS_LABEL] = _FALLBACK
    # If any unexpected names appear, give them fallback too.
    for b in present_labels:
        if b not in m:
            m[b] = _FALLBACK
    return m

_CATEGORY_ORDER = list(BRAND_COLORS.keys()) + [_ALL_BRANDS_LABEL]
# ---------------------------------------------------------------

def show_articles_for_date_company(df_filtered, selected_date, selected_company):
    """Show articles for a specific date and company"""
    # Convert selected_date to datetime if it's not already
    if isinstance(selected_date, str):
        selected_date = pd.to_datetime(selected_date).date()
    elif hasattr(selected_date, 'date'):
        selected_date = selected_date.date()
    
    # Filter data for the selected date and company
    df_filtered['date_only'] = df_filtered['date'].dt.date
    articles = df_filtered[
        (df_filtered['date_only'] == selected_date) & 
        (df_filtered['normalized_company'] == selected_company)
    ]
    
    if articles.empty:
        st.warning(f"No articles found for {selected_company} on {selected_date.strftime('%B %d, %Y')}")
        return
    
    st.success(f"Found {len(articles)} articles for {selected_company} on {selected_date.strftime('%B %d, %Y')}")
    
    # Display articles in a nice format
    for idx, article in articles.iterrows():
        with st.expander(f"📰 {article.get('Title', 'No Title')[:80]}..."):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Title:** {article.get('Title', 'N/A')}")
                st.markdown(f"**Outlet:** {article.get('Outlet', 'N/A')}")
                st.markdown(f"**Published:** {article.get('Published Date', 'N/A')}")
                
                if pd.notna(article.get('Coverage Snippet')):
                    st.markdown(f"**Snippet:** {article.get('Coverage Snippet', 'N/A')}")
                
                if pd.notna(article.get('Sentiment')):
                    sentiment = article.get('Sentiment', 'N/A')
                    if sentiment == 'Positive':
                        st.markdown(f"**Sentiment:** 🟢 {sentiment}")
                    elif sentiment == 'Negative':
                        st.markdown(f"**Sentiment:** 🔴 {sentiment}")
                    else:
                        st.markdown(f"**Sentiment:** 🟡 {sentiment}")
            
            with col2:
                if pd.notna(article.get('Impressions')):
                    st.metric("Impressions", f"{article.get('Impressions', 0):,}")
                
                if pd.notna(article.get('Link')):
                    st.markdown(f"[🔗 Read Article]({article.get('Link')})")
                else:
                    st.info("No link available")

def render(mode: str = "by_company"):
    """
    Plot article volume trends by day for the selected month.
    mode = "by_company" → lines per brand
    mode = "combined"   → one line summing all volumes
    """
    if mode not in {"by_company", "combined"}:
        st.error(f"Invalid mode '{mode}' in volume_trends.render(). Use 'by_company' or 'combined'.")
        return

    st.subheader("📈 Monthly Media Mention Trends")

    # Load PR data
    df = load_monthly_pr_data()
    
    if df is None or df.empty:
        st.warning("No data available for volume trends.")
        return
    
    # Check if we have the required columns
    if "date" not in df.columns:
        st.error("No 'date' column found in PR data")
        return

    # Get selected date range from sidebar
    try:
        start_date, end_date = get_selected_date_range()
    except Exception as e:
        st.error(f"Error getting selected date range: {e}")
        return

    # Filter data by selected date range
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df_filtered = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    if df_filtered.empty:
        st.warning(f"No data available for the selected period ({start_date.strftime('%B %Y')}).")
        return

    # Get selected brands from session state and filter
    selected_brands = st.session_state.get("selected_brands", [])
    
    if selected_brands:
        # Normalize the company names in the data and filter
        df_filtered['normalized_company'] = df_filtered['company'].apply(lambda x: normalize_brand_name(x, "pr"))
        df_filtered = df_filtered[df_filtered['normalized_company'].isin(selected_brands)]

    if df_filtered.empty:
        st.warning("No data available for the selected brands and period.")
        return

    # Create daily date range for the selected month
    daily_dates = pd.date_range(start=start_date, end=end_date, freq='D')

    # Initialize data structures
    volume_data, impressions_data = [], []

    # Get unique companies from the filtered data
    companies = df_filtered['company'].unique()
    
    for company in companies:
        company_df = df_filtered[df_filtered['company'] == company]
        
        if company_df.empty:
            continue

        # Get normalized company name for display
        normalized_company = normalize_brand_name(company, "pr")

        # Group by day and count articles
        company_df['date_only'] = company_df['date'].dt.date
        daily_counts = company_df.groupby('date_only').size()
        
        # Create a complete daily series with zeros for missing days
        daily_series = pd.Series(0, index=daily_dates.date)
        daily_series.update(daily_counts)

        # Impressions
        if "Impressions" in company_df.columns:
            company_df["Impressions"] = pd.to_numeric(company_df["Impressions"], errors="coerce").fillna(0)
            daily_impressions = company_df.groupby('date_only')["Impressions"].sum()
            daily_impressions_series = pd.Series(0, index=daily_dates.date)
            daily_impressions_series.update(daily_impressions)
        else:
            daily_impressions_series = pd.Series(0, index=daily_dates.date)

        if mode == "by_company":
            for date, count in daily_series.items():
                volume_data.append({"Date": date, "Company": normalized_company, "Volume": count})
            for date, impressions in daily_impressions_series.items():
                impressions_data.append({"Date": date, "Company": normalized_company, "Impressions": impressions})
        else:  # combined
            for date, count in daily_series.items():
                volume_data.append({"Date": date, "Company": _ALL_BRANDS_LABEL, "Volume": count if company == companies[0] else 0})
            for date, impressions in daily_impressions_series.items():
                impressions_data.append({"Date": date, "Company": _ALL_BRANDS_LABEL, "Impressions": impressions if company == companies[0] else 0})

    # Tabs
    tab1, tab2 = st.tabs(["📊 Volume", "👁️ Impressions"])

    # Volume Tab
    with tab1:
        if not volume_data:
            st.warning("No volume data found.")
        else:
            df_volume = pd.DataFrame(volume_data)
            if mode == "combined":
                df_volume = df_volume.groupby("Date", as_index=False).agg({"Volume": "sum"})
                df_volume["Company"] = _ALL_BRANDS_LABEL

            df_volume = _normalized(df_volume)  # <-- normalize names
            
            # Enhanced hover information
            fig_volume = px.line(
                df_volume,
                x="Date",
                y="Volume",
                color="Company",
                markers=True,
                title=f"Daily Media Mentions - {start_date.strftime('%B %Y')}",
                color_discrete_map=_present_color_map(df_volume["Company"].unique()),
                category_orders={"Company": _CATEGORY_ORDER},
                hover_data={"Date": True, "Volume": True, "Company": True}
            )
            
            # Enhanced hover template
            fig_volume.update_traces(
                hovertemplate="<b>%{fullData.name}</b><br>" +
                             "Date: %{x}<br>" +
                             "Articles: %{y}<br>" +
                             "<extra></extra>"
            )
            
            fig_volume.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Articles",
                xaxis=dict(
                    tickmode="auto",
                    tickformat="%d %b"
                )
            )
            st.plotly_chart(fig_volume, use_container_width=True)
            
            # Add drill-down functionality
            st.markdown("---")
            st.markdown("### 🔍 Drill Down: View Articles for Specific Date & Company")
            
            col1, col2 = st.columns(2)
            with col1:
                # Get available dates from the data
                available_dates = sorted(df_volume["Date"].unique())
                selected_date = st.selectbox(
                    "Select Date", 
                    options=available_dates,
                    format_func=lambda x: x.strftime("%B %d, %Y")
                )
            
            with col2:
                # Get available companies for the selected date
                available_companies = df_volume[df_volume["Date"] == selected_date]["Company"].unique()
                if len(available_companies) > 0:
                    selected_company = st.selectbox("Select Company", options=available_companies)
                else:
                    selected_company = None
                    st.info("No data for selected date")
            
            # Show articles button
            if selected_company and st.button("📰 Show Articles", type="primary"):
                show_articles_for_date_company(df_filtered, selected_date, selected_company)

    # Impressions Tab
    with tab2:
        if not impressions_data:
            st.warning("No impressions data found.")
        else:
            df_impressions = pd.DataFrame(impressions_data)
            if mode == "combined":
                df_impressions = df_impressions.groupby("Date", as_index=False).agg({"Impressions": "sum"})
                df_impressions["Company"] = _ALL_BRANDS_LABEL

            df_impressions = _normalized(df_impressions)  # <-- normalize names
            fig_impressions = px.line(
                df_impressions,
                x="Date",
                y="Impressions",
                color="Company",
                markers=True,
                title=f"Daily Total Impressions - {start_date.strftime('%B %Y')}",
                color_discrete_map=_present_color_map(df_impressions["Company"].unique()),
                category_orders={"Company": _CATEGORY_ORDER},
            )
            fig_impressions.update_layout(
                xaxis_title="Date",
                yaxis_title="Total Impressions",
                xaxis=dict(
                    tickmode="auto",
                    tickformat="%d %b"
                )
            )
            st.plotly_chart(fig_impressions, use_container_width=True)
