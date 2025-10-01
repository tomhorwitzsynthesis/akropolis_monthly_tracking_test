import streamlit as st
import pandas as pd
import plotly.express as px
from utils.file_io import load_monthly_pr_data
from utils.config import normalize_brand_name
from utils.date_utils import get_selected_date_range

def render() -> None:
    st.subheader("🧠 Key Communication Topics with Examples")

    # Load PR data
    df = load_monthly_pr_data()
    
    if df is None or df.empty:
        st.warning("No PR data available.")
        return
    
    # Check if we have the required columns
    topic_columns = ['Cluster_Topic1', 'Cluster_Topic2', 'Cluster_Topic3']
    missing_columns = [col for col in topic_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Missing topic columns: {missing_columns}")
        return

    # Filter by date range
    start_date, end_date = get_selected_date_range()
    df_filtered = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    # Get selected brands from session state and filter
    selected_brands = st.session_state.get("selected_brands", [])
    
    if selected_brands:
        # Normalize the company names in the data and filter
        df_filtered['normalized_company'] = df_filtered['company'].apply(lambda x: normalize_brand_name(x, "pr"))
        df_filtered = df_filtered[df_filtered['normalized_company'].isin(selected_brands)]
    
    if df_filtered.empty:
        st.warning("No data available for the selected period.")
        return

    # Collect all topics from the three cluster topic columns
    all_topics = []
    for col in topic_columns:
        topics = df_filtered[col].dropna().tolist()
        all_topics.extend(topics)
    
    if not all_topics:
        st.warning("No topic data available.")
        return
    
    # Count topics and calculate percentages
    topic_counts = pd.Series(all_topics).value_counts()
    topic_percentages = (topic_counts / len(all_topics) * 100).round(1)
    
    # Create topic summary by company
    company_topic_data = []
    companies = df_filtered['company'].unique()
    
    for company in companies:
        company_df = df_filtered[df_filtered['company'] == company]
        company_topics = []
        
        # Get normalized company name for display
        normalized_company = normalize_brand_name(company, "pr")
        
        for col in topic_columns:
            topics = company_df[col].dropna().tolist()
            company_topics.extend(topics)
        
        if company_topics:
            company_topic_counts = pd.Series(company_topics).value_counts()
            company_topic_percentages = (company_topic_counts / len(company_topics) * 100).round(1)
            
            for topic, percentage in company_topic_percentages.items():
                company_topic_data.append({
                    'Company': normalized_company,
                    'Topic': topic,
                    'Percentage': percentage,
                    'Count': company_topic_counts[topic]
                })
    
    # Display key topics with company tabs
    st.markdown("Key topics reflect main themes across all of the communicating companies: **Data is filtered based on your selected date range.**")
    
    # Add company tabs for detailed topic breakdown
    if company_topic_data:
        st.markdown("### 🏢 Topic Distribution by Company")
        
        # Create tabs for each company
        companies_with_data = list(set([item['Company'] for item in company_topic_data]))
        # Sort companies for consistent tab order
        companies_with_data.sort()
        tabs = st.tabs([f"🏢 {company}" for company in companies_with_data])
        
        for i, company in enumerate(companies_with_data):
            with tabs[i]:
                company_data = [item for item in company_topic_data if item['Company'] == company]
                company_df = pd.DataFrame(company_data)
                
                if not company_df.empty:
                    # Sort by percentage descending
                    company_df = company_df.sort_values('Percentage', ascending=False)
                    
                    # Display topics for this company in the same box format
                    for _, row in company_df.iterrows():
                        st.markdown(
                            f'<div style="display: flex; justify-content: space-between; border: 1px solid #ccc; padding: 5px; border-radius: 5px; margin-bottom: 5px;">'
                            f'<div style="background-color: white; padding: 5px; border-radius: 5px; flex: 1;">{row["Topic"]}</div>'
                            f'<div style="background-color: lightgray; padding: 5px; border-radius: 5px; margin-left: 10px;">{row["Percentage"]}%</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.info(f"No topic data available for {company}")
    
    st.markdown("<br>", unsafe_allow_html=True)  # Adds one line of vertical space
