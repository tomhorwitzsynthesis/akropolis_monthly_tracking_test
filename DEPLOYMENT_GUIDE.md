# Monthly Dashboard - GitHub Deployment Guide

## What to Upload to GitHub

### ✅ **INCLUDE** (Essential files):
```
📁 Your GitHub Repository/
├── 📁 dashboard/
│   ├── 📄 main.py                    # Main Streamlit app
│   ├── 📄 requirements.txt           # Python dependencies
│   ├── 📁 sections/                  # All dashboard sections
│   │   ├── 📄 pr_ranking_metrics.py
│   │   ├── 📄 social_media_ranking_metrics.py
│   │   ├── 📄 compos_matrix.py
│   │   ├── 📄 media_coverage.py
│   │   └── ... (all other .py files)
│   └── 📁 utils/                     # Utility functions
│       ├── 📄 config.py
│       ├── 📄 date_utils.py
│       └── 📄 file_io.py
├── 📄 config.py                      # Main config file
├── 📄 README.md                      # Project documentation
└── 📄 .gitignore                     # Ignore sensitive files
```

### ❌ **EXCLUDE** (Don't upload):
```
❌ dashboard_data/                     # Your actual data (too large + sensitive)
❌ new_data/                          # Raw data files
❌ analysis/                          # Analysis scripts
❌ __pycache__/                       # Python cache files
❌ *.pyc                             # Compiled Python files
❌ test_*.py                          # Test files
❌ debug_*.py                         # Debug files
❌ run_analysis*.py                   # Analysis runner scripts
```

## Path Handling for Streamlit Cloud

### ✅ **Current BASE_DIR will work perfectly!**

Your current setup:
```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DATA_DIR = os.path.join(BASE_DIR, "dashboard_data")
```

**This will work on Streamlit Cloud because:**
- `os.path.abspath(__file__)` gets the absolute path of `config.py`
- `os.path.dirname()` gets the directory containing `config.py`
- When you put everything in a GitHub folder, the relative paths remain the same

### Example Structure on Streamlit Cloud:
```
📁 Your GitHub Repository/
├── 📄 config.py                      # BASE_DIR points here
├── 📁 dashboard/
│   ├── 📄 main.py
│   └── 📁 utils/
└── 📁 dashboard_data/                # DASHBOARD_DATA_DIR will find this
    ├── 📁 2025-08/
    └── 📁 2025-09/
```

## Steps to Deploy:

### 1. Create .gitignore file:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
new_data/
analysis/
test_*.py
debug_*.py
run_analysis*.py
*.log
```

### 2. Upload to GitHub:
- Create a new repository
- Upload only the files marked with ✅ above
- Make sure `dashboard/main.py` is the entry point

### 3. Deploy on Streamlit Cloud:
- Go to [share.streamlit.io](https://share.streamlit.io)
- Connect your GitHub repository
- Set **Main file path**: `dashboard/main.py`
- Set **Branch**: `main` (or your default branch)

### 4. Data Considerations:

**Option A: Include sample data (recommended for demo)**
- Upload a small sample of `dashboard_data/` with 1-2 months
- This allows the app to run immediately

**Option B: Connect to external data source**
- Modify `file_io.py` to load from Google Drive, AWS S3, etc.
- More complex but handles large datasets

**Option C: Streamlit Secrets (for sensitive data)**
- Store data credentials in Streamlit Secrets
- Load data dynamically from external sources

## Important Notes:

1. **File Size Limits**: GitHub has a 100MB file limit, Streamlit Cloud has similar limits
2. **Data Privacy**: Don't upload sensitive business data to public repositories
3. **Dependencies**: Make sure `requirements.txt` includes all needed packages
4. **Environment**: Streamlit Cloud runs on Python 3.11

## Quick Start Commands:

```bash
# Create .gitignore
echo "__pycache__/
*.pyc
new_data/
analysis/
test_*.py
debug_*.py" > .gitignore

# Initialize git repo
git init
git add .
git commit -m "Initial commit: Monthly Dashboard"
git remote add origin https://github.com/yourusername/your-repo.git
git push -u origin main
```

Your current path setup will work perfectly on Streamlit Cloud! 🚀
