"""
Audience Affinity Analysis for Social Media
Based on the monthly_update/audience_affinity.py code
"""

import os
import pickle
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from config import OPENAI_API_KEY, MEDIA_TYPES, MAX_WORKERS, MIN_POSTS_FOR_ANALYSIS
from utils.data_processor import load_new_data

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# OLD Persona Prompts (LinkedIn-focused) - COMMENTED OUT
# PERSONA_PROMPTS = {
#     "Customers & End Users": {
#         "prompt": """You will be provided with LinkedIn post content. You should look at the given content from the perspective of the Customers & End Users (Clients, Partners, Prospective Buyers).
# 
# Evaluate each of the following three points from 1 to 7, where 1 = poorly represented and 7 = strongly represented:
# 
# 1. Problem-Solving Value: Does the content help them understand solutions to their key challenges?
# 2. Clarity of Offerings: Does it clearly communicate the company's value proposition and differentiators?
# 3. Innovation & Market Leadership: Does the content showcase new product developments, industry advancements, or thought leadership?
# 
# Respond ONLY in the following format:
# Problem-Solving Value: [score]
# Clarity of Offerings: [score]
# Innovation & Market Leadership: [score]""",
#         "columns": [
#             "Customer_Problem_Solving",
#             "Customer_Clarity_Offerings",
#             "Customer_Innovation"
#         ]
#     },
# 
#     "Job Seekers & Talent": {
#         "prompt": """You will be provided with LinkedIn post content. You should look at the given content from the perspective of Job Seekers and Talent.
# 
# Evaluate each of the following three points from 1 to 7:
# 
# 1. Authenticity of Employer Branding
# 2. Career Growth Insights
# 3. Market Impact
# 
# Respond ONLY in the following format:
# Authenticity of Employer Branding: [score]
# Career Growth Insights: [score]
# Market Impact: [score]""",
#         "columns": [
#             "Talent_Employer_Branding",
#             "Talent_Career_Growth",
#             "Talent_Market_Impact"
#         ]
#     },
# 
#     "Professionals": {
#         "prompt": """You will be provided with LinkedIn post content. You should look at the given content from the perspective of Industry Professionals.
# 
# Evaluate each of the following three points from 1 to 7:
# 
# 1. Expertise & Thought Leadership
# 2. Industry Relevance
# 3. Innovation & Trends
# 
# Respond ONLY in the following format:
# Expertise & Thought Leadership: [score]
# Industry Relevance: [score]
# Innovation & Trends: [score]""",
#         "columns": [
#             "Pro_Expertise",
#             "Pro_Industry_Relevance",
#             "Pro_Innovation"
#         ]
#     },
# 
#     "Decision Makers & Investors": {
#         "prompt": """You will be provided with LinkedIn post content. You should look at the given content from the perspective of Decision Makers and Investors.
# 
# Evaluate each of the following three points from 1 to 7:
# 
# 1. Long-term Strategic Value
# 2. Market Positioning
# 3. Market Influence & Growth
# 
# Respond ONLY in the following format:
# Long-term Strategic Value: [score]
# Market Positioning: [score]
# Market Influence & Growth: [score]""",
#         "columns": [
#             "Investor_Long_Term",
#             "Investor_Positioning",
#             "Investor_Market_Influence"
#         ]
#     }
# }

# Persona Prompts
PERSONA_PROMPTS = {
    "Families & Household Shoppers": {
        "prompt": """You will be provided with Facebook post content. You should look at the given content from the perspective of Families & Household Shoppers (parents, caregivers, people shopping for a household).

Evaluate each of the following three points from 1 to 7, where 1 = poorly represented and 7 = strongly represented.
A 1 would mean that the post is not relevant to the audience, a 7 would mean that the post is strongly relevant to the audience.

1. Kids’ Products Relevance: Does it feature toys, clothing, food, or other products specifically for children?
2. Kids’ Events & Activities: Does it promote events, workshops, or entertainment designed for children or families?
3. Household Savings & Discounts: Does it clearly highlight discounts, bundle deals, or cost-saving opportunities aimed at household shopping?

Respond ONLY in the following format:
Kids’ Products Relevance: [score]
Kids’ Events & Activities: [score]
Household Savings & Discounts: [score]""",
        "columns": [
            "Family_Kids_Products",
            "Family_Kids_Events",
            "Family_Household_Discounts"
        ]
    },

    "Young Adults – Tech & Fashion": {
        "prompt": """You will be provided with Facebook post content. You should look at the given content from the perspective of Young Adults – Tech & Fashion (students, young professionals, and early-career adults).

Evaluate each of the following three points from 1 to 7, where 1 = poorly represented and 7 = strongly represented.
A 1 would mean that the post is not relevant to the audience, a 7 would mean that the post is strongly relevant to the audience.

1. Technology & Gaming Relevance: Does it feature electronics, gaming, or other digital lifestyle products?
2. Fashion & Style for Young Adults: Does it highlight clothing, footwear, or accessories appealing to a youthful and trend-aware audience?
3. Social & Youth-Oriented Events: Does it promote live music, product launches, or gatherings tailored to young adults?

Respond ONLY in the following format:
Technology & Gaming Relevance: [score]
Fashion & Style for Young Adults: [score]
Social & Youth-Oriented Events: [score]""",
        "columns": [
            "Young_Tech_Gaming",
            "Young_Fashion_Style",
            "Young_Social_Events"
        ]
    },

    "Store Owners & Business Partners": {
        "prompt": """You will be provided with Facebook post content. You should look at the given content from the perspective of Store Owners & Business Partners (current or potential tenants, brand partners).

Evaluate each of the following three points from 1 to 7, where 1 = poorly represented and 7 = strongly represented.
A 1 would mean that the post is not relevant to the audience, a 7 would mean that the post is strongly relevant to the audience.

1. Business Growth Opportunities: Does it communicate how the mall drives traffic, supports marketing campaigns, or expands customer reach?
2. Partnership & Co-Marketing Potential: Does it highlight collaborative promotions, cross-store events, or shared advertising initiatives?
3. Market Insights & Strategic Positioning: Does it offer useful information on customer trends, competitive positioning, or investment value?

Respond ONLY in the following format:
Business Growth Opportunities: [score]
Partnership & Co-Marketing Potential: [score]
Market Insights & Strategic Positioning: [score]""",
        "columns": [
            "Store_Business_Growth",
            "Store_Partnership_CoMarketing",
            "Store_Market_Insights"
        ]
    },

    "Shopping Experience & Mall Environment": {
        "prompt": """You will be provided with Facebook post content. You should look at the given content from the perspective of Shopping Experience & Mall Environment (visitors focused on comfort, accessibility, and the overall atmosphere of the mall).

Evaluate each of the following three points from 1 to 7, where 1 = poorly represented and 7 = strongly represented.
A 1 would mean that the post is not relevant to the audience, a 7 would mean that the post is strongly relevant to the audience.

1. Accessibility & Comfort: Does it emphasize parking, navigation, seating, or family-friendly services like elevators and rest areas?
2. Ambience & Design Quality: Does it convey a pleasant, clean, or distinctive shopping atmosphere?
3. Mall-Wide Events & Services: Does it highlight seasonal festivals, center-wide promotions, or customer-service improvements that enhance the overall trip?

Respond ONLY in the following format:
Accessibility & Comfort: [score]
Ambience & Design Quality: [score]
Mall-Wide Events & Services: [score]""",
        "columns": [
            "Experience_Accessibility_Comfort",
            "Experience_Ambience_Design",
            "Experience_Mallwide_Events"
        ]
    }
}


def parse_affinity_response(response_text, persona_name):
    """Parse the GPT response for audience affinity scores"""
    scores = {}
    columns = PERSONA_PROMPTS[persona_name]["columns"]
    
    # Define column name mappings for better matching
    column_mappings = {
        "Family_Kids_Products": ["Kids' Products Relevance", "Kids Products", "Products Relevance"],
        "Family_Kids_Events": ["Kids' Events & Activities", "Kids Events", "Events Activities"],
        "Family_Household_Discounts": ["Household Savings & Discounts", "Household Discounts", "Savings Discounts"],
        "Young_Tech_Gaming": ["Technology & Gaming Relevance", "Technology Gaming", "Gaming Relevance"],
        "Young_Fashion_Style": ["Fashion & Style for Young Adults", "Fashion Style", "Style Young Adults"],
        "Young_Social_Events": ["Social & Youth-Oriented Events", "Social Events", "Youth Events"],
        "Store_Business_Growth": ["Business Growth Opportunities", "Business Growth", "Growth Opportunities"],
        "Store_Partnership_CoMarketing": ["Partnership & Co-Marketing Potential", "Partnership Marketing", "Co-Marketing"],
        "Store_Market_Insights": ["Market Insights & Strategic Positioning", "Market Insights", "Strategic Positioning"],
        "Experience_Accessibility_Comfort": ["Accessibility & Comfort", "Accessibility Comfort", "Comfort"],
        "Experience_Ambience_Design": ["Ambience & Design Quality", "Ambience Design", "Design Quality"],
        "Experience_Mallwide_Events": ["Mall-Wide Events & Services", "Mallwide Events", "Events Services"]
    }
    
    for line in response_text.splitlines():
        line = line.strip()
        for col in columns:
            # Check if this line contains a score for this column
            if col in column_mappings:
                for mapping in column_mappings[col]:
                    if mapping.lower() in line.lower():
                        try:
                            # Extract score from line
                            score = None
                            for word in line.split():
                                if word.isdigit() and 1 <= int(word) <= 7:
                                    score = int(word)
                                    break
                            if score:
                                scores[col] = score
                                break  # Found the score, move to next column
                        except:
                            continue
    
    # Fill missing scores with neutral value (4)
    for col in columns:
        if col not in scores:
            scores[col] = 4
    
    return scores

def analyze_individual_post(post_content, persona_name, persona_config):
    """Analyze a single post for audience affinity"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": persona_config["prompt"]},
                {"role": "user", "content": post_content}
            ],
            temperature=0
        )
        
        gpt_response = response.choices[0].message.content
        scores = parse_affinity_response(gpt_response, persona_name)
        
        # Debug logging for first few posts
        if hasattr(analyze_individual_post, 'debug_count'):
            analyze_individual_post.debug_count += 1
        else:
            analyze_individual_post.debug_count = 1
            
        if analyze_individual_post.debug_count <= 3:
            logger.info(f"DEBUG - Persona: {persona_name}")
            logger.info(f"DEBUG - Post content (first 100 chars): {post_content[:100]}...")
            logger.info(f"DEBUG - GPT Response: {gpt_response}")
            logger.info(f"DEBUG - Parsed scores: {scores}")
        
        return scores
        
    except Exception as e:
        logger.error(f"Error analyzing post for {persona_name}: {e}")
        # Fill with neutral scores on error
        return {col: 4 for col in persona_config["columns"]}

def analyze_company_affinity(company_data):
    """Analyze audience affinity for a single company"""
    company_name, posts = company_data
    
    logger.info(f"Analyzing affinity for {company_name} ({len(posts)} posts)")
    
    # Check minimum posts threshold
    if len(posts) < MIN_POSTS_FOR_ANALYSIS:
        logger.warning(f"Company {company_name} has only {len(posts)} posts (minimum required: {MIN_POSTS_FOR_ANALYSIS}). Skipping.")
        return {
            "company": company_name,
            "post_count": len(posts),
            "error": f"Too few posts in this period ({len(posts)} < {MIN_POSTS_FOR_ANALYSIS})"
        }
    
    company_results = {
        "company": company_name,
        "post_count": len(posts),
        "individual_posts": []
    }
    
    # Analyze each persona by scoring individual posts
    for persona_name, persona_config in PERSONA_PROMPTS.items():
        all_post_scores = []
        
        # Score each individual post
        for i, post in enumerate(posts):
            post_scores = analyze_individual_post(post, persona_name, persona_config)
            all_post_scores.append(post_scores)
            
            # Store individual post details
            if i < len(company_results["individual_posts"]):
                company_results["individual_posts"][i]["post_content"] = post
                company_results["individual_posts"][i][f"{persona_name}_scores"] = post_scores
            else:
                company_results["individual_posts"].append({
                    "post_content": post,
                    f"{persona_name}_scores": post_scores
                })
        
        # Calculate top 2 box percentages for this persona
        persona_columns = persona_config["columns"]
        for col in persona_columns:
            # Get all scores for this column across all posts
            scores = [post_scores.get(col, 4) for post_scores in all_post_scores]
            
            # Calculate top 2 box percentage (scores 6-7)
            top_2_box_count = sum(1 for score in scores if score >= 6)
            top_2_box_pct = (top_2_box_count / len(scores)) * 100 if scores else 0
            
            # Store as the main column name (what dashboard expects)
            company_results[col] = round(top_2_box_pct, 1)
    
    return company_results

def create_summary_dataframe(company_results):
    """Create summary DataFrame with percentage calculations"""
    if not company_results:
        return pd.DataFrame()
    
    # Filter out error cases for summary calculation
    valid_results = [result for result in company_results if "error" not in result]
    if not valid_results:
        return pd.DataFrame()
    
    df = pd.DataFrame(valid_results)
    
    # Calculate percentage of high scores (6-7) for each persona
    persona_columns = {
        "Families & Household Shoppers": ["Family_Kids_Products", "Family_Kids_Events", "Family_Household_Discounts"],
        "Young Adults – Tech & Fashion": ["Young_Tech_Gaming", "Young_Fashion_Style", "Young_Social_Events"],
        "Store Owners & Business Partners": ["Store_Business_Growth", "Store_Partnership_CoMarketing", "Store_Market_Insights"],
        "Shopping Experience & Mall Environment": ["Experience_Accessibility_Comfort", "Experience_Ambience_Design", "Experience_Mallwide_Events"]
    }
    
    summary_data = []
    
    for _, row in df.iterrows():
        summary_row = {"Brand": row["company"]}
        
        for persona, cols in persona_columns.items():
            # Calculate overall percentage for this persona using individual dimension percentages
            dimension_percentages = [row[col] for col in cols if col in row]
            if dimension_percentages:
                overall_percentage = sum(dimension_percentages) / len(dimension_percentages)
                summary_row[f"{persona}_%High"] = round(overall_percentage, 1)
            else:
                summary_row[f"{persona}_%High"] = 0.0
        
        # Add individual dimension percentages (what dashboard expects)
        for col in df.columns:
            if col not in ["company", "post_count"] and not col.endswith("_%High"):
                summary_row[col] = row[col]
        
        summary_data.append(summary_row)
    
    return pd.DataFrame(summary_data)

def generate_gpt_summary(company_results):
    """Generate a GPT summary of the audience affinity results"""
    try:
        # Prepare comprehensive data for GPT analysis
        summary_text = "Audience Affinity Analysis Results:\n\n"
        
        # Filter out error cases
        valid_results = [result for result in company_results if "error" not in result]
        
        for result in valid_results:
            company_name = result["company"]
            post_count = result["post_count"]
            summary_text += f"Brand: {company_name} ({post_count} posts)\n"
            
            # Add individual dimension percentages
            summary_text += "  Top 2 Box Percentages (scores 6-7):\n"
            
            # Define persona columns for better organization
            persona_columns = {
                "Families & Household Shoppers": ["Family_Kids_Products", "Family_Kids_Events", "Family_Household_Discounts"],
                "Young Adults – Tech & Fashion": ["Young_Tech_Gaming", "Young_Fashion_Style", "Young_Social_Events"],
                "Store Owners & Business Partners": ["Store_Business_Growth", "Store_Partnership_CoMarketing", "Store_Market_Insights"],
                "Shopping Experience & Mall Environment": ["Experience_Accessibility_Comfort", "Experience_Ambience_Design", "Experience_Mallwide_Events"]
            }
            
            for persona, cols in persona_columns.items():
                summary_text += f"    {persona}:\n"
                for col in cols:
                    if col in result:
                        summary_text += f"      {col}: {result[col]}%\n"
            
            # Add sample of individual post scores for context
            if "individual_posts" in result and result["individual_posts"]:
                summary_text += "  Sample Post Scores (first 3 posts):\n"
                for i, post_data in enumerate(result["individual_posts"][:3]):
                    summary_text += f"    Post {i+1}: {post_data['post_content'][:100]}...\n"
                    for persona_name in persona_columns.keys():
                        persona_scores = post_data.get(f"{persona_name}_scores", {})
                        if persona_scores:
                            summary_text += f"      {persona_name}: {persona_scores}\n"
            
            summary_text += "\n"
        
        # Add skipped companies info
        skipped_results = [result for result in company_results if "error" in result]
        if skipped_results:
            summary_text += "Skipped Companies:\n"
            for result in skipped_results:
                summary_text += f"  {result['company']}: {result['error']}\n"
            summary_text += "\n"
        
        prompt = """Analyze the following audience affinity data and provide insights on:
1. Which brands are performing best across different audience segments (based on top 2 box percentages)
2. Key patterns and trends in audience engagement
3. Specific recommendations for improvement based on the data

The data shows the percentage of posts that scored 6-7 (high relevance) for each audience dimension. Focus on actionable insights based on the actual numbers provided.

Keep the summary concise and actionable."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": summary_text}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating GPT summary: {e}")
        return "Error generating summary"

def analyze_audience_affinity_for_month(year: int, month: int, output_folder: str) -> str:
    """
    Analyze audience affinity for social media data for a specific month
    
    Args:
        year: Analysis year
        month: Analysis month
        output_folder: Output folder path
        
    Returns:
        Path to the saved pickle file
    """
    logger.info(f"Starting audience affinity analysis for social_media {year}-{month:02d}")
    
    # Load data
    df = load_new_data("social_media", year, month)
    if df is None or df.empty:
        logger.error("No data loaded for audience affinity analysis")
        return None
    
    logger.info(f"Loaded {len(df)} social media items for audience affinity analysis")
    
    # Get column names
    brand_column = MEDIA_TYPES["social_media"]["brand_column"]
    text_column = MEDIA_TYPES["social_media"]["text_column"]
    
    # Group by company
    if brand_column not in df.columns:
        logger.error(f"Brand column '{brand_column}' not found in data")
        return None
    
    company_groups = df.groupby(brand_column)[text_column].apply(list).to_dict()
    
    logger.info(f"Found {len(company_groups)} companies for analysis")
    
    # Prepare data for parallel processing
    company_data = [(company, posts) for company, posts in company_groups.items()]
    
    company_results = []
    
    # Process companies in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_company = {
            executor.submit(analyze_company_affinity, data): data[0] 
            for data in company_data
        }
        
        for future in as_completed(future_to_company):
            company_name = future_to_company[future]
            try:
                result = future.result()
                company_results.append(result)
                logger.info(f"Completed analysis for {company_name}")
            except Exception as e:
                logger.error(f"Error processing {company_name}: {e}")
    
    # Create summary DataFrame
    summary_df = create_summary_dataframe(company_results)
    
    # Generate GPT summary
    gpt_summary = generate_gpt_summary(company_results)
    
    # Prepare final output
    output_data = {
        "company_results": company_results,
        "summary_df": summary_df,
        "gpt_summary": gpt_summary
    }
    
    # Save to pickle
    pickle_file = os.path.join(output_folder, "audience_affinity_outputs.pkl")
    logger.info(f"Saving output to {pickle_file}...")
    
    try:
        with open(pickle_file, "wb") as f:
            pickle.dump(output_data, f)
        logger.info("audience_affinity_outputs.pkl successfully created.")
    except Exception as e:
        logger.error(f"Error saving pickle file: {e}")
        return None
    
    # Save to Excel
    excel_file = os.path.join(output_folder, "audience_affinity_analysis_social_media.xlsx")
    logger.info(f"Saving output to Excel file: {excel_file}")
    
    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            # Summary sheet
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            
            # Individual company results
            if company_results:
                # Create company results without individual_posts for the main sheet
                company_results_clean = []
                for result in company_results:
                    if "error" not in result:
                        clean_result = {k: v for k, v in result.items() if k != "individual_posts"}
                        company_results_clean.append(clean_result)
                
                if company_results_clean:
                    company_df = pd.DataFrame(company_results_clean)
                    company_df.to_excel(writer, sheet_name="Company Results", index=False)
            
            # Individual post details sheet
            individual_posts_data = []
            for result in company_results:
                if "error" not in result and "individual_posts" in result:
                    company_name = result["company"]
                    for post_data in result["individual_posts"]:
                        post_row = {"Company": company_name, "Post Content": post_data["post_content"]}
                        
                        # Add scores for each persona
                        for persona_name in PERSONA_PROMPTS.keys():
                            persona_scores = post_data.get(f"{persona_name}_scores", {})
                            for col, score in persona_scores.items():
                                post_row[col] = score
                        
                        individual_posts_data.append(post_row)
            
            if individual_posts_data:
                individual_posts_df = pd.DataFrame(individual_posts_data)
                individual_posts_df.to_excel(writer, sheet_name="Individual Posts", index=False)
            
            # Skipped companies sheet
            skipped_companies = [result for result in company_results if "error" in result]
            if skipped_companies:
                skipped_df = pd.DataFrame([{
                    "Company": result["company"],
                    "Post Count": result["post_count"],
                    "Reason": result["error"]
                } for result in skipped_companies])
                skipped_df.to_excel(writer, sheet_name="Skipped Companies", index=False)
            
            # GPT Summary
            if gpt_summary:
                summary_text_df = pd.DataFrame([{"Summary": gpt_summary}])
                summary_text_df.to_excel(writer, sheet_name="GPT Summary", index=False)
        
        logger.info(f"Excel file saved: {excel_file}")
    except Exception as e:
        logger.error(f"Error saving Excel file: {e}")
    
    logger.info("Audience affinity analysis complete.")
    return pickle_file
