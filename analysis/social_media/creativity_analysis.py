"""
Social Media Creativity Analysis - Uses same structure as ads
"""
import os
import re
import json
import traceback
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
from tqdm import tqdm
from tenacity import retry, wait_exponential, stop_after_attempt
from openai import OpenAI
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import OPENAI_API_KEY, DEFAULT_MODEL, MAX_WORKERS, MEDIA_TYPES, MIN_ADS_FOR_ANALYSIS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Configuration
TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 2000
MAX_ITEMS_PER_BRAND = 50
TOP_K_PER_BRAND = 10
MAX_CHARS_PER_ITEM = 1000
CROSS_BRAND_TEXT_CHARS = 300
DEDUP_ACROSS_BRANDS = False

# Media-specific prompts
MEDIA_PROMPTS = {
    "ads": {
        "system": "You are an advertising creativity analyst. Given a SET of ads for one brand, pick the top K ads that are most original RELATIVE to the rest of that set.",
        "task_template": "Task: From the following ads (one brand only), choose the {top_k} most ORIGINAL ads relative to others in this set.",
        "originality_def": "Originality definition: novel angle, unexpected framing, fresh creative device, or distinct voice vs typical ads AND vs peers in this set.",
        "rules": [
            "- Judge ONLY on originality/creativity, not performance or reach.",
            "- Avoid near-duplicates: if multiple ads are the same idea, pick at most one strongest instance.",
            "- Prefer diversity of creative ideas among the selected set.",
            "- Indices MUST refer to the provided list order."
        ],
        "items_name": "Ads"
    },
    "pr": {
        "system": "You are a PR creativity analyst. Given a SET of PR materials/messages for one company, pick the top K items that are most original RELATIVE to the rest of that set.",
        "task_template": "Task: From the following PR materials (one company only), choose the {top_k} most ORIGINAL items relative to others in this set.",
        "originality_def": "Originality definition: novel angle, unexpected framing, fresh narrative device, or distinct voice vs typical PR and vs peers in this set.",
        "rules": [
            "- Choose only themes that are related to the company, as there are articles that only mention the company as a side-note, and the main story is not related to the company at all. The companies can be Kauno grudai, Thermo Fisher, Ignitis, SBA or Acme.",
            "- Judge ONLY on originality/creativity of the PR content, not performance or impressions.",
            "- Avoid near-duplicates: if multiple items are the same idea, pick at most one strongest instance.",
            "- Prefer diversity of creative ideas among the selected set.",
            "- Indices MUST refer to the provided list order."
        ],
        "items_name": "Items"
    },
    "social_media": {
        "system": "You are a creativity analyst for LinkedIn communications. Given a SET of LinkedIn posts for one company, pick the top K posts that are most original RELATIVE to the rest of that set.",
        "task_template": "Task: From the following LinkedIn posts (one company only), choose the {top_k} most ORIGINAL posts relative to others in this set.",
        "originality_def": "Originality definition: novel angle, unexpected framing, fresh narrative device, or distinct voice vs typical LinkedIn posts and vs peers in this set.",
        "rules": [
            "- Choose only posts that are genuinely about the company; ignore posts where the company is only mentioned as a side-note and the main story is unrelated.",
            "- The companies can be Kauno grudai, Thermo Fisher, Ignitis, SBA, or Acme.",
            "- Judge ONLY on originality/creativity of the post content, not on engagement metrics such as impressions or likes.",
            "- Avoid near-duplicates: if multiple posts share the same idea, pick at most one strongest instance.",
            "- Prefer diversity of creative ideas among the selected set.",
            "- Indices MUST refer to the provided list order."
        ],
        "items_name": "Posts"
    }
}

def normalize_text(s: Any) -> str:
    """Normalize text for processing"""
    if not isinstance(s, str):
        return ""
    s = s.replace("\n", " ").replace("\r", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def truncate(s: str, limit: int) -> str:
    """Truncate text to limit"""
    if not s:
        return ""
    return s if len(s) <= limit else (s[:limit] + "…")

def sanitize_filename(name: str) -> str:
    """Sanitize filename"""
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", str(name))
    return name[:80] if len(name) > 80 else name

def py(obj: Any):
    """Convert object to JSON-serializable format"""
    if isinstance(obj, (int, float, str)) or obj is None:
        return obj
    if isinstance(obj, (list, tuple)):
        return [py(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): py(v) for k, v in obj.items()}
    try:
        if hasattr(obj, "item"):
            return obj.item()
    except Exception:
        pass
    return str(obj)

def chat_json(messages: List[Dict[str, str]], *, model: str = DEFAULT_MODEL,
              temperature: float = TEMPERATURE, max_tokens: int = MAX_OUTPUT_TOKENS) -> Dict[str, Any]:
    """Call OpenAI with JSON response format and improved error handling"""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
            max_tokens=max_tokens,
        )
    except TypeError:
        # Older SDK: no response_format arg
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    raw = (resp.choices[0].message.content or "").strip()
    
    # Try to parse JSON directly
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        # Try to fix common JSON issues
        try:
            # Fix unterminated strings by truncating at the error position
            if "Unterminated string" in str(e):
                # Find the position of the unterminated string and truncate there
                error_pos = e.pos if hasattr(e, 'pos') else len(raw)
                # Find the last complete object before the error
                truncated = raw[:error_pos]
                # Find the last complete JSON object
                last_brace = truncated.rfind('}')
                if last_brace != -1:
                    truncated = truncated[:last_brace + 1]
                    return json.loads(truncated)
            
            # Try to extract JSON from the response
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                json_str = raw[start:end + 1]
                return json.loads(json_str)
                
        except Exception:
            pass
        
        # If all else fails, return a fallback structure
        logger.warning(f"JSON parsing failed, using fallback. Error: {e}")
        return {"rankings": []}

def build_within_brand_prompt(top_k: int, media_type: str) -> str:
    """Build prompt for within-brand selection"""
    if media_type not in MEDIA_PROMPTS:
        raise ValueError(f"Unknown media type: {media_type}")
    
    prompt_config = MEDIA_PROMPTS[media_type]
    items_name = prompt_config["items_name"]
    
    lines = [
        prompt_config["task_template"].format(top_k=top_k),
        prompt_config["originality_def"],
        "Rules:"
    ]
    lines.extend(prompt_config["rules"])
    lines.extend([
        "",
        "Return STRICT JSON ONLY (no markdown) with these keys:",
        "- selected_topk: array of integers (indices of chosen items)",
        "- selected_details: array of objects, each with: idx (int), originality_reason (string). Optional: short_title (string), themes (array of strings)",
        "- notes_overall: optional string",
        "",
        f"{items_name} (JSON array) follows next."
    ])
    return "\n".join(lines)

@retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(5))
def select_topk_within_brand(item_list: List[Dict[str, Any]], top_k: int, brand: str, media_type: str) -> Dict[str, Any]:
    """Select top K items within a brand"""
    compact_items = [
        {"idx": int(i),
         "reach": (float(item.get("reach")) if item.get("reach") is not None else None),
         "text": item.get("text", "")}
        for i, item in enumerate(item_list)
    ]

    prompt = build_within_brand_prompt(top_k, media_type)
    items_name = MEDIA_PROMPTS[media_type]["items_name"]
    user_input = prompt + f"\n\n{items_name} (JSON array):\n" + json.dumps(compact_items, ensure_ascii=False)
    
    # Reduced logging for cleaner output

    messages = [
        {"role": "system", "content": MEDIA_PROMPTS[media_type]["system"]},
        {"role": "user", "content": user_input},
    ]
    data = chat_json(messages)

    # Normalize & validate
    selected = data.get("selected_topk", [])
    if not isinstance(selected, list):
        selected = []
    selected = [int(i) for i in selected if isinstance(i, (int, float, str)) and str(i).strip().lstrip("-").isdigit()]
    selected = list(dict.fromkeys(selected))[:top_k]  # unique, keep order, cap length

    details = data.get("selected_details", [])
    if not isinstance(details, list):
        details = []

    result = {
        "selected_topk": selected,
        "selected_details": details,
        "notes_overall": data.get("notes_overall", ""),
    }
    return result

@retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(5))
def rank_brands_cross_brand(payload: List[Dict[str, Any]], media_type: str) -> Dict[str, Any]:
    """Rank brands across all brands"""
    payload_py = py(payload)
    
    # Build cross-brand prompt based on media type
    if media_type == "ads":
        header = "You are given multiple brands, each with a set of their top selected ads (already filtered for within-brand originality).\n"
        context = "Rank brands by overall originality/creativity compared to each other, considering:\n"
    elif media_type == "pr":
        header = "You are given multiple companies, each with a set of their top selected PR materials (already filtered for within-company originality).\n"
        context = "Rank companies by overall originality/creativity compared to each other, considering:\n"
    else:  # social_media
        header = "You are given multiple companies, each with a set of their top selected LinkedIn posts (already filtered for within-company originality).\n"
        context = "Rank companies by overall originality/creativity compared to each other, considering:\n"
    
    user_input = (header + context +
        "- Depth of originality across the set\n"
        "- Diversity of creative ideas\n"
        "- Boldness/novelty vs typical category norms (based on text alone)\n"
        "For each brand in the rankings, also include 2–3 short example snippets that best illustrate the originality you describe.\n"
        "IMPORTANT: Keep example snippets SHORT (max 50 characters each) and ensure all strings are properly escaped.\n"
        "Return STRICT JSON ONLY (no markdown) with key 'rankings' = array of objects with fields:\n"
        "- brand (string)\n"
        "- rank (int)\n"
        "- originality_score (0-10, decimals allowed)\n"
        "- justification (string, write 2-3 sentences)\n"
        "- examples (array of strings; each max 100 characters, properly escaped)\n"
        f"Brands payload (JSON array) follows next.\n\n" + json.dumps(payload_py, ensure_ascii=False))
    
    # Reduced logging for cleaner output

    messages = [
        {"role": "system", "content": "You are comparing creativity across brands using their already-selected top items. Rank brands by originality of these top items relative to other brands."},
        {"role": "user", "content": user_input},
    ]
    data = chat_json(messages, max_tokens=4000)  # Increase tokens for cross-brand ranking
    return data

def run_creativity_analysis(df: pd.DataFrame, media_type: str, 
                          text_column: str, brand_column: str, reach_column: str) -> str:
    """
    Run creativity analysis on dataframe
    Returns path to output Excel file
    """
    logger.info(f"Starting creativity analysis for {media_type} with {len(df)} items...")
    
    # Validate media type
    if media_type not in MEDIA_TYPES:
        raise ValueError(f"Unknown media type: {media_type}")
    
    # Clean data
    df = df.copy()
    df[text_column] = df[text_column].map(lambda x: truncate(normalize_text(x), MAX_CHARS_PER_ITEM))
    df[reach_column] = pd.to_numeric(df[reach_column], errors="coerce")
    df = df.dropna(subset=[brand_column, reach_column]).reset_index(drop=True)

    # Dedup
    logger.info(f"Rows before dedup: {len(df)}")
    df["__text_norm__"] = df[text_column].map(lambda s: normalize_text(s).lower())
    df_sorted = df.sort_values(reach_column, ascending=False).reset_index(drop=True)
    
    if DEDUP_ACROSS_BRANDS:
        dedup_df = df_sorted.drop_duplicates(subset=["__text_norm__"], keep="first").reset_index(drop=True)
    else:
        dedup_df = (df_sorted
                    .drop_duplicates(subset=[brand_column, "__text_norm__"], keep="first")
                    .reset_index(drop=True))
    logger.info(f"Rows after dedup: {len(dedup_df)}")

    # Top N by reach per brand
    top_per_brand = (dedup_df
                     .sort_values(reach_column, ascending=False)
                     .groupby(brand_column, group_keys=False)
                     .head(MAX_ITEMS_PER_BRAND)
                     .reset_index(drop=True))

    logger.info(f"Brands: {top_per_brand[brand_column].nunique()}")
    for b, g in top_per_brand.groupby(brand_column):
        logger.info(f"  {b}: {len(g)} items considered")

    # Within-brand selection with true parallel processing
    selections: List[Dict[str, Any]] = []
    per_brand_topk_rows: List[Dict[str, Any]] = []
    skipped_brands = []

    def process_brand(brand_group):
        brand, g = brand_group
        
        # Check minimum ads threshold
        if len(g) < MIN_ADS_FOR_ANALYSIS:
            return {"brand": brand, "skipped": True, "reason": f"too few ads ({len(g)} < {MIN_ADS_FOR_ANALYSIS})"}
        
        g_reset = g.reset_index(drop=True)
        dyn_top_k = min(TOP_K_PER_BRAND, len(g_reset))
        items_for_model = [
            {"text": g_reset.loc[i, text_column] or "",
             "reach": float(g_reset.loc[i, reach_column]) if pd.notnull(g_reset.loc[i, reach_column]) else None}
            for i in range(len(g_reset))
        ]
        
        try:
            sel = select_topk_within_brand(items_for_model, dyn_top_k, str(brand), media_type)
            
            # Map indices back to rows
            brand_rows = []
            for idx in sel.get("selected_topk", []):
                if 0 <= int(idx) < len(g_reset):
                    row = g_reset.iloc[int(idx)]
                    brand_rows.append({
                        brand_column: str(brand),
                        reach_column: float(row[reach_column]) if pd.notnull(row[reach_column]) else None,
                        text_column: row[text_column]
                    })
            
            return {"brand": brand, "selection": sel, "rows": brand_rows, "skipped": False}
            
        except Exception as e:
            logger.error(f"Within-brand selection failed for '{brand}': {type(e).__name__}: {e}")
            return {"brand": brand, "skipped": True, "reason": f"error: {e}"}

    # Process all brands in parallel
    brand_groups = list(top_per_brand.groupby(brand_column))
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all brand processing tasks
        future_to_brand = {
            executor.submit(process_brand, (brand, g)): brand 
            for brand, g in brand_groups
        }
        
        # Collect results with progress bar
        for future in tqdm(as_completed(future_to_brand), 
                          total=len(future_to_brand), 
                          desc="Processing brands"):
            result = future.result()
            
            if result["skipped"]:
                skipped_brands.append(f"{result['brand']} ({result['reason']})")
            else:
                selections.append({"brand": result["brand"], **result["selection"]})
                per_brand_topk_rows.extend(result["rows"])

    topk_df = pd.DataFrame(per_brand_topk_rows)
    if topk_df.empty:
        raise RuntimeError("Top-k selection produced no rows; check inputs or raise MAX_CHARS_PER_ITEM.")

    # Cross-brand payload
    cross_brand_payload: List[Dict[str, Any]] = []
    for item in selections:
        brand = item.get("brand", "(unknown)")
        details = item.get("selected_details", [])
        if details and isinstance(details, list):
            desc = [{
                "text": truncate(str(d.get("short_title") or "") + " -- " + str(d.get("originality_reason") or ""), CROSS_BRAND_TEXT_CHARS),
                "themes": d.get("themes", []) if isinstance(d.get("themes", []), list) else []
            } for d in details]
        else:
            subset = topk_df[topk_df[brand_column] == brand][text_column].tolist()
            desc = [{"text": truncate(s, CROSS_BRAND_TEXT_CHARS), "themes": []} for s in subset]
        cross_brand_payload.append({"brand": brand, "selected_ads": desc})

    # Cross-brand ranking
    try:
        cross_brand = rank_brands_cross_brand(cross_brand_payload, media_type)
        rankings = cross_brand.get("rankings", [])
        
        # Validate rankings structure
        if not rankings or not isinstance(rankings, list):
            raise ValueError("Invalid rankings structure received")
            
        # Ensure all required fields are present
        for ranking in rankings:
            if not all(key in ranking for key in ["brand", "rank", "originality_score", "justification"]):
                raise ValueError("Missing required fields in ranking")
                
    except Exception as e:
        logger.error(f"Cross-brand ranking failed: {type(e).__name__}: {e}")
        # Fallback: neutral scores, alphabetical by brand
        rankings = [
            {
                "brand": b, 
                "rank": i + 1, 
                "originality_score": 5.0, 
                "justification": f"Fallback due to ranking error: {str(e)[:100]}",
                "examples": []
            }
            for i, b in enumerate(sorted(topk_df[brand_column].unique()))
        ]

    ranking_df = pd.DataFrame(rankings).sort_values("rank").reset_index(drop=True)

    # Ensure 'examples' column exists
    if "examples" not in ranking_df.columns:
        ranking_df["examples"] = [[] for _ in range(len(ranking_df))]

    # Convert lists of examples into bullet-separated strings for Excel
    ranking_df["examples"] = ranking_df["examples"].apply(
        lambda ex: " • ".join(ex) if isinstance(ex, list) else str(ex)
    )

    # Export Excel
    run_ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_xlsx = f"creativity_ranking_{media_type}_{run_ts}.xlsx"
    
    # Remove timezone info from datetime columns before saving
    def remove_timezone(df):
        df_copy = df.copy()
        for col in df_copy.columns:
            if df_copy[col].dtype == 'datetime64[ns, UTC]':
                df_copy[col] = df_copy[col].dt.tz_localize(None)
        return df_copy
    
    with pd.ExcelWriter(out_xlsx, engine="xlsxwriter") as writer:
        remove_timezone(ranking_df).to_excel(writer, sheet_name="Overall Ranking", index=False)
        for brand, g in topk_df.groupby(brand_column):
            sheet = (str(brand)[:31]) if str(brand).strip() else "(blank)"
            remove_timezone(g.sort_values(reach_column, ascending=False)[[brand_column, reach_column, text_column]]).to_excel(writer, sheet_name=sheet, index=False)
        
        # Add skipped brands sheet if any were skipped
        if skipped_brands:
            skipped_df = pd.DataFrame({
                "Brand": [brand.split(" (")[0] for brand in skipped_brands],
                "Reason": [f"Too few ads ({brand.split('(')[1].rstrip(')')} < {MIN_ADS_FOR_ANALYSIS})" for brand in skipped_brands]
            })
            remove_timezone(skipped_df).to_excel(writer, sheet_name="Skipped Brands", index=False)
        
        # Debug sheets
        remove_timezone(pd.DataFrame(selections)).to_excel(writer, sheet_name="Selections JSON", index=False)
        remove_timezone(top_per_brand).to_excel(writer, sheet_name="TopN Considered", index=False)

    logger.info(f"Creativity analysis saved to: {out_xlsx}")
    return out_xlsx

def analyze_creativity_for_month(year: int, month: int, output_folder: str) -> str:
    """
    Run creativity analysis for social media data for a specific month
    Returns path to output file
    """
    from utils.data_processor import load_new_data
    
    # Load and filter social media data for the month
    df = load_new_data("social_media", year, month)
    if len(df) == 0:
        raise ValueError(f"No social media data found for {year}-{month:02d}")
    
    # Get column names from config
    media_config = MEDIA_TYPES["social_media"]
    text_column = media_config["text_column"]
    brand_column = media_config["brand_column"]
    reach_column = media_config["reach_column"]
    
    # Run analysis
    output_file = run_creativity_analysis(df, "social_media", text_column, brand_column, reach_column)
    
    # Move to output folder (overwrite if exists)
    os.makedirs(output_folder, exist_ok=True)
    final_output = os.path.join(output_folder, f"creativity_analysis_social_media.xlsx")
    
    # Remove existing file if it exists, then rename
    if os.path.exists(final_output):
        os.remove(final_output)
    os.rename(output_file, final_output)
    
    logger.info(f"Creativity analysis saved to: {final_output}")
    return final_output
