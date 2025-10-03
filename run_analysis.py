"""
Simple analysis runner that uses the month configured in config.py
"""
import os
import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ANALYSIS_YEAR, ANALYSIS_MONTH, MEDIA_TYPES, ANALYSIS_TYPES, ANALYSIS_CONTROL
from utils.folder_manager import get_monthly_folders, ensure_analysis_folder
from utils.data_processor import load_new_data, append_monthly_data, validate_data_structure, clean_data
from analysis.ads.compos_analysis import analyze_compos_for_month as analyze_ads_compos
from analysis.ads.creativity_analysis import analyze_creativity_for_month as analyze_ads_creativity
from analysis.ads.key_advantages import analyze_key_advantages_for_month as analyze_ads_key_advantages
from analysis.social_media.compos_analysis import analyze_compos_for_month as analyze_social_compos
from analysis.social_media.creativity_analysis import analyze_creativity_for_month as analyze_social_creativity
from analysis.social_media.content_pillars import analyze_content_pillars_for_month as analyze_social_content_pillars
from analysis.social_media.audience_affinity import analyze_audience_affinity_for_month as analyze_social_audience_affinity
from analysis.pr.compos_analysis import analyze_compos_for_month as analyze_pr_compos
from analysis.pr.creativity_analysis import analyze_creativity_for_month as analyze_pr_creativity
from analysis.pr.agility_analysis import analyze_agility_for_month as analyze_pr_agility

def main():
    """Run analysis for the configured month"""
    print("=" * 60)
    print("Monthly Dashboard Analysis")
    print("=" * 60)
    print(f"Analyzing data for: {ANALYSIS_YEAR}-{ANALYSIS_MONTH:02d}")
    print()
    
    # Show which analyses are enabled
    enabled_analyses = [key for key, value in ANALYSIS_CONTROL.items() if value]
    if enabled_analyses:
        print("Enabled analyses:")
        for analysis in enabled_analyses:
            print(f"  [OK] {analysis}")
    else:
        print("[WARNING] No analyses enabled in config.py")
    print()
    
    # Check if API key is loaded
    try:
        from config import OPENAI_API_KEY
        if OPENAI_API_KEY:
            print("[OK] OpenAI API key loaded successfully")
        else:
            print("[ERROR] OpenAI API key not found. Please check your .env file")
    except Exception as e:
        print(f"[ERROR] Error loading configuration: {e}")
    print()
    
    # Create monthly folders
    folders = get_monthly_folders(ANALYSIS_YEAR, ANALYSIS_MONTH)
    print(f"Created/verified folders for {ANALYSIS_YEAR}-{ANALYSIS_MONTH:02d}")
    
    results = {
        "processed_data": {},
        "analyses": {},
        "errors": []
    }
    
    # Determine which media types to process based on enabled analyses
    media_types_to_process = set()
    for analysis_key in ANALYSIS_CONTROL:
        if ANALYSIS_CONTROL[analysis_key]:
            # Parse media type from analysis key
            parts = analysis_key.split('_')
            if parts[0] == "social" and parts[1] == "media":
                media_type = "social_media"
            elif parts[0] == "ads":
                media_type = "ads"
            elif parts[0] == "pr":
                media_type = "pr"
            else:
                media_type = parts[0]  # fallback
            media_types_to_process.add(media_type)
    
    if not media_types_to_process:
        print("No analyses enabled. Please set at least one analysis to True in config.py")
        return
    
    print(f"Processing media types: {', '.join(media_types_to_process)}")
    print()
    
    # Process each media type that has enabled analyses
    for media_type in media_types_to_process:
        print(f"\n--- Processing {media_type.upper()} ---")
        
        # Special handling for PR with agility analysis
        if media_type == "pr" and ANALYSIS_CONTROL.get("pr_agility", False):
            print("Using agility data merge instead of standard PR data loading")
            # Skip the normal data loading for PR when agility is enabled
            # The agility analysis will create the master file directly
        else:
            try:
                # Load and filter data for the configured month
                new_data = load_new_data(media_type, ANALYSIS_YEAR, ANALYSIS_MONTH)
                
                if len(new_data) == 0:
                    print(f"No {media_type} data found for {ANALYSIS_YEAR}-{ANALYSIS_MONTH:02d}")
                    continue
                
                # Validate data structure
                validation = validate_data_structure(new_data, media_type)
                if not validation["valid"]:
                    error_msg = f"Data validation failed for {media_type}: {validation}"
                    print(f"[ERROR] {error_msg}")
                    results["errors"].append(error_msg)
                    continue
                
                # Clean data
                cleaned_data = clean_data(new_data, media_type)
                print(f"[OK] Loaded and cleaned {len(cleaned_data)} {media_type} items")
                
                # Append to dashboard data
                output_file = append_monthly_data(
                    ANALYSIS_YEAR, ANALYSIS_MONTH, media_type, cleaned_data, overwrite=False
                )
                results["processed_data"][media_type] = output_file
                print(f"[OK] Saved to: {os.path.basename(output_file)}")
                
            except Exception as e:
                error_msg = f"Failed to process {media_type} data: {e}"
                print(f"[ERROR] {error_msg}")
                results["errors"].append(error_msg)
                continue
        
        # Run analyses for this media type based on config
        print(f"\nRunning analyses for {media_type}...")
        results["analyses"][media_type] = {}
        
        # Check which analyses are enabled for this media type
        enabled_for_media = [key for key, value in ANALYSIS_CONTROL.items() 
                           if value and key.startswith(media_type)]
        
        if not enabled_for_media:
            print(f"  No analyses enabled for {media_type}")
            continue
        
        # CompOS Analysis
        if f"{media_type}_compos" in ANALYSIS_CONTROL and ANALYSIS_CONTROL[f"{media_type}_compos"]:
            try:
                print("  - CompOS Analysis...")
                compos_folder = ensure_analysis_folder(ANALYSIS_YEAR, ANALYSIS_MONTH, "compos", media_type)
                
                # Use appropriate function based on media type
                if media_type == "ads":
                    compos_output = analyze_ads_compos(ANALYSIS_YEAR, ANALYSIS_MONTH, compos_folder)
                elif media_type == "social_media":
                    compos_output = analyze_social_compos(ANALYSIS_YEAR, ANALYSIS_MONTH, compos_folder)
                elif media_type == "pr":
                    compos_output = analyze_pr_compos(ANALYSIS_YEAR, ANALYSIS_MONTH, compos_folder)
                else:
                    print(f"    [SKIP] CompOS analysis not implemented for {media_type}")
                    continue
                
                if compos_output:
                    results["analyses"][media_type]["compos"] = compos_output
                    print(f"    [OK] Saved: {os.path.basename(compos_output)}")
                else:
                    error_msg = f"CompOS analysis failed for {media_type} - no output file"
                    print(f"    [ERROR] {error_msg}")
                    results["errors"].append(error_msg)
            except Exception as e:
                error_msg = f"CompOS analysis failed for {media_type}: {e}"
                print(f"    [ERROR] {error_msg}")
                results["errors"].append(error_msg)
        
        # Creativity Analysis
        if f"{media_type}_creativity" in ANALYSIS_CONTROL and ANALYSIS_CONTROL[f"{media_type}_creativity"]:
            try:
                print("  - Creativity Analysis...")
                creativity_folder = ensure_analysis_folder(ANALYSIS_YEAR, ANALYSIS_MONTH, "creativity", media_type)
                
                # Use appropriate function based on media type
                if media_type == "ads":
                    creativity_output = analyze_ads_creativity(ANALYSIS_YEAR, ANALYSIS_MONTH, creativity_folder)
                elif media_type == "social_media":
                    creativity_output = analyze_social_creativity(ANALYSIS_YEAR, ANALYSIS_MONTH, creativity_folder)
                elif media_type == "pr":
                    creativity_output = analyze_pr_creativity(ANALYSIS_YEAR, ANALYSIS_MONTH, creativity_folder)
                else:
                    print(f"    [SKIP] Creativity analysis not implemented for {media_type}")
                    continue
                
                if creativity_output:
                    results["analyses"][media_type]["creativity"] = creativity_output
                    print(f"    [OK] Saved: {os.path.basename(creativity_output)}")
                else:
                    error_msg = f"Creativity analysis failed for {media_type} - no output file"
                    print(f"    [ERROR] {error_msg}")
                    results["errors"].append(error_msg)
            except Exception as e:
                error_msg = f"Creativity analysis failed for {media_type}: {e}"
                print(f"    [ERROR] {error_msg}")
                results["errors"].append(error_msg)
        
        # Key Advantages Analysis
        if f"{media_type}_key_advantages" in ANALYSIS_CONTROL and ANALYSIS_CONTROL[f"{media_type}_key_advantages"]:
            try:
                print("  - Key Advantages Analysis...")
                ka_folder = ensure_analysis_folder(ANALYSIS_YEAR, ANALYSIS_MONTH, "key_advantages", media_type)
                
                # Use appropriate function based on media type
                if media_type == "ads":
                    ka_output = analyze_ads_key_advantages(ANALYSIS_YEAR, ANALYSIS_MONTH, ka_folder)
                else:
                    print(f"    [SKIP] Key Advantages analysis not implemented for {media_type}")
                    continue
                
                results["analyses"][media_type]["key_advantages"] = ka_output
                print(f"    ✅ Saved: {os.path.basename(ka_output)}")
            except Exception as e:
                error_msg = f"Key Advantages analysis failed for {media_type}: {e}"
                print(f"    [ERROR] {error_msg}")
                results["errors"].append(error_msg)
        
        # Content Pillars Analysis
        if f"{media_type}_content_pillars" in ANALYSIS_CONTROL and ANALYSIS_CONTROL[f"{media_type}_content_pillars"]:
            try:
                print("  - Content Pillars Analysis...")
                content_pillars_folder = ensure_analysis_folder(ANALYSIS_YEAR, ANALYSIS_MONTH, "content_pillars", media_type)
                
                # Use appropriate function based on media type
                if media_type == "social_media":
                    content_pillars_output = analyze_social_content_pillars(ANALYSIS_YEAR, ANALYSIS_MONTH, content_pillars_folder)
                else:
                    print(f"    ⏸️  Content Pillars analysis not implemented for {media_type}")
                    continue
                
                if content_pillars_output:
                    results["analyses"][media_type]["content_pillars"] = content_pillars_output
                    print(f"    ✅ Saved: {os.path.basename(content_pillars_output)}")
                else:
                    error_msg = f"Content Pillars analysis failed for {media_type}"
                    print(f"    [ERROR] {error_msg}")
                    results["errors"].append(error_msg)
                    
            except Exception as e:
                error_msg = f"Content Pillars analysis failed for {media_type}: {e}"
                print(f"    [ERROR] {error_msg}")
                results["errors"].append(error_msg)
        
        # Audience Affinity Analysis
        if f"{media_type}_audience_affinity" in ANALYSIS_CONTROL and ANALYSIS_CONTROL[f"{media_type}_audience_affinity"]:
            try:
                print("  - Audience Affinity Analysis...")
                audience_affinity_folder = ensure_analysis_folder(ANALYSIS_YEAR, ANALYSIS_MONTH, "audience_affinity", media_type)
                
                # Use appropriate function based on media type
                if media_type == "social_media":
                    audience_affinity_output = analyze_social_audience_affinity(ANALYSIS_YEAR, ANALYSIS_MONTH, audience_affinity_folder)
                else:
                    print(f"    ⏸️  Audience Affinity analysis not implemented for {media_type}")
                    continue
                
                if audience_affinity_output:
                    results["analyses"][media_type]["audience_affinity"] = audience_affinity_output
                    print(f"    ✅ Saved: {os.path.basename(audience_affinity_output)}")
                else:
                    error_msg = f"Audience Affinity analysis failed for {media_type}"
                    print(f"    [ERROR] {error_msg}")
                    results["errors"].append(error_msg)
                    
            except Exception as e:
                error_msg = f"Audience Affinity analysis failed for {media_type}: {e}"
                print(f"    [ERROR] {error_msg}")
                results["errors"].append(error_msg)
        
        # Agility Analysis (PR only)
        if f"{media_type}_agility" in ANALYSIS_CONTROL and ANALYSIS_CONTROL[f"{media_type}_agility"]:
            try:
                print("  - Agility Data Merge...")
                
                # Use appropriate function based on media type
                if media_type == "pr":
                    agility_output = analyze_pr_agility(ANALYSIS_YEAR, ANALYSIS_MONTH)
                else:
                    print(f"    [SKIP] Agility analysis not implemented for {media_type}")
                    continue
                
                if agility_output:
                    results["analyses"][media_type]["agility"] = agility_output
                    results["processed_data"][media_type] = agility_output  # Mark as processed data
                    print(f"    [OK] Saved: {os.path.basename(agility_output)}")
                else:
                    error_msg = f"Agility analysis failed for {media_type}"
                    print(f"    [ERROR] {error_msg}")
                    results["errors"].append(error_msg)
                    
            except Exception as e:
                error_msg = f"Agility analysis failed for {media_type}: {e}"
                print(f"    [ERROR] {error_msg}")
                results["errors"].append(error_msg)
    
    # Summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETED")
    print("=" * 60)
    print(f"Month: {ANALYSIS_YEAR}-{ANALYSIS_MONTH:02d}")
    print(f"Processed data: {list(results['processed_data'].keys())}")
    
    for media_type, analyses in results["analyses"].items():
        if analyses:
            print(f"\n{media_type.upper()}:")
            for analysis_type, output_file in analyses.items():
                if output_file:
                    print(f"  {analysis_type}: {os.path.basename(output_file)}")
                else:
                    print(f"  {analysis_type}: Failed")
    
    if results["errors"]:
        print(f"\nErrors ({len(results['errors'])}):")
        for error in results["errors"]:
            print(f"  - {error}")
    
    print(f"\nAll files saved in: dashboard_data/{ANALYSIS_YEAR}-{ANALYSIS_MONTH:02d}/")
    print("\nTo analyze a different month, change ANALYSIS_YEAR and ANALYSIS_MONTH in config.py")

if __name__ == "__main__":
    main()
