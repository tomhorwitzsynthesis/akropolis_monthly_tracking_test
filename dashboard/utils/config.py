# utils/config.py

import os

# Top-level folder where your data is stored - updated to use dashboard_data
# Check if we're running from dashboard directory or root directory
if os.path.exists("dashboard_data"):
    DATA_ROOT = "dashboard_data"
else:
    DATA_ROOT = os.path.join("..", "dashboard_data")

# Analysis Configuration - Set the month you want to analyze
ANALYSIS_YEAR = 2025
ANALYSIS_MONTH = 9  # Change this to the month you want to analyze (1-12)

# Brands to include in the dashboard - updated for Akropolis context
BRANDS = ["Akropolis", "Akropolis Group", "BIG", "MEGA", "OZAS", "PANORAMA", "Outlet Park", "Molas", "Nordika", "CUP", "EUROPA", "G9", "Kauno Akropolis", "Klaipeda Akropolis", "Siauliai Akropolis", "Vilnius Akropolis", "Saules Miestos"]

# Company clusters for selection
AKROPOLIS_LOCATIONS = ["Klaipeda Akropolis", "Vilnius Akropolis", "Siauliai Akropolis"]
BIG_PLAYERS = ["OZAS", "PANORAMA", "Kauno Akropolis", "Akropolis Group"]
SMALLER_PLAYERS = ["BIG", "MEGA", "Outlet Park", "Molas", "Nordika", "Saules Miestos"]
OTHER_CITIES = ["CUP", "EUROPA", "G9"]
RETAIL = ["IKI", "Lidl", "Maxima", "Rimi"]  # Main retail brand

BRAND_NAME_MAPPING = {
    "Akropolis": "Akropolis",
    "Big": "Big",
    "Mega": "Mega", 
    "Oz": "Oz",
    "Panorama": "Panorama",
    "Outlet Park": "Outlet Park",
    "Molas": "Molas",
    "Nordika": "Nordika",
    "CUP": "CUP",
    "Europa": "Europa",
    "G9": "G9",
    "Kauno Akropolis": "Kauno Akropolis",
    "Klaipeda Akropolis": "Klaipeda Akropolis",
    "Siauliai Akropolis": "Siauliai Akropolis",
    "Vilnius Akropolis": "Vilnius Akropolis",
    "Saules Miestos": "Saules Miestos"
}

BRAND_COLORS = {
    "Akropolis Group": "#228B22",  # Forest Green for Akropolis Group
    "BIG": "#4083B3",  # Blue
    "MEGA": "#2FB375",  # Teal/Green
    "OZAS": "#FF0E0E",  # Red
    "PANORAMA": "#FF9896",  # Light Red / Pink
    "Outlet Park": "#BECFE6",  # Light Blue
    "Vilnius Outlet": "#87CEEB",  # Sky Blue
    "Molas": "#DDA0DD",  # Plum
    "Nordika": "#F0E68C",  # Khaki
    "CUP": "#FFA07A",  # Light Salmon
    "EUROPA": "#98FB98",  # Pale Green
    "G9": "#F5DEB3",  # Wheat
    "Kauno Akropolis": "#FF6B6B",  # Coral Red
    "Klaipeda Akropolis": "#4ECDC4",  # Turquoise
    "Siauliai Akropolis": "#45B7D1",  # Sky Blue
    "Vilnius Akropolis": "#96CEB4",  # Mint Green
    "Saules Miestos": "#FFEAA7",  # Soft Yellow
    "IKI": "#FFA07A",  # Light Salmon
    "Lidl": "#98FB98",  # Pale Green
    "Maxima": "#4ECDC4",  # Turquoise
    "Rimi": "#45B7D1",  # Sky Blue
}

# Separate brand color mappings for different sections
# These use the normalized brand names that each section actually uses

# Ads section brand colors (using original brand names from ads data - LEFT side of ADS_BRAND_MAPPING)
ADS_BRAND_COLORS = {
    "AKROPOLIS | Vilnius": "#96CEB4",  # Mint Green
    "AKROPOLIS | Šiauliai": "#45B7D1",  # Sky Blue
    "AKROPOLIS | Klaipėda": "#4ECDC4",  # Turquoise
    "Kauno Akropolis": "#FF6B6B",  # Coral Red
    "OZAS": "#FF0E0E",  # Red
    "PANORAMA": "#FF9896",  # Light Red / Pink
    "BIG Vilnius": "#4083B3",  # Blue
    "CUP prekybos centras": "#FFA07A",  # Light Salmon
    "PC Europa": "#98FB98",  # Pale Green
    "PLC Mega": "#2FB375",  # Teal/Green
    "SAULĖS MIESTAS": "#FFEAA7",  # Soft Yellow
    "MOLAS Klaipėda": "#DDA0DD",  # Plum
    "Vilnius Outlet": "#87CEEB",  # Sky Blue
    "Outlet Park": "#BECFE6",  # Light Blue
    "Rimi Lietuva": "#45B7D1",  # Sky Blue
    "IKI": "#FFA07A",  # Light Salmon
    "Lidl Lietuva": "#98FB98",  # Pale Green
    "Maxima LT": "#4ECDC4",  # Turquoise
}

# Social Media section brand colors (using normalized names from social media data)
SOCIAL_MEDIA_BRAND_COLORS = {
    "Vilnius Akropolis": "#96CEB4",  # Mint Green
    "Siauliai Akropolis": "#45B7D1",  # Sky Blue
    "Klaipeda Akropolis": "#4ECDC4",  # Turquoise
    "Kauno Akropolis": "#FF6B6B",  # Coral Red
    "BIG": "#4083B3",  # Blue
    "OZAS": "#FF0E0E",  # Red
    "PANORAMA": "#FF9896",  # Light Red / Pink
    "CUP": "#FFA07A",  # Light Salmon
    "EUROPA": "#98FB98",  # Pale Green
    "G9": "#F5DEB3",  # Wheat
    "Outlet Park": "#BECFE6",  # Light Blue
    "IKI": "#FFA07A",  # Light Salmon
    "Lidl": "#98FB98",  # Pale Green
    "Maxima": "#4ECDC4",  # Turquoise
    "Rimi": "#45B7D1",  # Sky Blue
}

# PR section brand colors (using normalized names from PR data)
PR_BRAND_COLORS = {
    "Vilnius Akropolis": "#96CEB4",  # Mint Green
    "Siauliai Akropolis": "#45B7D1",  # Sky Blue
    "Klaipeda Akropolis": "#4ECDC4",  # Turquoise
    "Kauno Akropolis": "#FF6B6B",  # Coral Red
    "BIG": "#4083B3",  # Blue
    "OZAS": "#FF0E0E",  # Red
    "PANORAMA": "#FF9896",  # Light Red / Pink
    "CUP": "#FFA07A",  # Light Salmon
    "EUROPA": "#98FB98",  # Pale Green
    "G9": "#F5DEB3",  # Wheat
    "Outlet Park": "#BECFE6",  # Light Blue
    "IKI": "#FFA07A",  # Light Salmon
    "Lidl": "#98FB98",  # Pale Green
    "Maxima": "#4ECDC4",  # Turquoise
    "Rimi": "#45B7D1",  # Sky Blue
}

# Brand column mapping for different media types
BRAND_COLUMNS = {
    "ads": "ad_details/advertiser/ad_library_page_info/page_info/page_name",
    "social_media": "page_name",  # Use page_name instead of brand for social media
    "pr": "company"
}

# Brand mappings are now separated by media type for consistency:
# - SOCIAL_MEDIA_BRAND_MAPPING: Maps social media page names to standard names
# - PR_BRAND_MAPPING: Maps PR company names to standard names  
# - ADS_BRAND_MAPPING: Maps ads brand names to standard names

# Social Media specific brand mappings
SOCIAL_MEDIA_BRAND_MAPPING = {
    # Social media page names -> Standard names (from actual data)
    "AKROPOLIS | Klaipėda": "Klaipeda Akropolis",
    "AKROPOLIS | Šiauliai": "Siauliai Akropolis", 
    "AKROPOLIS | Vilnius": "Vilnius Akropolis",
    "BIG Vilnius": "BIG",
    "CUP prekybos centras": "CUP",
    "G9": "G9",
    "IKI": "IKI",
    "Kauno Akropolis": "Kauno Akropolis",
    "Lidl Lietuva": "Lidl",
    "Maxima LT": "Maxima",
    "MOLAS Klaipėda": "Molas",
    "Outlet Park": "Outlet Park",
    "OZAS": "OZAS",
    "PANORAMA": "PANORAMA",
    "PC Europa": "EUROPA",
    "PLC Mega": "MEGA",
    "Rimi Lietuva": "Rimi",
    "SAULĖS MIESTAS": "Saules Miestos",
    "Vilnius Outlet": "Vilnius Outlet"
}

# PR specific brand mappings
PR_BRAND_MAPPING = {
    # PR company names -> Standard names (from actual data)
    "Akropolis Group": "Akropolis Group",  # Separate entity for the overall Akropolis brand
    "BIG": "BIG",
    "CUP": "CUP",
    "Europa": "EUROPA", 
    "G9": "G9",
    "Ak": "Kauno Akropolis",
    "Akro": "Klaipeda Akropolis",
    "Akrop": "Siauliai Akropolis",
    "Akr": "Vilnius Akropolis",
    "Mega": "MEGA",
    "Molas": "Molas",
    "Nordika": "Nordika",
    "outlet": "Outlet Park",
    "Outlet": "Vilnius Outlet",
    "outle": "Outlet Park",
    "Ozas": "OZAS",
    "Panorama": "PANORAMA",
    "saul": "Saules Miestos"
}

# Ads specific brand mappings (updated based on actual ads data)
ADS_BRAND_MAPPING = {
    # Ads brand names -> Standard names (from actual data)
    "AKROPOLIS | Vilnius": "Vilnius Akropolis",
    "AKROPOLIS | Šiauliai": "Siauliai Akropolis", 
    "AKROPOLIS | Klaipėda": "Klaipeda Akropolis",
    "Kauno Akropolis": "Kauno Akropolis", 
    "OZAS": "OZAS",
    "PANORAMA": "PANORAMA",
    "BIG Vilnius": "BIG",
    "CUP prekybos centras": "CUP",
    "PC Europa": "EUROPA",
    "PLC Mega": "MEGA",
    "SAULĖS MIESTAS": "Saules Miestos",
    "MOLAS Klaipėda": "Molas",
    "Vilnius Outlet": "Outlet Park",
    "Outlet Park": "Outlet Park",
    "Rimi Lietuva": "Rimi",
    "IKI": "IKI",
    "Lidl Lietuva": "Lidl",
    "Maxima LT": "Maxima"
}

# Specific mapping for ads creativity data (from Overall Ranking sheet)
ADS_CREATIVITY_BRAND_MAPPING = {
    "Kauno Akropolis": "Kauno Akropolis",
    "CUP prekybos centras": "CUP",
    "BIG Vilnius": "BIG",
    "AKROPOLIS | Vilnius": "Vilnius Akropolis",
    "Outlet Park": "Outlet Park",
    "PANORAMA": "PANORAMA",
    "PC Europa": "EUROPA",
    "Maxima LT": "Maxima",
    "IKI": "IKI",
    "Lidl Lietuva": "Lidl",
    "Rimi Lietuva": "Rimi",
    "G9": "G9",
    "AKROPOLIS | Šiauliai": "Siauliai Akropolis",
    "Vilnius Outlet": "Outlet Park"
}

# Specific mapping for ads key advantages data (from sheet names)
ADS_KEY_ADVANTAGES_BRAND_MAPPING = {
    "PC_Europa": "EUROPA",
    "Maxima_LT": "Maxima",
    "Kauno_Akropolis": "Kauno Akropolis",
    "IKI": "IKI",
    "PANORAMA": "PANORAMA",
    "AKROPOLIS___Vilnius": "Vilnius Akropolis",
    "G9": "G9",
    "Vilnius_Outlet": "Outlet Park",
    "Outlet_Park": "Outlet Park",
    "AKROPOLIS____iauliai": "Siauliai Akropolis",
    "BIG_Vilnius": "BIG",
    "Lidl_Lietuva": "Lidl",
    "CUP_prekybos_centras": "CUP",
    "Rimi_Lietuva": "Rimi"
}

def normalize_brand_name(brand_name: str, media_type: str, is_creativity_data: bool = False, is_key_advantages_data: bool = False) -> str:
    """Normalize brand name to standard format"""
    if not isinstance(brand_name, str):
        return ""
    
    # Clean the brand name
    cleaned = brand_name.strip()
    
    # Apply mapping based on media type
    if media_type == "social_media" and cleaned in SOCIAL_MEDIA_BRAND_MAPPING:
        return SOCIAL_MEDIA_BRAND_MAPPING[cleaned]
    elif media_type == "pr" and cleaned in PR_BRAND_MAPPING:
        return PR_BRAND_MAPPING[cleaned]
    elif media_type == "ads":
        # Use specific key advantages mapping if this is key advantages data
        if is_key_advantages_data and cleaned in ADS_KEY_ADVANTAGES_BRAND_MAPPING:
            return ADS_KEY_ADVANTAGES_BRAND_MAPPING[cleaned]
        # Use specific creativity mapping if this is creativity data
        elif is_creativity_data and cleaned in ADS_CREATIVITY_BRAND_MAPPING:
            return ADS_CREATIVITY_BRAND_MAPPING[cleaned]
        elif cleaned in ADS_BRAND_MAPPING:
            return ADS_BRAND_MAPPING[cleaned]
    
    # Fallback: return cleaned name
    return cleaned

def get_brand_column(media_type: str) -> str:
    """Get the brand column name for a media type"""
    return BRAND_COLUMNS.get(media_type, "brand")

def get_brand_colors(media_type: str) -> dict:
    """Get the appropriate brand colors for a media type"""
    if media_type == "ads":
        return ADS_BRAND_COLORS
    elif media_type == "social_media":
        return SOCIAL_MEDIA_BRAND_COLORS
    elif media_type == "pr":
        return PR_BRAND_COLORS
    else:
        return BRAND_COLORS  # Fallback to original