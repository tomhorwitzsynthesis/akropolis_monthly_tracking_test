"""
Key Advantages Analysis - Extract key benefits and advantages from content
"""
import os
import json
import re
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
from openai import OpenAI
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from config import OPENAI_API_KEY, DEFAULT_MODEL, MEDIA_TYPES, MIN_ADS_FOR_ANALYSIS, MAX_WORKERS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Configuration
TEMPERATURE = 0
TOP_N = 50

# Media-specific prompts
MEDIA_PROMPTS = {
    "ads": {
        "system": "You are auditing advertising copy. Output only valid JSON. Each advantage must have: title (short, English), category, evidence[], examples[] (with ad_index + quote). Categories: Try to find common categories within the ads that are used the most often. Make sure that the category has AT LEAST 2 ADS THAT RELATE TO IT DIRECTLY. Evidence: Write 2-3 sentences explaining what the key advantages are for this category. Examples: NEVER use the same ad twice as examples, write the original ad and the English translation after it in brackets.",
        "user": "Extract 1–5 recurring benefits from the ads. Only use explicit info. 'quote:' should include both the ad quote and the translation. Make sure that the category has AT LEAST 2 ADS THAT RELATE TO IT DIRECTLY. NEVER USE THE SAME EXAMPLE TWICE. JSON format: { 'company': '...', 'advantages': [{ 'title': '...', 'category': '...', 'evidence': ['...','...'], 'examples': [{'ad_index': 1, 'quote': '...'}, {'ad_index': 3, 'quote': '...'}] }] }"
    },
    "pr": {
        "system": "You are auditing PR content and press releases. Output only valid JSON. Each advantage must have: title (short, English), category, evidence[], examples[] (with article_index + quote). Categories: Try to find common categories within the PR materials that are used the most often. Make sure that the category has AT LEAST 2 ARTICLES THAT RELATE TO IT DIRECTLY. Evidence: Write 2-3 sentences explaining what the key advantages are for this category. Examples: NEVER use the same article twice as examples, write the original quote and the English translation after it in brackets.",
        "user": "Extract 1–5 recurring benefits from the PR materials. Only use explicit info. 'quote:' should include both the original quote and the translation. Make sure that the category has AT LEAST 2 ARTICLES THAT RELATE TO IT DIRECTLY. NEVER USE THE SAME EXAMPLE TWICE. JSON format: { 'company': '...', 'advantages': [{ 'title': '...', 'category': '...', 'evidence': ['...','...'], 'examples': [{'article_index': 1, 'quote': '...'}, {'article_index': 3, 'quote': '...'}] }] }"
    },
    "social_media": {
        "system": "You are auditing social media content and LinkedIn posts. Output only valid JSON. Each advantage must have: title (short, English), category, evidence[], examples[] (with post_index + quote). Categories: Try to find common categories within the social media posts that are used the most often. Make sure that the category has AT LEAST 2 POSTS THAT RELATE TO IT DIRECTLY. Evidence: Write 2-3 sentences explaining what the key advantages are for this category. Examples: NEVER use the same post twice as examples, write the original quote and the English translation after it in brackets.",
        "user": "Extract 1–5 recurring benefits from the social media posts. Only use explicit info. 'quote:' should include both the original quote and the translation. Make sure that the category has AT LEAST 2 POSTS THAT RELATE TO IT DIRECTLY. NEVER USE THE SAME EXAMPLE TWICE. JSON format: { 'company': '...', 'advantages': [{ 'title': '...', 'category': '...', 'evidence': ['...','...'], 'examples': [{'post_index': 1, 'quote': '...'}, {'post_index': 3, 'quote': '...'}] }] }"
    }
}

def preprocess_data(df: pd.DataFrame, media_type: str) -> pd.DataFrame:
    """Preprocess data for key advantages analysis"""
    if media_type not in MEDIA_TYPES:
        raise ValueError(f"Unknown media type: {media_type}")
    
    media_config = MEDIA_TYPES[media_type]
    company_col = media_config["brand_column"]
    text_col = media_config["text_column"]
    reach_col = media_config["reach_column"]
    
    df = df.copy()
    df = df.dropna(subset=[company_col, text_col])
    
    # Coerce reach safely
    df.loc[:, reach_col] = pd.to_numeric(df[reach_col], errors="coerce").fillna(0)
    
    # Rank top N by reach per company
    df = df.sort_values([company_col, reach_col], ascending=[True, False])
    df.loc[:, "__rank"] = df.groupby(company_col)[reach_col].rank(method="first", ascending=False)
    df = df[df["__rank"] <= TOP_N].drop(columns="__rank")
    
    return df

def to_iso(val):
    """Return YYYY-MM-DD for strings/Timestamps; None if invalid/NaT."""
    ts = pd.to_datetime(val, errors="coerce", utc=True)
    if pd.isna(ts):
        return None
    return ts.date().isoformat()

def build_payload(group_df: pd.DataFrame, media_type: str) -> dict:
    """Build payload for OpenAI analysis"""
    if media_type not in MEDIA_TYPES:
        raise ValueError(f"Unknown media type: {media_type}")
    
    media_config = MEDIA_TYPES[media_type]
    company_col = media_config["brand_column"]
    text_col = media_config["text_column"]
    reach_col = media_config["reach_column"]
    
    company_name = group_df[company_col].iloc[0]
    # Reduced logging for cleaner output
    
    items = []
    for i, (_, row) in enumerate(group_df.iterrows(), start=1):
        txt = row[text_col]
        txt = str(txt).strip() if isinstance(txt, str) else ""
        
        # Handle date columns if they exist
        start_iso = None
        end_iso = None
        if "startDateFormatted" in row:
            start_iso = to_iso(row["startDateFormatted"])
        if "endDateFormatted" in row:
            end_iso = to_iso(row["endDateFormatted"])
        
        items.append({
            "index": i,
            "text": txt,
            "reach": float(pd.to_numeric(row.get(reach_col, 0), errors="coerce") or 0),
            "start": start_iso,
            "end": end_iso,
        })
    
    return {"company": str(company_name), "ads": items}

def call_model(payload: dict, media_type: str) -> str:
    """Call OpenAI model for key advantages analysis"""
    if media_type not in MEDIA_PROMPTS:
        raise ValueError(f"Unknown media type: {media_type}")
    
    prompt_config = MEDIA_PROMPTS[media_type]
    
    messages = [
        {"role": "system", "content": prompt_config["system"]},
        {"role": "user", "content": prompt_config["user"]},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
    ]
    
    resp = client.chat.completions.create(
        model=DEFAULT_MODEL, 
        temperature=TEMPERATURE, 
        messages=messages,
        response_format={"type": "json_object"}
    )
    return resp.choices[0].message.content

def run_key_advantages_analysis(df: pd.DataFrame, media_type: str) -> str:
    """
    Run key advantages analysis on dataframe
    Returns path to output Excel file
    """
    logger.info(f"Starting key advantages analysis for {media_type} with {len(df)} items...")
    
    # Validate media type
    if media_type not in MEDIA_TYPES:
        raise ValueError(f"Unknown media type: {media_type}")
    
    # Preprocess data
    df_processed = preprocess_data(df, media_type)
    media_config = MEDIA_TYPES[media_type]
    company_col = media_config["brand_column"]
    
    # Create output file
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_xlsx = f"key_advantages_{media_type}_{run_ts}.xlsx"
    
    # Process companies in parallel for better performance
    def process_company(company_group):
        company, group_df = company_group
        
        # Check minimum ads threshold
        if len(group_df) < MIN_ADS_FOR_ANALYSIS:
            logger.info(f"Skipping {company}: too few ads ({len(group_df)} < {MIN_ADS_FOR_ANALYSIS})")
            return company, [], []  # Return empty results for skipped companies
        
        try:
            payload = build_payload(group_df, media_type)
            raw_output = call_model(payload, media_type)
            
            try:
                data = json.loads(raw_output)
            except Exception as e:
                logger.error(f"JSON parsing error for {company}: {e}")
                data = {"company": company, "advantages": []}
            
            # Flatten to sheet
            rows = []
            for i, adv in enumerate(data.get("advantages", []), start=1):
                examples = adv.get("examples") or [{}]  # ensure at least one row per advantage
                for ex in examples:
                    rows.append({
                        "advantage_id": i,
                        "title": adv.get("title"),
                        "category": adv.get("category"),
                        "evidence_list": " | ".join(adv.get("evidence", []) or []),
                        "example_index": ex.get("ad_index") or ex.get("article_index") or ex.get("post_index"),
                        "example_quote": ex.get("quote"),
                    })
            
            return company, rows, data.get("advantages", [])
            
        except Exception as e:
            logger.error(f"Error processing {company}: {e}")
            return company, [], []
    
    # Process companies in parallel
    all_advantages = []
    company_results = {}
    skipped_companies = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:  # Use configurable max workers
        # Submit all tasks
        future_to_company = {
            executor.submit(process_company, (company, group_df)): company 
            for company, group_df in df_processed.groupby(company_col)
        }
        
        # Collect results with progress bar
        for future in tqdm(as_completed(future_to_company), 
                          total=len(future_to_company), 
                          desc="Processing companies"):
            company, rows, advantages = future.result()
            if rows:  # Only add companies with results
                company_results[company] = rows
                all_advantages.extend(advantages)
            else:  # Track skipped companies
                skipped_companies.append(company)
    
    # Write results to Excel
    with pd.ExcelWriter(out_xlsx, engine="xlsxwriter") as writer:
        for company, rows in company_results.items():
            if rows:
                pd.DataFrame(rows).to_excel(
                    writer, 
                    sheet_name=re.sub(r"[^A-Za-z0-9]", "_", company)[:31], 
                    index=False
                )
        
        # Add skipped companies sheet if any were skipped
        if skipped_companies:
            # Get the actual ad counts for skipped companies
            skipped_data = []
            for company in skipped_companies:
                company_data = df_processed[df_processed[company_col] == company]
                skipped_data.append({
                    "Company": company,
                    "Ad Count": len(company_data),
                    "Reason": f"Too few ads ({len(company_data)} < {MIN_ADS_FOR_ANALYSIS})"
                })
            skipped_df = pd.DataFrame(skipped_data)
            skipped_df.to_excel(writer, sheet_name="Skipped Companies", index=False)
        
        # Create summary sheet
        if all_advantages:
            summary_rows = []
            for i, adv in enumerate(all_advantages, start=1):
                summary_rows.append({
                    "advantage_id": i,
                    "title": adv.get("title"),
                    "category": adv.get("category"),
                    "evidence_list": " | ".join(adv.get("evidence", []) or []),
                    "example_count": len(adv.get("examples", []))
                })
            
            pd.DataFrame(summary_rows).to_excel(
                writer, 
                sheet_name="Summary", 
                index=False
            )
    
    logger.info(f"Key advantages analysis saved to: {out_xlsx}")
    return out_xlsx

def analyze_key_advantages_for_month(year: int, month: int, output_folder: str) -> str:
    """
    Run key advantages analysis for ads data for a specific month
    Returns path to output file
    """
    from utils.data_processor import load_new_data
    
    # Load and filter ads data for the month
    df = load_new_data("ads", year, month)
    if len(df) == 0:
        raise ValueError(f"No ads data found for {year}-{month:02d}")
    
    # Run analysis
    output_file = run_key_advantages_analysis(df, "ads")
    
    # Move to output folder (overwrite if exists)
    os.makedirs(output_folder, exist_ok=True)
    final_output = os.path.join(output_folder, f"key_advantages_ads.xlsx")
    
    # Remove existing file if it exists, then rename
    if os.path.exists(final_output):
        os.remove(final_output)
    os.rename(output_file, final_output)
    
    logger.info(f"Key advantages analysis saved to: {final_output}")
    return final_output
