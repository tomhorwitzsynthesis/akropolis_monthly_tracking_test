"""
Data processing utilities for monthly dashboard
"""
import pandas as pd
import os
from typing import Dict, Any, Optional, List
from config import MEDIA_TYPES
from .folder_manager import get_new_data_path, get_dashboard_data_path
from .timezone_fix import remove_timezone_from_dataframe, safe_to_datetime

def load_new_data(media_type: str, year: int = None, month: int = None) -> pd.DataFrame:
    """
    Load new data for specific media type, filtered by month if specified
    """
    if media_type not in MEDIA_TYPES:
        raise ValueError(f"Unknown media type: {media_type}")
    
    media_config = MEDIA_TYPES[media_type]
    file_path = os.path.join(get_new_data_path(media_type), media_config["master_file"])
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Master file not found: {file_path}")
    
    # Load the data
    df = pd.read_excel(file_path)
    
    # Clean datetime columns to remove timezone information (prevents Excel export errors)
    df = remove_timezone_from_dataframe(df)
    
    # Filter by month if year and month are specified
    if year is not None and month is not None:
        print(f"Filtering {media_type} data for {year}-{month:02d}...")
        df = filter_data_by_month(df, year, month)
        print(f"Loaded {len(df)} {media_type} items for {year}-{month:02d}")
    else:
        print(f"Loaded {len(df)} {media_type} items (no month filtering)")
    
    return df

def load_existing_dashboard_data(year: int, month: int, media_type: str) -> Optional[pd.DataFrame]:
    """
    Load existing dashboard data for specific month and media type
    Returns None if no existing data
    """
    folder_path = get_dashboard_data_path(year, month, media_type)
    master_file = os.path.join(folder_path, f"{media_type}_master_data.xlsx")
    
    if not os.path.exists(master_file):
        return None
    
    return pd.read_excel(master_file)

def append_monthly_data(year: int, month: int, media_type: str, 
                       new_data: pd.DataFrame, overwrite: bool = False) -> str:
    """
    Append new monthly data to dashboard data
    Returns path to saved file
    """
    # Add month and year columns to new data
    new_data = new_data.copy()
    new_data['year'] = year
    new_data['month'] = month
    new_data['analysis_date'] = pd.Timestamp.now().tz_localize(None)  # Ensure timezone-naive
    
    # Load existing data if it exists
    existing_data = load_existing_dashboard_data(year, month, media_type)
    
    if existing_data is not None and not overwrite:
        # Append new data to existing
        combined_data = pd.concat([existing_data, new_data], ignore_index=True)
        # Remove duplicates based on content (if text column exists)
        text_col = MEDIA_TYPES[media_type]["text_column"]
        if text_col in combined_data.columns:
            combined_data = combined_data.drop_duplicates(subset=[text_col], keep='last')
    else:
        combined_data = new_data
    
    # Save combined data
    folder_path = get_dashboard_data_path(year, month, media_type)
    os.makedirs(folder_path, exist_ok=True)
    
    output_file = os.path.join(folder_path, f"{media_type}_master_data.xlsx")
    
    # Clean all datetime columns to remove timezone information before saving
    data_to_save = remove_timezone_from_dataframe(combined_data)
    
    data_to_save.to_excel(output_file, index=False)
    
    return output_file

def filter_data_by_month(df: pd.DataFrame, year: int, month: int, 
                        date_columns: list = None) -> pd.DataFrame:
    """
    Filter dataframe by specific month
    For ads: Only considers start date (startDateFormatted)
    For other media: Uses available date columns
    """
    if date_columns is None:
        # Common date column names to check
        # For social media, prioritize created_date over timestamp
        date_columns = [
            'startDateFormatted', 'endDateFormatted', 'date', 'created_at', 
            'created_date', 'published_date', 'timestamp', 'start_date', 'end_date'
        ]
    
    # Find which date columns exist in the dataframe
    available_date_columns = [col for col in date_columns if col in df.columns]
    
    if not available_date_columns:
        # If no date columns found, return all data
        print(f"Warning: No date columns found. Analyzing all data for {year}-{month:02d}")
        return df
    
    # For ads, prioritize startDateFormatted (start date only)
    if 'startDateFormatted' in available_date_columns:
        try:
            df_temp = df.copy()
            df_temp['startDateFormatted'] = safe_to_datetime(df_temp['startDateFormatted'], utc=True)
            
            # Filter by start date year and month only
            month_mask = (
                (df_temp['startDateFormatted'].dt.year == year) & 
                (df_temp['startDateFormatted'].dt.month == month)
            )
            
            if month_mask.any():
                filtered_df = df_temp[month_mask].copy()
                print(f"Found {len(filtered_df)} items with start date in {year}-{month:02d}")
                return filtered_df
            else:
                print(f"No items found with start date in {year}-{month:02d}")
                return df.iloc[0:0].copy()  # Return empty dataframe with same structure
                
        except Exception as e:
            print(f"Error filtering by startDateFormatted: {e}")
    
    # For other media types, try all available date columns
    filtered_dfs = []
    for date_col in available_date_columns:
        try:
            # Convert date column to datetime
            df_temp = df.copy()
            df_temp[date_col] = safe_to_datetime(df_temp[date_col], utc=True)
            
            # Filter by year and month
            month_mask = (
                (df_temp[date_col].dt.year == year) & 
                (df_temp[date_col].dt.month == month)
            )
            
            if month_mask.any():
                filtered_df = df_temp[month_mask].copy()
                filtered_dfs.append(filtered_df)
                print(f"Found {len(filtered_df)} items in {date_col} for {year}-{month:02d}")
        except Exception as e:
            print(f"Error filtering by {date_col}: {e}")
            continue
    
    if filtered_dfs:
        # Combine all filtered dataframes and remove duplicates
        combined_df = pd.concat(filtered_dfs, ignore_index=True)
        # Remove duplicates based on text content if available
        text_cols = [col for col in df.columns if 'text' in col.lower() or 'content' in col.lower()]
        if text_cols:
            combined_df = combined_df.drop_duplicates(subset=text_cols[0], keep='first')
        return combined_df
    else:
        print(f"Warning: No data found for {year}-{month:02d}. Analyzing all data.")
        return df

def validate_data_structure(df: pd.DataFrame, media_type: str) -> Dict[str, Any]:
    """
    Validate data structure for specific media type
    Returns validation results
    """
    media_config = MEDIA_TYPES[media_type]
    required_columns = [
        media_config["text_column"],
        media_config["brand_column"], 
        media_config["reach_column"]
    ]
    
    validation = {
        "valid": True,
        "missing_columns": [],
        "empty_rows": 0,
        "total_rows": len(df)
    }
    
    # Check for required columns
    for col in required_columns:
        if col not in df.columns:
            validation["missing_columns"].append(col)
            validation["valid"] = False
    
    if validation["valid"]:
        # Check for empty rows in required columns
        text_col = media_config["text_column"]
        brand_col = media_config["brand_column"]
        
        empty_mask = df[text_col].isna() | df[brand_col].isna()
        validation["empty_rows"] = empty_mask.sum()
        
        if validation["empty_rows"] > 0:
            validation["valid"] = False
    
    return validation

def clean_data(df: pd.DataFrame, media_type: str) -> pd.DataFrame:
    """
    Clean data for specific media type
    """
    media_config = MEDIA_TYPES[media_type]
    
    # Remove rows with missing required data
    text_col = media_config["text_column"]
    brand_col = media_config["brand_column"]
    reach_col = media_config["reach_column"]
    
    # Clean text data
    if text_col in df.columns:
        df[text_col] = df[text_col].astype(str).str.strip()
        df = df[df[text_col] != 'nan']
        df = df[df[text_col] != '']
    
    # Clean brand data
    if brand_col in df.columns:
        df = df[df[brand_col].notna()]
    
    # Clean reach data
    if reach_col in df.columns:
        df[reach_col] = pd.to_numeric(df[reach_col], errors='coerce')
        df = df[df[reach_col].notna()]
    
    return df.reset_index(drop=True)
