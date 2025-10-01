import streamlit as st
import pandas as pd
import json
import os
from config import get_keys_file_path
from src.utils.utils import extract_date, filter_data_by_date_range

def create_topic_analysis(start_date, end_date):
    """
    Create and display key topics analysis showing main themes across all companies.
    
    Args:
        start_date: Start date for filtering
        end_date: End date for filtering
    """
    st.subheader("Key Topics")

    st.markdown("Key topics reflect main themes across all of the communicating companies: **Data is filtered based on your selected date range.**")

    # Load company-file mappings from JSON
    keys_file = get_keys_file_path()
    
    if not os.path.exists(keys_file):
        st.error("Error: keys.txt file is missing in the data folder!")
        return

    with open(keys_file, "r") as f:
        keys_data = json.load(f)

    # Initialize a dictionary to store topic counts for all companies
    topic_counts = {
        "Cluster_Topic1": {},
        "Cluster_Topic2": {},
        "Cluster_Topic3": {}
    }

    # Loop through each company and extract topic counts
    for company, filename in keys_data.items():
        file_path = os.path.join("data", "data august", filename)

        if os.path.exists(file_path):
            df = pd.read_excel(file_path, sheet_name="Raw Data")

            # Check if "Date" column exists, if not, create it
            if "Date" not in df.columns:
                df["Date"] = df["Snippet"].apply(lambda x: extract_date(x) if isinstance(x, str) else None)
            
            # Filter by date range
            df_filtered = filter_data_by_date_range(df, "Date", start_date, end_date)

            # Ensure the necessary topic columns exist
            if "Cluster_Topic1" in df_filtered.columns and "Cluster_Topic2" in df_filtered.columns and "Cluster_Topic3" in df_filtered.columns:
                # Process topics (Cluster_Topic1, Cluster_Topic2, Cluster_Topic3)
                for column in ["Cluster_Topic1", "Cluster_Topic2", "Cluster_Topic3"]:
                    for topic in df_filtered[column].dropna():  # Drop NaN values
                        if topic in topic_counts[column]:
                            topic_counts[column][topic] += 1
                        else:
                            topic_counts[column][topic] = 1

    # Flatten the topic counts into a single list (combine counts from all columns)
    all_topic_counts = {}

    for column in topic_counts:
        for topic, count in topic_counts[column].items():
            if topic in all_topic_counts:
                all_topic_counts[topic] += count
            else:
                all_topic_counts[topic] = count

    # Get the top 5 topics based on total count across all companies
    sorted_topics = sorted(all_topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Prepare the data for display
    topics_data = []
    total_count = sum(all_topic_counts.values())

    for topic, count in sorted_topics:
        percentage = (count / total_count) * 100
        topics_data.append({"Topic Cluster": topic, "Count": count, "Percentage": round(percentage, 2)})

    # Create a DataFrame for the top 5 topics
    key_topics_df = pd.DataFrame(topics_data)

    # Display the key topics box design
    for _, row in key_topics_df.iterrows():
        st.markdown(
            f'<div style="display: flex; justify-content: space-between; border: 1px solid #ccc; padding: 5px; border-radius: 5px; margin-bottom: 5px;">'
            f'<div style="background-color: white; padding: 5px; border-radius: 5px; flex: 1;">{row["Topic Cluster"]}</div>'
            f'<div style="background-color: lightgray; padding: 5px; border-radius: 5px; margin-left: 10px;">{row["Percentage"]}%</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)  # Adds one line of vertical space
    st.markdown("<br>", unsafe_allow_html=True)  # Adds one line of vertical space
