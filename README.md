# Monthly Dashboard Analysis System

A comprehensive system for analyzing ads, PR, and social media content on a monthly basis with advanced insights and analyses.

## Overview

This system processes monthly data from different media sources and runs three main types of analysis:
- **CompOS Analysis**: Archetype assignment for content positioning
- **Creativity Analysis**: Originality and creativity ranking across brands
- **Key Advantages**: Extraction of key benefits and advantages from content

## Folder Structure

```
Monthly Dashboard/
├── config.py                          # Configuration settings
├── monthly_analysis_runner.py         # Main analysis runner
├── run_monthly_analysis.py           # Interactive analysis script
├── new_data/                         # New data to be analyzed
│   ├── ads/
│   │   └── ads_master_file.xlsx
│   ├── social_media/
│   │   └── facebook_master_file.xlsx
│   └── pr/
│       └── pr_master_file.xlsx
├── dashboard_data/                   # Processed monthly data
│   └── 2025-01/                     # Monthly folders (YYYY-MM format)
│       ├── ads/
│       ├── social_media/
│       ├── pr/
│       └── analysis/
│           ├── compos/
│           ├── creativity/
│           └── key_advantages/
├── analysis/                         # Analysis modules
│   ├── compos_analysis.py
│   ├── creativity_analysis.py
│   └── key_advantages.py
└── utils/                           # Utility functions
    ├── folder_manager.py
    └── data_processor.py
```

## Setup

1. **Install Dependencies**:
   ```bash
   pip install pandas openai tqdm tenacity openpyxl xlsxwriter
   ```

2. **Set OpenAI API Key**:
   Create a `.env` file in the root directory:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Prepare Data**:
   - Place your ads data in `new_data/ads/ads_master_file.xlsx`
   - Place your social media data in `new_data/social_media/facebook_master_file.xlsx`
   - Place your PR data in `new_data/pr/pr_master_file.xlsx`

## Usage

### Simple Mode (Recommended)

1. **Set the month and enable analyses in config.py**:
   ```python
   # In config.py
   ANALYSIS_YEAR = 2025
   ANALYSIS_MONTH = 1  # Change this to the month you want to analyze
   
   # Enable/disable specific analyses
   ANALYSIS_CONTROL = {
       # Ads Analyses
       "ads_compos": True,
       "ads_creativity": True, 
       "ads_key_advantages": True,
       
       # Social Media Analyses (currently disabled)
       "social_media_compos": False,
       "social_media_creativity": False,
       "social_media_content_pillars": False,
       "social_media_audience_affinity": False,
       
       # PR Analyses (currently disabled)
       "pr_creativity": False,
   }
   ```

2. **Run the analysis**:
   ```bash
   python run_analysis.py
   ```

This will automatically:
- Load data from `new_data/` folders
- Filter data to only include items from the specified month
- Run only the analyses marked as `True` in the config
- Save results in organized monthly folders

### Advanced Mode

For more control, use the full runner:

```bash
# Use configured month from config.py
python monthly_analysis_runner.py

# Override with specific month
python monthly_analysis_runner.py --year 2025 --month 1

# Analyze only specific media types
python monthly_analysis_runner.py --media-types ads --analysis-types compos creativity

# Skip data processing (only run analyses on existing data)
python monthly_analysis_runner.py --skip-data-processing

# Show summary of available data and analyses
python monthly_analysis_runner.py --summary
```

## Data Requirements

### Ads Data (`ads_master_file.xlsx`)
Required columns:
- `snapshot/body/text`: Ad content text
- `ad_details/advertiser/ad_library_page_info/page_info/page_name`: Brand name
- `ad_details/aaa_info/eu_total_reach`: Reach/impressions

Optional date columns (for month filtering):
- `startDateFormatted`, `endDateFormatted`: Ad run dates

### Social Media Data (`facebook_master_file.xlsx`)
Required columns:
- `post_text`: Post content
- `user_id`: Brand/company identifier
- `num_likes`: Engagement metric

Optional date columns (for month filtering):
- `created_at`, `published_date`: Post dates

### PR Data (`pr_master_file.xlsx`)
Required columns:
- `content`: Article content
- `company`: Company name
- `Impressions`: Reach metric

Optional date columns (for month filtering):
- `date`, `published_date`: Article dates

## Analysis Types

### 1. CompOS Analysis
- **Purpose**: Assigns archetypes to content for positioning analysis
- **Output**: Excel file with archetype assignments
- **Archetypes**: 16 different positioning archetypes (Futurist, Eco Warrior, etc.)
- **Requirements**: No minimum ad threshold

### 2. Creativity Analysis
- **Purpose**: Ranks content by originality and creativity
- **Process**: 
  1. Within-brand selection of most original content
  2. Cross-brand ranking by creativity
- **Output**: Excel file with creativity rankings and examples
- **Requirements**: Minimum 5 ads per brand (configurable via `MIN_ADS_FOR_ANALYSIS`)
- **Skipped Brands**: Companies with fewer ads are listed in "Skipped Brands" sheet

### 3. Key Advantages Analysis
- **Purpose**: Extracts key benefits and advantages from content
- **Output**: Excel file with categorized advantages and evidence
- **Requirements**: Minimum 5 ads per brand (configurable via `MIN_ADS_FOR_ANALYSIS`)
- **Skipped Companies**: Companies with fewer ads are listed in "Skipped Companies" sheet

## Monthly Data Management

- **New Data**: Place monthly data in `new_data/` folders
- **Dashboard Data**: Processed data is stored in `dashboard_data/YYYY-MM/` folders
- **Appending**: New monthly data is appended to existing dashboard data
- **Overwriting**: Analysis results can be overwritten when re-running analyses

## Configuration

Edit `config.py` to modify:

### Analysis Control
- `ANALYSIS_YEAR` and `ANALYSIS_MONTH`: Set which month to analyze
- `ANALYSIS_CONTROL`: Enable/disable specific analyses with True/False values

### Analysis Parameters
- `MAX_ADS_PER_BRAND`: Maximum number of ads per brand to analyze (default: 50)
- `TOP_K_PER_BRAND`: Number of top ads to select per brand (default: 10)
- `MAX_CHARS_PER_AD`: Maximum characters per ad for analysis (default: 1000)
- `MIN_ADS_FOR_ANALYSIS`: Minimum number of ads required for creativity/key advantages analysis (default: 5)

### Technical Settings
- OpenAI model settings
- Column mappings for different media types
- File paths and folder structure

## Error Handling

The system includes comprehensive error handling:
- Data validation before processing
- Graceful handling of API failures
- Detailed logging of all operations
- Backup creation for existing files

## Output Files

Analysis results are saved in the monthly analysis folders:
- `dashboard_data/YYYY-MM/analysis/compos/compos_analysis_[media_type].xlsx`
- `dashboard_data/YYYY-MM/analysis/creativity/creativity_analysis_[media_type].xlsx`
- `dashboard_data/YYYY-MM/analysis/key_advantages/key_advantages_[media_type].xlsx`

## Troubleshooting

1. **API Key Issues**: Ensure your OpenAI API key is set in the `.env` file
2. **Data Format Issues**: Check that your Excel files have the required columns
3. **Memory Issues**: Reduce `MAX_ITEMS_PER_BRAND` in config for large datasets
4. **Rate Limiting**: The system includes retry logic for API rate limits

## Future Enhancements

- Support for additional media types
- Custom analysis configurations
- Dashboard visualization integration
- Automated monthly scheduling
