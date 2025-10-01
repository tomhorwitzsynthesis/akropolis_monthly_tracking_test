# Monthly Dashboard - Akropolis Intelligence

This dashboard provides comprehensive analytics for Akropolis across multiple media types (Ads, Social Media, PR) with unified metrics and brand comparison capabilities.

## Features

### 🏢 Company Cluster Selection
- **Akropolis Locations**: Always included (Klaipeda, Siauliai, Vilnius, Saules Miestos)
- **Company Clusters**: 
  - **Big Players**: Big, Mega, Oz, Panorama, Kauno Akropolis
  - **Smaller Players**: Outlet Park, Molas, Nordika
  - **Other Cities**: CUP, Europa, G9
  - **Retail**: Akropolis (main retail brand)
- **Dynamic Selection**: Choose which Akropolis locations and competitor clusters to analyze

### 📅 Month Selection
- **Dynamic Discovery**: Automatically finds available months from `dashboard_data` folder
- **Range Selection**: Select start and end months for analysis
- **Current Available**: 2025-08, 2025-09 (automatically updated as new data is added)

### 📊 Comprehensive Metrics
The dashboard now includes three key metrics across all media types:

#### 1. **Reach/Engagement Metrics**
- **Ads**: Total reach from ad campaigns
- **Social Media**: Total likes/engagement
- **PR**: Total impressions from media coverage

#### 2. **Brand Strength**
- Based on CompOS archetype analysis
- Shows percentage of dominant archetype
- Indicates brand positioning consistency

#### 3. **Creativity Score**
- Originality and creativity ranking
- Cross-brand comparison
- AI-generated creativity analysis

### 🎯 Unified Brand Names
The dashboard handles different brand column names across media types:
- **Ads**: `ad_details/advertiser/ad_library_page_info/page_info/page_name`
- **Social Media**: `brand`
- **PR**: `company`

All brands are normalized to consistent display names for unified analysis.

## Data Structure

The dashboard expects data in the following structure:
```
dashboard_data/
├── 2025-08/
│   ├── ads/
│   │   ├── ads_master_data.xlsx
│   │   └── analysis/
│   │       ├── creativity/
│   │       │   └── creativity_analysis_ads.xlsx
│   │       └── compos/
│   │           └── compos_analysis_ads.xlsx
│   ├── social_media/
│   │   ├── social_media_master_data.xlsx
│   │   └── analysis/
│   │       ├── creativity/
│   │       │   └── creativity_analysis_social_media.xlsx
│   │       └── compos/
│   │           └── compos_analysis_social_media.xlsx
│   └── pr/
│       ├── pr_master_data.xlsx
│       └── analysis/
│           ├── creativity/
│           │   └── creativity_analysis_pr.xlsx
│           └── compos/
│               └── compos_analysis_pr.xlsx
└── 2025-09/
    └── ... (same structure)
```

## Running the Dashboard

1. **Install Dependencies**:
   ```bash
   pip install streamlit pandas plotly openpyxl
   ```

2. **Run the Dashboard**:
   ```bash
   streamlit run main.py
   ```

3. **Test Configuration**:
   ```bash
   python test_dashboard.py
   ```

## Navigation

The dashboard includes the following sections:

1. **Comprehensive Metrics** - New unified metrics across all media types
2. **Press Releases** - PR analysis and media coverage
3. **Social Media** - Social media trends and top posts
4. **Content Pillars** - Content categorization analysis
5. **Audience Affinity** - Audience targeting insights
6. **Ad Intelligence** - Detailed ad performance analysis

## Configuration

Key configuration files:
- `utils/config.py` - Brand definitions and colors
- `utils/date_utils.py` - Month selection logic
- `utils/file_io.py` - Data loading functions
- `sections/comprehensive_metrics.py` - Unified metrics implementation

## Brand Mapping

The dashboard includes comprehensive brand mapping to handle variations in brand names across different data sources. All brands are normalized to consistent display names for unified analysis and comparison.

## Updates from Original Dashboard

1. **✅ Updated data paths** to use `dashboard_data` folder structure
2. **✅ Added month selector** that dynamically discovers available months
3. **✅ Added company cluster selector** at the top like in `dashboard_example.py`
4. **✅ Extended creativity, reach, and brand strength metrics** to social media and PR sections
5. **✅ Unified brand name handling** across different media types
6. **✅ Created comprehensive metrics section** with tabs for each media type

The dashboard now provides a unified view of performance across all media types while maintaining the detailed analysis capabilities of the original sections.
