# Monthly Dashboard Analysis System

A comprehensive system for analyzing ads, PR, and social media content on a monthly basis with advanced insights and analyses.

---

# Step-by-Step Dashboard Update Process for Colleagues

## Prerequisites
- Python environment with required packages installed
- OpenAI API key configured in `.env` file
- Access to the dashboard repository

## Step 1: Prepare New Data Files

### 1.1 Copy Master Files for Ads and Social Media
1. **Ads Master File**: Copy the ads master file from `Ads Tracking\Akropolis_Ad_Updates\data` to `new_data/ads/ads_master_file.xlsx`
2. **Social Media Master File**: Copy the Facebook master file from `Social Media Tracking\data` to `new_data/social_media/facebook_master_file.xlsx`

### 1.2 Prepare PR Agility Data
1. Copy all individual agility files for the new month to `new_data/agility/` folder
2. Ensure each file follows the naming convention: `[Company]_compos_analysis.xlsx`
3. Verify all agility files are present for the brands you want to analyze

## Step 2: Update Configuration

1. Open `config.py` in the root directory
2. Update the analysis month:
   ```python
   ANALYSIS_YEAR = 2025
   ANALYSIS_MONTH = 10  # Change to the month you want to analyze
   ```

3. Configure which analyses to run by setting values to `True` in `ANALYSIS_CONTROL`:
   ```python
   ANALYSIS_CONTROL = {
       # Ads Analyses
       "ads_compos": True,           # Set to True if you want ads analysis
       "ads_creativity": True,       # Set to True if you want ads analysis
       "ads_key_advantages": True,   # Set to True if you want ads analysis
       
       # Social Media Analyses
       "social_media_compos": True,
       "social_media_creativity": True,
       "social_media_content_pillars": True,
       "social_media_audience_affinity": True,
       
       # PR Analyses
       "pr_compos": True,            # Set to True if you want PR analysis
       "pr_creativity": True,        # Set to True if you want PR analysis
       "pr_agility": True,           # MUST be True for PR - creates master file
   }
   ```

## Step 3: Run the Analysis

1. Open terminal/command prompt in the dashboard root directory
2. Run the analysis with cache clearing:
   ```bash
   python run_analysis_clean.py
   ```

## Step 4: Verify Results

1. Check that the new month folder was created: `dashboard_data/2025-10/`
2. Verify all enabled analyses completed successfully by checking the console output
3. Check the analysis output files in their respective folders:
   - `dashboard_data/2025-10/ads/analysis/` (if ads analyses were enabled)
   - `dashboard_data/2025-10/social_media/analysis/` (if social media analyses were enabled)
   - `dashboard_data/2025-10/pr/analysis/` (if PR analyses were enabled)

## Step 5: Update Dashboard

1. Navigate to the `dashboard/` folder
2. Run the main dashboard:
   ```bash
   python main.py
   ```
3. The dashboard should now include October data in the analysis results

## Important Notes:

### Analysis Execution Order
The analyses run in this specific order (this is handled automatically):
1. **PR Agility** (if enabled) - Creates the master PR file first
2. **CompOS Analysis** - For each enabled media type
3. **Creativity Analysis** - For each enabled media type
4. **Key Advantages Analysis** - For each enabled media type
5. **Content Pillars Analysis** - For social media only
6. **Audience Affinity Analysis** - For social media only

### Folder Structure
The system automatically creates this folder structure for the new month:
```
dashboard_data/2025-10/
├── ads/
│   └── analysis/
│       ├── compos/
│       ├── creativity/
│       └── key_advantages/
├── social_media/
│   └── analysis/
│       ├── compos/
│       ├── creativity/
│       ├── content_pillars/
│       └── audience_affinity/
└── pr/
    ├── pr_master_data.xlsx  (created by agility analysis)
    └── analysis/
        ├── compos/
        └── creativity/
```

### Troubleshooting
- If you get API rate limit errors, reduce `MAX_WORKERS` in `config.py` from 20 to 5 or 3
- If analyses fail, check the console output for specific error messages
- Ensure all required data files are in the correct locations before running
- The system will show which analyses are enabled and which data was processed

### Next Month Update
To update for November (or any future month), simply:
1. Repeat Steps 1.1 and 1.2 with new data
2. Change `ANALYSIS_MONTH = 11` in `config.py`
3. Run `python run_analysis_clean.py`

The system will automatically create the new month folder and process the data accordingly.

**Note**: Always use `run_analysis_clean.py` instead of `run_analysis.py` as it clears the Python cache first, ensuring you're running with the latest code changes and avoiding any potential cache-related issues.

---

## Quick Setup

### 1. Install Dependencies
```bash
pip install pandas openai tqdm tenacity openpyxl xlsxwriter python-dotenv
```

### 2. Set OpenAI API Key
Create a `.env` file in the root directory:
```
OPENAI_API_KEY=your_openai_api_key_here
```