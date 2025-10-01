"""
Folder management utilities for monthly dashboard
"""
import os
import shutil
from typing import List, Optional
from config import DASHBOARD_DATA_DIR, NEW_DATA_DIR, get_month_folder_name

def create_monthly_folders(year: int, month: int) -> dict:
    """
    Create folder structure for a specific month
    Returns dict with created folder paths
    """
    month_folder = get_month_folder_name(year, month)
    
    folders = {
        "month_root": os.path.join(DASHBOARD_DATA_DIR, month_folder),
        "ads": os.path.join(DASHBOARD_DATA_DIR, month_folder, "ads"),
        "social_media": os.path.join(DASHBOARD_DATA_DIR, month_folder, "social_media"),
        "pr": os.path.join(DASHBOARD_DATA_DIR, month_folder, "pr"),
    }
    
    # Create all media type folders
    for folder_path in folders.values():
        os.makedirs(folder_path, exist_ok=True)
    
    # Create analysis subfolders for each media type
    analysis_types = ["compos", "creativity", "key_advantages", "content_pillars", "audience_affinity"]
    for media_type in ["ads", "social_media", "pr"]:
        for analysis_type in analysis_types:
            analysis_folder = os.path.join(folders[media_type], "analysis", analysis_type)
            os.makedirs(analysis_folder, exist_ok=True)
    
    return folders

def get_monthly_folders(year: int, month: int) -> dict:
    """
    Get folder paths for a specific month (create if doesn't exist)
    """
    return create_monthly_folders(year, month)

def list_available_months() -> List[str]:
    """
    List all available months in dashboard_data
    """
    if not os.path.exists(DASHBOARD_DATA_DIR):
        return []
    
    months = []
    for item in os.listdir(DASHBOARD_DATA_DIR):
        item_path = os.path.join(DASHBOARD_DATA_DIR, item)
        if os.path.isdir(item_path) and len(item) == 7 and item[4] == '-':
            months.append(item)
    
    return sorted(months)

def get_new_data_path(media_type: str) -> str:
    """
    Get path to new data for specific media type
    """
    return os.path.join(NEW_DATA_DIR, media_type)

def get_dashboard_data_path(year: int, month: int, media_type: str) -> str:
    """
    Get path to dashboard data for specific month and media type
    """
    month_folder = get_month_folder_name(year, month)
    return os.path.join(DASHBOARD_DATA_DIR, month_folder, media_type)

def backup_existing_file(file_path: str) -> Optional[str]:
    """
    Create backup of existing file with timestamp
    Returns backup file path or None if no backup needed
    """
    if not os.path.exists(file_path):
        return None
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    return backup_path

def ensure_analysis_folder(year: int, month: int, analysis_type: str, media_type: str = None) -> str:
    """
    Ensure analysis folder exists for specific month, analysis type, and media type
    """
    month_folder = get_month_folder_name(year, month)
    
    if media_type:
        # New structure: media_type/analysis/analysis_type
        analysis_folder = os.path.join(DASHBOARD_DATA_DIR, month_folder, media_type, "analysis", analysis_type)
    else:
        # Legacy structure: analysis/analysis_type (for backward compatibility)
        analysis_folder = os.path.join(DASHBOARD_DATA_DIR, month_folder, "analysis", analysis_type)
    
    os.makedirs(analysis_folder, exist_ok=True)
    return analysis_folder
