"""
Social Media CompOS Analysis - Archetype Assignment
"""
import os
import json
import logging
from typing import Dict, Any, List
import pandas as pd
from tqdm import tqdm
from tenacity import retry, wait_exponential, stop_after_attempt
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import OPENAI_API_KEY, DEFAULT_MODEL, MAX_WORKERS, MEDIA_TYPES

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Use the same archetype prompt as ads
ARCHETYPE_PROMPT = """As a senior Public Relations and Branding Communication expert you are interested in how companies are positioned by their content.
Your task will be to analyze content and assign the best-fitting archetype to each item, based on the following framework:

1. The Futurist (innovative, disruptive, pioneering, visionary)
2. The Eco Warrior (ecological, sustainable, environmental, renewable)
3. The Technologist (technological, automated, smart, integrated)
4. The Mentor (guiding, insightful, informative, supportive)
5. The Collaborator (community, collaborative, teamwork, partner)
6. The People's Champion (democratic, inclusive, empowering, friendly)
7. The Nurturer (caring, understanding, nurturing, encouraging)
8. The Simplifier (simple, easy, simplifying, effortless)
9. The Expert (intelligent, expert, specialized, scientific)
10. The Value-Seeker (cost-effective, affordable, economical, low-cost)
11. The Personalizer (adaptive, tailored, personalized, customized)
12. The Accelerator (agile, instant, fast, enabling)
13. The Guardian (safe, secure, dependable, encrypted)
14. The Principled (honest, transparent, fair, responsible)
15. The Jet-Setter (global, international, largest, leading)
16. The Optimizer (efficient, optimized, streamlined, frictionless)

Please make sure to always respond in the following format:

Top Archetype: [Top Archetype]
"""

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def assign_archetype(text: str, idx: int) -> tuple[int, str]:
    """Assign archetype to a single social media post"""
    if not text or str(text).strip() == '' or str(text).lower() == 'nan':
        return idx, "No Content"
    
    try:
        completion = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": ARCHETYPE_PROMPT},
                {"role": "user", "content": str(text)}
            ],
            temperature=0.1,
            max_tokens=100
        )
        
        response = completion.choices[0].message.content.strip()
        
        # Extract archetype from response
        if "Top Archetype:" in response:
            archetype = response.split("Top Archetype:")[1].strip()
        else:
            archetype = response.strip()
        
        # Clean up the archetype name
        archetype = archetype.replace("The ", "").strip()
        
        return idx, archetype
        
    except Exception as e:
        logger.error(f"Error assigning archetype to post {idx}: {e}")
        return idx, "Error"

def run_compos_analysis(df: pd.DataFrame, text_column: str, 
                       max_workers: int = MAX_WORKERS) -> pd.DataFrame:
    """
    Run CompOS analysis on dataframe
    Adds 'Top Archetype' column to the dataframe
    """
    logger.info(f"Starting CompOS analysis on {len(df)} items...")
    
    # Prepare data for parallel processing
    results = []
    futures = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for idx, text in enumerate(df[text_column]):
            future = executor.submit(assign_archetype, text, idx)
            futures[future] = idx
        
        # Collect results as they complete with progress bar
        for future in tqdm(as_completed(futures), total=len(futures), desc="Assigning archetypes"):
            try:
                idx, archetype = future.result()
                results.append((idx, archetype))
            except Exception as e:
                idx = futures[future]
                logger.error(f"Error processing item at index {idx}: {e}")
                results.append((idx, "Error"))
    
    # Sort results by index to maintain order
    results.sort(key=lambda x: x[0])
    
    # Add archetype column to dataframe
    df_result = df.copy()
    df_result["Top Archetype"] = [result[1] for result in results]
    
    logger.info("CompOS analysis complete.")
    return df_result

def analyze_compos_for_month(year: int, month: int, output_folder: str) -> str:
    """
    Run CompOS analysis for social media data for a specific month
    
    Args:
        year: Year to analyze
        month: Month to analyze (1-12)
        output_folder: Folder to save results
        
    Returns:
        Path to saved file
    """
    from utils.data_processor import load_new_data
    from config import MEDIA_TYPES
    
    # Load and filter social media data for the month
    df = load_new_data("social_media", year, month)
    
    if len(df) == 0:
        logger.warning(f"No social media data found for {year}-{month:02d}")
        return None
    
    # Get text column from config
    text_column = MEDIA_TYPES["social_media"]["text_column"]
    
    # Run analysis
    df_analyzed = run_compos_analysis(df, text_column)
    
    # Save results
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, f"compos_analysis_social_media.xlsx")
    
    # Remove timezone info from datetime columns before saving
    df_export = df_analyzed.copy()
    for col in df_export.columns:
        if df_export[col].dtype == 'datetime64[ns, UTC]':
            df_export[col] = df_export[col].dt.tz_localize(None)
    
    df_export.to_excel(output_file, index=False)
    
    logger.info(f"CompOS analysis saved to: {output_file}")
    return output_file
