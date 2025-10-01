# sections/content_pillars.py

import streamlit as st
from utils.config import BRAND_NAME_MAPPING
from utils.file_io import load_content_pillar_outputs

def render():
    try:
        content_pillar_outputs = load_content_pillar_outputs()
        if content_pillar_outputs is None:
            st.warning("No analysis data found.")
            return

        st.subheader("🏛️ Content Pillar Analysis")

        if not content_pillar_outputs:
            st.warning("No analysis data found.")
            return

        # Add dropdown to select brand
        brand_options = list(content_pillar_outputs.keys())
        # Filter out __summary__ from dropdown if it exists
        brand_options = [brand for brand in brand_options if brand != "__summary__"]
        
        if not brand_options:
            st.warning("No brand data available.")
            return
            
        selected_brand = st.selectbox("Select Brand", brand_options)
        
        if selected_brand not in content_pillar_outputs:
            st.error(f"Selected brand '{selected_brand}' not found in data.")
            return
            
        data = content_pillar_outputs[selected_brand]
        
        if isinstance(data, str):
            st.error(f"Error for {selected_brand}: {data}")
            return

        brand_display = BRAND_NAME_MAPPING.get(selected_brand, selected_brand)
        st.header(f"🏛️ {brand_display}")
        
        is_summary_brand = str(selected_brand).strip().lower() == "__summary__"

        for theme in data:
            st.header(theme.get('theme', ''))

            # Display share and posts count if available
            share = theme.get('share', 'N/A')
            posts_count = theme.get('posts_count', 'N/A')
            if share != 'N/A' or posts_count != 'N/A':
                st.write(f"Share: {share} | Posts: {posts_count}")

            if is_summary_brand:
                # For __summary__ brand: no Subtopics; show only Examples full width
                st.subheader("Examples")
                for example in theme.get('posts', []):
                    st.markdown(f'"{example}"')
            else:
                # Original 2-column layout
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Subtopics")
                    for subtopic in theme.get('subtopics', []):
                        name = str(subtopic.get('subtopic', '')).strip()
                        desc = str(subtopic.get('description', '')).strip()
                        st.markdown(f"**{name}**: {desc}")

                with col2:
                    st.subheader("Examples")
                    for example in theme.get('posts', []):
                        st.markdown(f'"{example}"')

            st.markdown("---")

    except Exception as e:
        st.error("🚨 Failed to load content pillar analysis.")
        st.exception(e)
