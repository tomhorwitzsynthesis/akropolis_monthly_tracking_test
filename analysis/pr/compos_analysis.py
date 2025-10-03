"""
PR CompOS Analysis - Archetype assignment for PR content
Based on the social media compos analysis structure
"""

import os
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from config import OPENAI_API_KEY, MEDIA_TYPES, MAX_WORKERS, MIN_ADS_FOR_ANALYSIS
from utils.data_processor import load_new_data

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Archetype Prompt for PR
ARCHETYPE_PROMPT = """As a senior Public Relations and Branding Communication expert you are interested in how companies are positioned by their PR materials.
Your task will be to analyze PR materials and assign the best-fitting archetype to each article, based on the following framework:

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

Top Archetype: [Top Archetype]"""

def assign_archetype_to_content(content: str, company_name: str) -> str:
    """Assign archetype to a single PR content item"""
    try:
        if not content or not content.strip():
            return "No Content"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": ARCHETYPE_PROMPT},
                {"role": "user", "content": content}
            ],
            temperature=0
        )
        
        output = response.choices[0].message.content
        top_archetype = None
        
        for line in output.splitlines():
            if "Top Archetype" in line:
                _, value = line.split(":", 1)
                top_archetype = value.strip()
                break
        
        return top_archetype or "Parsing Error"
        
    except Exception as e:
        logger.error(f"Error assigning archetype for {company_name}: {e}")
        return "Error"

def analyze_company_archetypes(company_data):
    """Analyze archetypes for a single company"""
    company_name, contents = company_data
    
    logger.info(f"Analyzing archetypes for {company_name} ({len(contents)} PR materials)")
    
    # Check minimum content threshold
    if len(contents) < MIN_ADS_FOR_ANALYSIS:
        logger.warning(f"Company {company_name} has only {len(contents)} PR materials (minimum required: {MIN_ADS_FOR_ANALYSIS}). Skipping.")
        return {
            "company": company_name,
            "archetype_count": len(contents),
            "error": f"Too few PR materials ({len(contents)} < {MIN_ADS_FOR_ANALYSIS})"
        }
    
    # Assign archetypes to each content item
    archetype_assignments = []
    for i, content in enumerate(contents):
        archetype = assign_archetype_to_content(content, company_name)
        archetype_assignments.append({
            "content_index": i,
            "content": content[:200] + "..." if len(content) > 200 else content,  # Truncate for summary
            "archetype": archetype
        })
    
    # Count archetype distribution
    archetype_counts = {}
    for assignment in archetype_assignments:
        archetype = assignment["archetype"]
        archetype_counts[archetype] = archetype_counts.get(archetype, 0) + 1
    
    # Find top archetype
    top_archetype = max(archetype_counts.items(), key=lambda x: x[1])[0] if archetype_counts else "Unknown"
    
    company_results = {
        "company": company_name,
        "total_materials": len(contents),
        "top_archetype": top_archetype,
        "archetype_distribution": archetype_counts,
        "archetype_assignments": archetype_assignments
    }
    
    return company_results

def create_archetype_summary(company_results):
    """Create summary of archetype analysis"""
    if not company_results:
        return pd.DataFrame()
    
    # Filter out error cases
    valid_results = [result for result in company_results if "error" not in result]
    if not valid_results:
        return pd.DataFrame()
    
    # Create summary data
    summary_data = []
    for result in valid_results:
        summary_row = {
            "Company": result["company"],
            "Total Materials": result["total_materials"],
            "Top Archetype": result["top_archetype"]
        }
        
        # Add archetype distribution
        for archetype, count in result["archetype_distribution"].items():
            summary_row[f"{archetype} Count"] = count
            summary_row[f"{archetype} %"] = round((count / result["total_materials"]) * 100, 1)
        
        summary_data.append(summary_row)
    
    return pd.DataFrame(summary_data)

def analyze_compos_for_month(year: int, month: int, output_folder: str) -> str:
    """
    Analyze CompOS (archetypes) for PR data for a specific month
    
    Args:
        year: Analysis year
        month: Analysis month
        output_folder: Output folder path
        
    Returns:
        Path to the saved Excel file
    """
    logger.info(f"Starting PR CompOS analysis for {year}-{month:02d}")
    
    # Load data
    df = load_new_data("pr", year, month)
    if df is None or df.empty:
        logger.error("No PR data loaded for CompOS analysis")
        return None
    
    logger.info(f"Loaded {len(df)} PR items for CompOS analysis")
    
    # Get column names
    brand_column = MEDIA_TYPES["pr"]["brand_column"]
    text_column = MEDIA_TYPES["pr"]["text_column"]
    
    # Group by company
    if brand_column not in df.columns:
        logger.error(f"Brand column '{brand_column}' not found in PR data")
        return None
    
    company_groups = df.groupby(brand_column)[text_column].apply(list).to_dict()
    
    logger.info(f"Found {len(company_groups)} companies for PR CompOS analysis")
    
    # Prepare data for parallel processing
    company_data = [(company, contents) for company, contents in company_groups.items()]
    
    company_results = []
    
    # Process companies in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_company = {
            executor.submit(analyze_company_archetypes, data): data[0] 
            for data in company_data
        }
        
        for future in as_completed(future_to_company):
            company_name = future_to_company[future]
            try:
                result = future.result()
                company_results.append(result)
                logger.info(f"Completed archetype analysis for {company_name}")
            except Exception as e:
                logger.error(f"Error processing {company_name}: {e}")
    
    # Create summary
    summary_df = create_archetype_summary(company_results)
    
    # Save to Excel
    excel_file = os.path.join(output_folder, "compos_analysis_pr.xlsx")
    logger.info(f"Saving PR CompOS analysis to: {excel_file}")
    
    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            # Summary sheet
            if not summary_df.empty:
                summary_df.to_excel(writer, sheet_name="Summary", index=False)
            
            # Individual company results
            used_sheet_names = set()
            for result in company_results:
                if "error" not in result:
                    company_name = result["company"]
                    sheet_name = company_name[:31]  # Excel sheet name limit
                    
                    # Handle duplicate sheet names (case-insensitive)
                    original_sheet_name = sheet_name
                    counter = 1
                    while sheet_name.lower() in [name.lower() for name in used_sheet_names]:
                        sheet_name = f"{original_sheet_name[:28]}_{counter}"  # Keep under 31 chars
                        counter += 1
                    used_sheet_names.add(sheet_name)
                    
                    # Create detailed results for this company
                    detailed_data = []
                    for assignment in result["archetype_assignments"]:
                        detailed_data.append({
                            "Content Index": assignment["content_index"],
                            "Content Preview": assignment["content"],
                            "Assigned Archetype": assignment["archetype"]
                        })
                    
                    if detailed_data:
                        detailed_df = pd.DataFrame(detailed_data)
                        detailed_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Skipped companies
            skipped_companies = [result for result in company_results if "error" in result]
            if skipped_companies:
                skipped_df = pd.DataFrame([{
                    "Company": result["company"],
                    "Material Count": result["archetype_count"],
                    "Reason": result["error"]
                } for result in skipped_companies])
                skipped_df.to_excel(writer, sheet_name="Skipped Companies", index=False)
        
        logger.info(f"PR CompOS analysis saved: {excel_file}")
        return excel_file
        
    except Exception as e:
        logger.error(f"Error saving PR CompOS analysis: {e}")
        return None
