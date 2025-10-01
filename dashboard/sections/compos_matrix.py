import streamlit as st
import plotly.express as px
from utils.file_io import load_monthly_pr_data
from utils.config import BRANDS, normalize_brand_name
import pandas as pd
from utils.date_utils import get_selected_date_range  # Add this import

def render():
    st.subheader("🏷️ Brand Archetypes: Volume vs. Quality")

    st.markdown("""
    **Note:** News articles were selected from February 1st until July 31st. Only articles where the bank was mentioned in either the title or the first paragraph were kept for analysis.
    """)

    st.markdown("""
    **Quality definition:** The Brand Mention Quality (BMQ) score is a measure of how well the brand is represented in the article. It takes into account the [PageRank]('https://en.wikipedia.org/wiki/PageRank') of the website, how often the brand is mentioned and where the brand is mentioned in the article. The BMQ score ranges from 0 to 1, where 1 is the best possible score.
    """)

    # Load PR data
    df = load_monthly_pr_data()
    
    if df is None or df.empty:
        st.info("No PR data found.")
        return

    summary = {}

    # Check if we have the required columns
    if 'BMQ' not in df.columns or 'company' not in df.columns:
        st.error("Required columns (BMQ, company) not found in PR data")
        return
    
    # Filter data for the selected date range
    start_date, end_date = get_selected_date_range()
    df_filtered = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    # Create summary in original format
    summary = {}
    
    # Get selected brands from session state
    selected_brands = st.session_state.get("selected_brands", [])
    
    # Filter by selected brands using normalized names
    if selected_brands:
        # Normalize the company names in the data and filter
        df_filtered['normalized_company'] = df_filtered['company'].apply(lambda x: normalize_brand_name(x, "pr"))
        df_filtered = df_filtered[df_filtered['normalized_company'].isin(selected_brands)]
    
    # Get unique companies from the filtered data
    companies = df_filtered['company'].unique()
    
    for company in companies:
        company_df = df_filtered[df_filtered['company'] == company]
        
        # Get normalized company name for display
        normalized_company = normalize_brand_name(company, "pr")
        
        volume = len(company_df)  # Use count as volume
        quality = company_df["BMQ"].mean() if "BMQ" in company_df.columns and not company_df.empty else 0

        if "Top Archetype" in company_df.columns and not company_df.empty:
            archetype_counts = company_df["Top Archetype"].value_counts(normalize=True) * 100
            top_3 = archetype_counts.nlargest(3)
            archetype_text = "<br>".join([f"{a} ({p:.1f}%)" for a, p in top_3.items()])
        else:
            archetype_text = "N/A"

        summary[normalized_company] = {
            "Volume": volume,
            "Quality": round(quality, 2) if pd.notna(quality) else 0,
            "Archetypes": archetype_text
        }

    if not summary:
        st.warning("No archetype data found.")
        return

    df_summary = pd.DataFrame.from_dict(summary, orient="index").reset_index()
    df_summary.columns = ["Company", "Volume", "Quality", "Archetypes"]

    fig = px.scatter(
        df_summary,
        x="Volume",
        y="Quality",
        text="Company",
        hover_data=["Archetypes"],
        title="Company Positioning by Volume & Quality",
    )

    fig.update_traces(textposition="top center", marker=dict(size=10))

    for _, row in df_summary.iterrows():
        fig.add_annotation(
            x=row["Volume"],
            y=row["Quality"],
            text=f"<b>{row['Company']}</b><br>{row['Archetypes']}",
            showarrow=False,
            font=dict(size=9),
            align="center",
            bgcolor="white",
            borderpad=4
        )

    fig.update_layout(
        xaxis_title="Volume (Articles)",
        yaxis_title="Quality (Avg. BMQ)",
        margin=dict(l=40, r=40, t=40, b=40),
        dragmode=False
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        'Read more about brand archetypes here: [Brandtypes](https://www.comp-os.com/brandtypes)'
    )
