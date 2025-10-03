"""
Agility Analysis - Merges all agility files into a master PR file
Reads all .xlsx files from new_data/agility and merges their 'Raw Data' sheets
into a single master file for PR analysis
"""

import os
import sys
import pandas as pd
import logging
from typing import List, Optional

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import NEW_DATA_DIR, DASHBOARD_DATA_DIR, get_month_folder_name

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_agility_files() -> List[str]:
    """
    Get all .xlsx files from the agility directory
    
    Returns:
        List of file paths to agility Excel files
    """
    agility_dir = os.path.join(NEW_DATA_DIR, "agility")
    
    if not os.path.exists(agility_dir):
        logger.error(f"Agility directory not found: {agility_dir}")
        return []
    
    # Get all .xlsx files (excluding backup folder)
    excel_files = []
    for file in os.listdir(agility_dir):
        if file.endswith('.xlsx') and not file.startswith('~$'):  # Exclude temp files
            file_path = os.path.join(agility_dir, file)
            excel_files.append(file_path)
    
    logger.info(f"Found {len(excel_files)} agility Excel files")
    return excel_files

def read_agility_file(file_path: str) -> Optional[pd.DataFrame]:
    """
    Read the 'Raw Data' sheet from an agility Excel file
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        DataFrame with the raw data, or None if error
    """
    try:
        # Check if 'Raw Data' sheet exists
        excel_file = pd.ExcelFile(file_path)
        if 'Raw Data' not in excel_file.sheet_names:
            logger.warning(f"No 'Raw Data' sheet found in {file_path}")
            return None
        
        # Read the Raw Data sheet
        df = pd.read_excel(file_path, sheet_name='Raw Data')
        
        # Add source file information
        df['source_file'] = os.path.basename(file_path)
        
        logger.info(f"Loaded {len(df)} rows from {os.path.basename(file_path)}")
        return df
        
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

def merge_agility_data() -> Optional[pd.DataFrame]:
    """
    Merge all agility files into a single DataFrame
    
    Returns:
        Combined DataFrame with all agility data, or None if error
    """
    logger.info("Starting agility data merge process")
    
    # Get all agility files
    agility_files = get_agility_files()
    
    if not agility_files:
        logger.error("No agility files found to merge")
        return None
    
    # Read all files
    dataframes = []
    for file_path in agility_files:
        df = read_agility_file(file_path)
        if df is not None and not df.empty:
            dataframes.append(df)
    
    if not dataframes:
        logger.error("No valid data found in agility files")
        return None
    
    # Merge all dataframes
    try:
        merged_df = pd.concat(dataframes, ignore_index=True)
        logger.info(f"Successfully merged {len(dataframes)} files into {len(merged_df)} total rows")
        
        # Remove duplicates based on content if it exists
        if 'content' in merged_df.columns:
            initial_count = len(merged_df)
            merged_df = merged_df.drop_duplicates(subset=['content'], keep='first')
            final_count = len(merged_df)
            if initial_count != final_count:
                logger.info(f"Removed {initial_count - final_count} duplicate content entries")
        
        return merged_df
        
    except Exception as e:
        logger.error(f"Error merging agility data: {e}")
        return None

def create_master_pr_file(year: int, month: int, merged_data: pd.DataFrame) -> str:
    """
    Create the master PR file from merged agility data
    
    Args:
        year: Analysis year
        month: Analysis month
        merged_data: Merged DataFrame from all agility files
        
    Returns:
        Path to the created master file
    """
    # Create output directory
    month_folder = get_month_folder_name(year, month)
    output_dir = os.path.join(DASHBOARD_DATA_DIR, month_folder, "pr")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create output file path
    output_file = os.path.join(output_dir, "pr_master_data.xlsx")
    
    try:
        # Save to Excel with a single sheet
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            merged_data.to_excel(writer, sheet_name='Master Data', index=False)
        
        logger.info(f"Created master PR file: {output_file}")
        logger.info(f"File contains {len(merged_data)} rows and {len(merged_data.columns)} columns")
        
        return output_file
        
    except Exception as e:
        logger.error(f"Error creating master PR file: {e}")
        return None

def analyze_agility_for_month(year: int, month: int, output_folder: str = None) -> str:
    """
    Main function to merge agility data and create master PR file
    
    Args:
        year: Analysis year
        month: Analysis month
        output_folder: Output folder path (not used, determined automatically)
        
    Returns:
        Path to the created master PR file
    """
    logger.info(f"Starting agility analysis for {year}-{month:02d}")
    
    # Merge all agility data
    merged_data = merge_agility_data()
    
    if merged_data is None or merged_data.empty:
        logger.error("No agility data to process")
        return None
    
    # Create master PR file
    master_file = create_master_pr_file(year, month, merged_data)
    
    if master_file:
        logger.info(f"Agility analysis completed successfully: {master_file}")
        
        # Log summary statistics
        logger.info(f"Summary:")
        logger.info(f"  - Total rows: {len(merged_data)}")
        logger.info(f"  - Total columns: {len(merged_data.columns)}")
        logger.info(f"  - Source files: {merged_data['source_file'].nunique() if 'source_file' in merged_data.columns else 'Unknown'}")
        
        # Log column information
        if 'content' in merged_data.columns:
            logger.info(f"  - Content entries: {merged_data['content'].notna().sum()}")
        if 'company' in merged_data.columns:
            logger.info(f"  - Unique companies: {merged_data['company'].nunique()}")
        if 'Impressions' in merged_data.columns:
            logger.info(f"  - Total impressions: {merged_data['Impressions'].sum() if merged_data['Impressions'].dtype in ['int64', 'float64'] else 'N/A'}")
    
    return master_file

if __name__ == "__main__":
    # Test the function
    from config import ANALYSIS_YEAR, ANALYSIS_MONTH
    
    result = analyze_agility_for_month(ANALYSIS_YEAR, ANALYSIS_MONTH)
    if result:
        print(f"SUCCESS: Agility analysis completed: {result}")
    else:
        print("ERROR: Agility analysis failed")
