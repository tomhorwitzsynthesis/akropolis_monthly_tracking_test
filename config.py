"""
Configuration file for Monthly Dashboard Analysis
"""
import os
from datetime import datetime
from typing import Dict, Any

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, try to load .env manually
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set OPENAI_API_KEY in your .env file")

# Model Configuration
DEFAULT_MODEL = "gpt-4o-mini"
TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 2000

# Analysis Configuration
MAX_WORKERS = 20  # Increased for better parallelization (adjust based on API limits)
MAX_ADS_PER_BRAND = 50
TOP_K_PER_BRAND = 10
MAX_CHARS_PER_AD = 1000
MIN_ADS_FOR_ANALYSIS = 5  # Minimum number of ads required for creativity/key advantages analysis
MIN_POSTS_FOR_ANALYSIS = 5  # Minimum number of posts required for content pillars/audience affinity analysis

# Performance Notes:
# - MAX_WORKERS: Higher = faster but more API calls/second
# - OpenAI rate limits: ~60 requests/minute for gpt-4o-mini
# - With 8 workers: ~8 requests every few seconds = well within limits
# - If you hit rate limits, reduce MAX_WORKERS to 5 or 3

# Analysis Configuration - Set the month you want to analyze
ANALYSIS_YEAR = 2025
ANALYSIS_MONTH = 9  # Change this to the month you want to analyze (1-12)

# Analysis Control - Set to True to run specific analyses
ANALYSIS_CONTROL = {
    # Ads Analyses
    "ads_compos": False,
    "ads_creativity": False, 
    "ads_key_advantages": False,
    
    # Social Media Analyses
    "social_media_compos": True,
    "social_media_creativity": True,
    "social_media_content_pillars": True,
    "social_media_audience_affinity": True,
    
    # PR Analyses
    "pr_compos": False,
    "pr_creativity": False,
    "pr_agility": False,  # Merge agility files into master PR data
}

# File Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NEW_DATA_DIR = os.path.join(BASE_DIR, "new_data")
DASHBOARD_DATA_DIR = os.path.join(BASE_DIR, "dashboard_data")

# Media Types
MEDIA_TYPES = {
    "ads": {
        "folder": "ads",
        "master_file": "ads_master_file.xlsx",
        "text_column": "snapshot/body/text",
        "brand_column": "ad_details/advertiser/ad_library_page_info/page_info/page_name",
        "reach_column": "ad_details/aaa_info/eu_total_reach"
    },
    "social_media": {
        "folder": "social_media", 
        "master_file": "facebook_master_file.xlsx",
        "text_column": "content",
        "brand_column": "brand",
        "reach_column": "likes"
    },
    "pr": {
        "folder": "pr",
        "master_file": "pr_master_file.xlsx", 
        "text_column": "content",
        "brand_column": "company",
        "reach_column": "Impressions"
    }
}

# Analysis Types
ANALYSIS_TYPES = {
    "compos": {
        "name": "CompOS Analysis",
        "description": "Archetype assignment for content positioning",
        "overwrite": True
    },
    "creativity": {
        "name": "Creativity Analysis", 
        "description": "Originality and creativity ranking",
        "overwrite": True
    },
    "key_advantages": {
        "name": "Key Advantages",
        "description": "Extract key benefits and advantages",
        "overwrite": True
    },
    "audience_affinity": {
        "name": "Audience Affinity",
        "description": "Audience targeting analysis",
        "overwrite": True
    },
    "content_pillars": {
        "name": "Content Pillars",
        "description": "Content categorization and pillars",
        "overwrite": True
    },
    "agility": {
        "name": "Agility Data Merge",
        "description": "Merge agility files into master PR data",
        "overwrite": True
    }
}

def get_month_folder_name(year: int, month: int) -> str:
    """Generate folder name in YYYY-MM format"""
    return f"{year}-{month:02d}"

def get_current_month() -> tuple:
    """Get current year and month"""
    now = datetime.now()
    return now.year, now.month

def validate_month(year: int, month: int) -> bool:
    """Validate year and month values"""
    if not (2020 <= year <= 2030):
        return False
    if not (1 <= month <= 12):
        return False
    return True

def get_analysis_config(media_type: str, analysis_type: str) -> Dict[str, Any]:
    """Get configuration for specific media type and analysis"""
    if media_type not in MEDIA_TYPES:
        raise ValueError(f"Unknown media type: {media_type}")
    if analysis_type not in ANALYSIS_TYPES:
        raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    return {
        "media_config": MEDIA_TYPES[media_type],
        "analysis_config": ANALYSIS_TYPES[analysis_type]
    }
