import streamlit as st
import pandas as pd
from utils.config import BRAND_COLORS, normalize_brand_name, get_brand_column
from utils.date_utils import get_selected_date_range
from utils.file_io import load_monthly_social_media_data

POST_TEXT_COLUMNS = ["content", "post_text", "Post"]

def render(selected_platforms=None):
    if selected_platforms is None:
        selected_platforms = ["facebook"]

    st.subheader("🏆 Top Social Media Posts")


    start_date, end_date = get_selected_date_range()

    # Load social media data
    df = load_monthly_social_media_data()
    
    if df is None or df.empty:
        st.warning("No social media data available.")
        return
    
    # Filter by date range - use the selected month
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

    for platform in selected_platforms:
        st.markdown(f"### {platform.capitalize()}")
        all_posts = []

        # Get the post text column
        post_col = next((col for col in POST_TEXT_COLUMNS if col in df_filtered.columns), None)
        if not post_col:
            st.warning(f"No post content column found for {platform.capitalize()}.")
            continue
        
        # Get URL column - use source_url if available, otherwise url
        url_col = "source_url" if "source_url" in df_filtered.columns else ("url" if "url" in df_filtered.columns else None)
        
        # Calculate engagement using the same logic as data loading
        if "likes" in df_filtered.columns and "num_comments" in df_filtered.columns and "num_shares" in df_filtered.columns:
            # Calculate total engagement: likes + comments*3 + shares*5
            likes = pd.to_numeric(df_filtered["likes"], errors="coerce").fillna(0)
            comments = pd.to_numeric(df_filtered["num_comments"], errors="coerce").fillna(0)
            shares = pd.to_numeric(df_filtered["num_shares"], errors="coerce").fillna(0)
            df_filtered["Engagement"] = likes + comments * 3 + shares * 5
        elif "total_engagement" in df_filtered.columns:
            df_filtered["Engagement"] = pd.to_numeric(df_filtered["total_engagement"], errors="coerce").fillna(0)
        else:
            df_filtered["Engagement"] = 0

        # Filter out posts with no engagement
        df_filtered = df_filtered[df_filtered["Engagement"] > 0]
        if df_filtered.empty:
            st.info(f"No {platform.capitalize()} posts with engagement found.")
            continue

        # Get unique companies and create tabs
        unique_companies = df_filtered['normalized_company'].unique()
        brand_display_names = list(unique_companies)
        tab_labels = ["🌍 Overall"] + [f"🏢 {brand}" for brand in brand_display_names]
        tabs = st.tabs(tab_labels)

        # Prepare all posts data
        for _, row in df_filtered.iterrows():
            preview = str(row[post_col])[:50].replace("\n", " ").strip()
            url = row[url_col] if url_col and pd.notna(row[url_col]) else "#"
            # Make the post preview clickable if URL is available
            if url != "#" and url:
                link = f"[{preview}...]({url})"
            else:
                link = preview
            all_posts.append({
                "Company": row['normalized_company'],
                "Date": row["date"].strftime('%Y-%m-%d') if pd.notna(row["date"]) else "Unknown",
                "Post": link,
                "Engagement": int(row["Engagement"])
            })

        if not all_posts:
            st.info(f"No {platform.capitalize()} posts found.")
            continue

        df_all = pd.DataFrame(all_posts).sort_values(by="Engagement", ascending=False)

        # Overall tab
        with tabs[0]:
            st.markdown("**Top 5 posts overall**")
            st.markdown(df_all.head(5).to_markdown(index=False), unsafe_allow_html=True)

        # Company-specific tabs
        for i, brand_display in enumerate(brand_display_names, start=1):
            with tabs[i]:
                brand_df = df_all[df_all["Company"] == brand_display]
                if brand_df.empty:
                    st.info(f"No posts for {brand_display}.")
                else:
                    st.markdown(f"**Top posts for {brand_display}**")
                    st.markdown(brand_df.head(5).to_markdown(index=False), unsafe_allow_html=True)
