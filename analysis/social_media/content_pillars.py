"""
Content Pillars Analysis for Social Media
Based on the monthly_update/content_pillars.py code
"""

import os
import pickle
import pandas as pd
import logging
from openai import OpenAI
from config import OPENAI_API_KEY, MEDIA_TYPES, MIN_POSTS_FOR_ANALYSIS
from utils.data_processor import load_new_data

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Content Pillar Prompt Template
CONTENT_PILLAR_PROMPT_TEMPLATE = """You are performing a topical analysis of social media posts.

Please ALWAYS respond in English, even if the input is not in English, but leave the examples in the original language.

Here are the posts:
"{content}"

Analyze the content and classify it into main themes. Be conservative with the number of themes - only create themes that are truly distinct and meaningful.
Some rules for the number of main themes:
- For 5-10 posts: A maximum of 2-3 themes.
- For 11-20 posts: A maximum of 3-4 themes.
- For 21+ posts: A maximum of 4-5 themes.

For each theme, provide:
1. A clear theme name
2. A brief description of what this theme covers
3. 2-3 subtopics that fall under this theme
4. 2-3 specific examples with EXACT QUOTES from the actual posts (use quotation marks)

Format your response EXACTLY as follows:

THEME: [Theme Name]
DESCRIPTION: [Brief description of the theme]
SHARE: [Percentage of content that falls under this theme]%
POSTS_COUNT: [Number of posts that fall under this theme]
SUBTOPICS:
- [Subtopic 1]: [Description]
- [Subtopic 2]: [Description]
- [Subtopic 3]: [Description]
POSTS:
- "[Exact quote from actual post 1]"
- "[Exact quote from actual post 2]"
- "[Exact quote from actual post 3]"

THEME: [Next Theme Name]
DESCRIPTION: [Brief description of the theme]
SHARE: [Percentage of content that falls under this theme]%
POSTS_COUNT: [Number of posts that fall under this theme]
SUBTOPICS:
- [Subtopic 1]: [Description]
- [Subtopic 2]: [Description]
POSTS:
- "[Exact quote from actual post 1]"
- "[Exact quote from actual post 2]"

Continue this format for all themes."""

# Genericity Comparison Prompt Template
GENERICITY_COMPARISON_PROMPT_TEMPLATE = """
You are a senior content strategist analyzing content pillar structures across multiple companies.

You will receive structured content pillar data from multiple brands.

Your tasks:
1. Identify and group themes into THREE buckets:
   - MOST GENERIC THEMES (appear in nearly all companies)
   - MODERATELY DIFFERENTIATED THEMES (appear in some, but not all)
   - MOST DIFFERENTIATED THEMES (unique or nearly unique to a single brand)

2. For each bucket, list the themes with brief explanations

3. Provide a ranking of companies from MOST GENERIC to MOST DIFFERENTIATED

Format your response as:

MOST GENERIC THEMES:
THEME: [Theme Name] - [Brief explanation of why it's generic]

MODERATELY DIFFERENTIATED THEMES:
THEME: [Theme Name] - [Brief explanation]

MOST DIFFERENTIATED THEMES:
THEME: [Theme Name] - [Brief explanation of what makes it unique]

COMPANY DIFFERENTIATION RANKING:
1. [Company Name] - [Brief explanation]
2. [Company Name] - [Brief explanation]
3. [Company Name] - [Brief explanation]
"""

def parse_response_to_structure(response_text):
    """Parse the GPT response into structured data"""
    themes = []
    current_theme = None
    in_subtopics = False
    in_posts = False
    
    for line in response_text.splitlines():
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("THEME:"):
            if current_theme:
                themes.append(current_theme)
            current_theme = {
                "theme": line.replace("THEME:", "").strip(),
                "description": "",
                "share": "",
                "posts_count": "",
                "subtopics": [],
                "posts": []
            }
            in_subtopics = False
            in_posts = False
        elif line.startswith("DESCRIPTION:"):
            if current_theme:
                current_theme["description"] = line.replace("DESCRIPTION:", "").strip()
        elif line.startswith("SHARE:"):
            if current_theme:
                current_theme["share"] = line.replace("SHARE:", "").strip()
        elif line.startswith("POSTS_COUNT:"):
            if current_theme:
                current_theme["posts_count"] = line.replace("POSTS_COUNT:", "").strip()
        elif line.startswith("SUBTOPICS:"):
            in_subtopics = True
            in_posts = False
        elif line.startswith("POSTS:"):
            in_subtopics = False
            in_posts = True
        elif line.startswith("- ") and current_theme:
            content = line[2:].strip()
            if in_subtopics:
                # This is a subtopic
                if ":" in content:
                    subtopic, description = content.split(":", 1)
                    current_theme["subtopics"].append({
                        "subtopic": subtopic.strip(),
                        "description": description.strip()
                    })
            elif in_posts:
                # This is a post example - remove quotes if present
                if content.startswith('"') and content.endswith('"'):
                    content = content[1:-1]
                current_theme["posts"].append(content)
    
    if current_theme:
        themes.append(current_theme)
    
    return themes

def parse_summary_to_rows(summary_text):
    """Parse the genericity summary into structured rows"""
    structured = []
    ranking = []
    
    current_section = None
    
    for line in summary_text.splitlines():
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("MOST GENERIC THEMES:"):
            current_section = "MOST GENERIC THEMES"
        elif line.startswith("MODERATELY DIFFERENTIATED THEMES:"):
            current_section = "MODERATELY DIFFERENTIATED THEMES"
        elif line.startswith("MOST DIFFERENTIATED THEMES:"):
            current_section = "MOST DIFFERENTIATED THEMES"
        elif line.startswith("COMPANY DIFFERENTIATION RANKING:"):
            current_section = "RANKING"
        elif line.startswith("THEME:") and current_section:
            theme_info = line.replace("THEME:", "").strip()
            if " - " in theme_info:
                title, desc = theme_info.split(" - ", 1)
                structured.append([current_section, title.strip(), desc.strip()])
        elif line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")) and current_section == "RANKING":
            ranking.append(line.strip())
    
    return structured, ranking

def get_available_filename(base_name):
    """Generate an available filename with timestamp"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{base_name}_social_media_{timestamp}.xlsx"

def analyze_content_pillars_for_month(year: int, month: int, output_folder: str) -> str:
    """
    Analyze content pillars for social media data for a specific month
    
    Args:
        year: Analysis year
        month: Analysis month
        output_folder: Output folder path
        
    Returns:
        Path to the saved pickle file
    """
    logger.info(f"Starting content pillars analysis for social_media {year}-{month:02d}")
    
    # Load data
    df = load_new_data("social_media", year, month)
    if df is None or df.empty:
        logger.error("No data loaded for content pillars analysis")
        return None
    
    logger.info(f"Loaded {len(df)} social media items for content pillars analysis")
    
    content_pillar_outputs = {}
    
    # Check if we have brand/company column
    brand_column = MEDIA_TYPES["social_media"]["brand_column"]
    text_column = MEDIA_TYPES["social_media"]["text_column"]
    
    if brand_column in df.columns:
        logger.info(f"'{brand_column}' column detected. Running analysis per brand...")
        brands = df[brand_column].dropna().unique()
        
        for brand in brands:
            logger.info(f"Processing brand: {brand}")
            brand_df = df[df[brand_column] == brand]
            texts = brand_df[text_column].dropna().tolist()
            
            if not texts:
                logger.warning(f"No content found for brand {brand}. Skipping.")
                continue
            
            if len(texts) < MIN_POSTS_FOR_ANALYSIS:
                logger.warning(f"Brand {brand} has only {len(texts)} posts (minimum required: {MIN_POSTS_FOR_ANALYSIS}). Excluding from analysis.")
                continue
            
            merged_text = "\n".join(texts)
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": CONTENT_PILLAR_PROMPT_TEMPLATE},
                        {"role": "user", "content": merged_text}
                    ],
                    temperature=0
                )
                structured = parse_response_to_structure(response.choices[0].message.content)
                content_pillar_outputs[brand] = structured
                logger.info(f"Successfully processed brand: {brand}")
                
            except Exception as e:
                logger.error(f"Error processing brand {brand}: {e}")
                content_pillar_outputs[brand] = f"Error: {e}"
    else:
        logger.warning(f"No '{brand_column}' column detected. Running analysis on full content set...")
        texts = df[text_column].dropna().tolist()
        
        if not texts:
            logger.error("No content found. Exiting function.")
            return None
        
        merged_text = "\n".join(texts)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": CONTENT_PILLAR_PROMPT_TEMPLATE},
                    {"role": "user", "content": merged_text}
                ],
                temperature=0
            )
            structured = parse_response_to_structure(response.choices[0].message.content)
            content_pillar_outputs['Overall'] = structured
            logger.info("Successfully processed overall content.")
            
        except Exception as e:
            logger.error(f"Error processing overall content: {e}")
            content_pillar_outputs['Overall'] = f"Error: {e}"
    
    # Run Genericity Summary
    def format_company_data_for_comparison(content_data):
        lines = []
        for company, themes in content_data.items():
            if company == '__summary__' or isinstance(themes, str):
                continue
            lines.append(f"Company: {company}")
            for theme in themes:
                lines.append(f"THEME: {theme['theme']}")
                for sub in theme['subtopics']:
                    lines.append(f"  SUBTOPIC: {sub['subtopic']} - {sub['description']}")
                for ex in theme['posts']:
                    lines.append(f"  EXAMPLE: {ex}")
            lines.append("")
        return "\n".join(lines)
    
    try:
        logger.info("Running genericity comparison across companies...")
        comparison_input = format_company_data_for_comparison(content_pillar_outputs)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": GENERICITY_COMPARISON_PROMPT_TEMPLATE},
                {"role": "user", "content": comparison_input}
            ],
            temperature=0
        )
        summary_text = response.choices[0].message.content
        summary_structured, summary_ranking = parse_summary_to_rows(summary_text)
        
        summary_themes = []
        current_theme = None
        
        for row in summary_structured:
            section, title, desc = row
            if section in ["MOST GENERIC THEMES", "MODERATELY DIFFERENTIATED THEMES", "MOST DIFFERENTIATED THEMES"]:
                current_theme = {
                    "theme": f"{section.title()}: {title}",
                    "examples": []
                }
                summary_themes.append(current_theme)
            elif section == "THEME_EXAMPLE" and current_theme:
                current_theme["examples"].append(f"{title}: {desc}")
        
        # Append ranking as a separate section
        summary_themes.append({
            "theme": "COMPANY DIFFERENTIATION RANKING",
            "examples": summary_ranking
        })
        
        content_pillar_outputs['__summary__'] = summary_themes
        logger.info("Genericity summary created.")
    except Exception as e:
        logger.error(f"Error during genericity comparison: {e}")
        content_pillar_outputs['__summary__'] = f"Error generating summary: {e}"
    
    # Save output to pickle
    pickle_file = os.path.join(output_folder, "content_pillar_outputs.pkl")
    logger.info(f"Saving output to {pickle_file}...")
    
    try:
        with open(pickle_file, "wb") as f:
            pickle.dump(content_pillar_outputs, f)
        logger.info("content_pillar_outputs.pkl successfully created.")
    except Exception as e:
        logger.error(f"Error saving pickle file: {e}")
        return None
    
    # Save output to Excel
    excel_file = os.path.join(output_folder, "content_pillar_analysis_social_media.xlsx")
    logger.info(f"Saving output to Excel file: {excel_file}")
    
    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            for brand, structured_content in content_pillar_outputs.items():
                if brand == '__summary__':
                    rows = []
                    for theme in structured_content:
                        theme_title = theme["theme"]
                        for example in theme["examples"]:
                            rows.append({
                                "Theme": theme_title,
                                "Example": example
                            })
                    if rows:
                        summary_df = pd.DataFrame(rows)
                        summary_df.to_excel(writer, sheet_name="Summary", index=False)
                else:
                    if isinstance(structured_content, str):
                        # Error case
                        error_df = pd.DataFrame([{"Error": structured_content}])
                        error_df.to_excel(writer, sheet_name=f"{brand}_Error", index=False)
                    else:
                        rows = []
                        for theme in structured_content:
                            theme_name = theme["theme"]
                            description = theme["description"]
                            share = theme["share"]
                            posts_count = theme.get("posts_count", "")
                            
                            # Add subtopics
                            for subtopic in theme["subtopics"]:
                                rows.append({
                                    "Theme": theme_name,
                                    "Description": description,
                                    "Share": share,
                                    "Posts Count": posts_count,
                                    "Type": "Subtopic",
                                    "Content": f"{subtopic['subtopic']}: {subtopic['description']}"
                                })
                            
                            # Add posts
                            for post in theme["posts"]:
                                rows.append({
                                    "Theme": theme_name,
                                    "Description": description,
                                    "Share": share,
                                    "Posts Count": posts_count,
                                    "Type": "Post Example",
                                    "Content": post
                                })
                        
                        if rows:
                            brand_df = pd.DataFrame(rows)
                            # Clean sheet name (Excel has 31 char limit)
                            sheet_name = str(brand)[:31] if str(brand).strip() else "Unknown"
                            brand_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        logger.info(f"Excel file saved: {excel_file}")
    except Exception as e:
        logger.error(f"Error saving Excel file: {e}")
    
    logger.info("Content pillars analysis complete.")
    return pickle_file
