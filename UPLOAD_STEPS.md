# Step-by-Step Upload Instructions

## Your Repository
https://github.com/tomhorwitzsynthesis/akropolis_monthly_tracking_test

## Commands to Run

### 1. Open Command Prompt/PowerShell
- Press `Windows + R`
- Type `cmd` and press Enter
- Navigate to your project folder:
```bash
cd "C:\Users\thoma\Documents\Projects\Akropolis\Tracking\Tracking\Monthly Dashboard"
```

### 2. Initialize Git and Upload (Copy-Paste These Commands One by One)

```bash
git init
```

```bash
git add .
```

```bash
git commit -m "Initial commit: Monthly Dashboard with PR and Social Media metrics"
```

```bash
git remote add origin https://github.com/tomhorwitzsynthesis/akropolis_monthly_tracking_test.git
```

```bash
git branch -M main
```

```bash
git push -u origin main
```

### 3. Authentication
When prompted for username and password:
- **Username**: `tomhorwitzsynthesis`
- **Password**: Use a Personal Access Token (not your GitHub password)

#### To get Personal Access Token:
1. Go to GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Name: "Dashboard Upload"
4. Check "repo" permission
5. Click "Generate token"
6. Copy the token (you won't see it again!)
7. Use this token as your password when git asks

### 4. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Repository: `tomhorwitzsynthesis/akropolis_monthly_tracking_test`
4. Branch: `main`
5. Main file path: `dashboard/main.py`
6. Click "Deploy"

## What Each Command Does:
- `git init` - Sets up git in your folder
- `git add .` - Prepares all files (respects .gitignore)
- `git commit -m "message"` - Creates save point
- `git remote add origin URL` - Connects to your GitHub repo
- `git branch -M main` - Sets main branch name
- `git push -u origin main` - Uploads everything

## Troubleshooting:
- **"git not found"** → Install Git from git-scm.com
- **"Permission denied"** → Use Personal Access Token as password
- **"Repository not found"** → Check the URL is correct

## Future Updates:
When you make changes:
```bash
git add .
git commit -m "Description of changes"
git push
```

Your dashboard will be live at: `https://tomhorwitzsynthesis-akropolis-monthly-tracking-test-main-xxxxxx.streamlit.app`
