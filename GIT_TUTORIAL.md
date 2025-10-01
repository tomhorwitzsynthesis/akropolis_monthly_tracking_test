# Git Tutorial for Beginners - Upload Your Dashboard to GitHub

## What is Git?
Git is like a "save system" for your code that also lets you share it online. Think of it like Google Drive, but specifically for code.

## Step-by-Step Guide

### 1. Install Git (if you don't have it)
- Go to [git-scm.com](https://git-scm.com/downloads)
- Download and install (just click "Next" through everything)
- Open Command Prompt/PowerShell and type: `git --version`
- If it shows a version number, you're good to go!

### 2. Create a GitHub Account
- Go to [github.com](https://github.com)
- Sign up (it's free)
- Verify your email

### 3. Create a New Repository on GitHub
- Click the green "New" button (or go to github.com/new)
- Repository name: `monthly-dashboard` (or whatever you want)
- Description: `Monthly Dashboard for Akropolis`
- Make it **Public** (so Streamlit can access it)
- **DON'T** check "Add a README file" (we already have files)
- Click "Create repository"

### 4. Upload Your Code Using Git

**Open Command Prompt/PowerShell in your project folder:**
- Press `Windows + R`
- Type `cmd` and press Enter
- Navigate to your project: `cd "C:\Users\thoma\Documents\Projects\Akropolis\Tracking\Tracking\Monthly Dashboard"`

**Run these commands one by one:**

```bash
# Initialize git in your folder
git init

# Add all your files (except the ones in .gitignore)
git add .

# Create your first "save point" (called a commit)
git commit -m "Initial commit: Monthly Dashboard"

# Connect to your GitHub repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/monthly-dashboard.git

# Upload everything to GitHub
git push -u origin main
```

### 5. What Each Command Does:
- `git init` - Sets up git in your folder
- `git add .` - Prepares all files for upload (respects .gitignore)
- `git commit -m "message"` - Creates a "save point" with a message
- `git remote add origin URL` - Connects your folder to GitHub
- `git push -u origin main` - Uploads everything to GitHub

### 6. If You Get Authentication Errors:
GitHub now requires a "Personal Access Token" instead of your password:

1. Go to GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name like "Dashboard Upload"
4. Check "repo" permission
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)
7. When git asks for password, paste the token instead

### 7. Future Updates:
When you make changes to your code:

```bash
# Add your changes
git add .

# Create a new save point
git commit -m "Fixed creativity metrics"

# Upload the changes
git push
```

## Why Git is Better Than Manual Upload:

✅ **Automatic**: Uploads only changed files  
✅ **Version Control**: Keeps history of all changes  
✅ **Easy Updates**: Just run 3 commands to update  
✅ **Professional**: Standard way developers share code  
✅ **Backup**: Your code is safely stored on GitHub  

## Troubleshooting:

**"git is not recognized"** → Install Git from git-scm.com

**"Permission denied"** → Use Personal Access Token (see step 6)

**"Repository not found"** → Check the URL in step 4, make sure repository exists

**"Everything up-to-date"** → Your code is already uploaded!

## Next Steps After Upload:

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your repository
4. Set Main file path: `dashboard/main.py`
5. Click "Deploy"

That's it! Your dashboard will be live on the internet! 🚀

## Quick Reference Card:

```bash
# First time setup (run once)
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main

# Future updates (run whenever you make changes)
git add .
git commit -m "Description of changes"
git push
```

**Pro tip**: You can copy-paste these commands directly into your terminal!
