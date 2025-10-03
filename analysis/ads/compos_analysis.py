"""
CompOS (Content Positioning) Analysis - Archetype Assignment
"""
import pandas as pd
import os
from typing import Dict, Any, List
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from tqdm import tqdm
from config import OPENAI_API_KEY, DEFAULT_MODEL, MAX_WORKERS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

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

def assign_archetype(text: str, idx: int) -> tuple:
    """
    Assign archetype to a single piece of content
    Returns (index, archetype)
    """
    if not text or str(text).strip() == '' or str(text).lower() == 'nan':
        return idx, "No Content"
    
    try:
        completion = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": ARCHETYPE_PROMPT},
                {"role": "user", "content": str(text)}
            ],
            temperature=0
        )
        output = completion.choices[0].message.content
        
        # Parse the output to extract archetype
        top_archetype = None
        for line in output.splitlines():
            if "Top Archetype" in line:
                _, value = line.split(":", 1)
                top_archetype = value.strip()
                break
        
        return idx, top_archetype or "Parsing Error"
        
    except Exception as e:
        logger.error(f"Error assigning archetype at index {idx}: {e}")
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
    Run CompOS analysis for ads data for a specific month
    Returns path to output file
    """
    from utils.data_processor import load_new_data
    from config import MEDIA_TYPES
    
    # Load and filter ads data for the month
    df = load_new_data("ads", year, month)
    if len(df) == 0:
        raise ValueError(f"No ads data found for {year}-{month:02d}")
    
    # Get text column from config
    text_column = MEDIA_TYPES["ads"]["text_column"]
    
    # Run analysis
    df_analyzed = run_compos_analysis(df, text_column)
    
    # Save results directly in the analysis folder
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, f"compos_analysis_ads.xlsx")
    df_analyzed.to_excel(output_file, index=False)
    
    logger.info(f"CompOS analysis saved to: {output_file}")
    return output_file

def get_archetype_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics for archetype analysis
    """
    if "Top Archetype" not in df.columns:
        return {"error": "No archetype data found"}
    
    archetype_counts = df["Top Archetype"].value_counts()
    
    summary = {
        "total_items": len(df),
        "archetype_distribution": archetype_counts.to_dict(),
        "top_archetype": archetype_counts.index[0] if len(archetype_counts) > 0 else None,
        "top_archetype_percentage": (archetype_counts.iloc[0] / len(df) * 100) if len(archetype_counts) > 0 else 0
    }
    
    return summary
