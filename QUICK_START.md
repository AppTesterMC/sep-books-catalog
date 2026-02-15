# 🚀 Quick Start Guide - SEP Books Catalog

## What You're Getting

A complete GitHub repository that:
- ✅ Automatically scrapes book data from sep.gr daily
- ✅ Displays books in a beautiful, searchable website
- ✅ Hosts for free on GitHub Pages
- ✅ Updates itself without any manual work

## 5-Minute Deployment Steps

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Name your repository: `sep-books-catalog` (or any name you prefer)
3. Make it **Public** (required for free GitHub Pages)
4. **Don't** initialize with README, .gitignore, or license (we already have these)
5. Click **Create repository**

### Step 2: Upload Your Files

**Option A - Using Git (Recommended)**

```bash
# Navigate to the folder you downloaded
cd sep-books-catalog

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit"

# Add your GitHub repository as remote (replace YOUR-USERNAME)
git remote add origin https://github.com/YOUR-USERNAME/sep-books-catalog.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Option B - Using GitHub Web Interface**

1. Open your new repository on GitHub
2. Click **uploading an existing file**
3. Drag and drop ALL the files from the `sep-books-catalog` folder
4. Click **Commit changes**

### Step 3: Enable GitHub Pages

1. In your repository, go to **Settings** (top menu)
2. Click **Pages** in the left sidebar
3. Under **Source**:
   - Branch: Select `main`
   - Folder: Select `/ (root)`
4. Click **Save**
5. Wait 1-2 minutes, then refresh. You'll see your site URL!

### Step 4: Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. Click **"I understand my workflows, go ahead and enable them"**
3. Click **"Scrape Books Data"** workflow
4. Click **"Run workflow"** → **"Run workflow"** (green button)

This will:
- Run the scraper immediately
- Commit the real book data
- Update your website

### Step 5: Done! 🎉

Your website is now live at:
```
https://YOUR-USERNAME.github.io/sep-books-catalog/
```

The scraper will run automatically every day at 3 AM UTC to keep your catalog updated.

## Customization Tips

### Change the Color Scheme

Edit `style.css` lines 1-9:

```css
:root {
    --primary-bg: #faf8f5;        /* Background color */
    --accent-color: #8b4513;       /* Main accent color */
    --text-primary: #2c2418;       /* Main text color */
}
```

### Change the Scrape Schedule

Edit `.github/workflows/scrape.yml` line 6:

```yaml
- cron: '0 3 * * *'  # Current: Daily at 3 AM UTC
- cron: '0 */6 * * *'  # Example: Every 6 hours
- cron: '0 0 * * 0'    # Example: Weekly on Sundays
```

Use https://crontab.guru/ to create your schedule.

### Add More Categories

Edit `scraper.py` line 188 to add more URL paths:

```python
thislist = [
    "biblia-poy-diathetei-h-se",
    "vivlia-allon-ekdoton",
    # Add more categories here
]
```

## Troubleshooting

### Website Shows "No Data"
- Wait 2-3 minutes after running the workflow
- Check the Actions tab for errors
- Make sure `data/latest.csv` exists in your repo

### Actions Not Running
- Go to Settings → Actions → General
- Ensure "Allow all actions" is selected
- Check if Actions are enabled for your account

### Site Not Updating
- Check the Actions tab for workflow runs
- Verify the workflow succeeded (green checkmark)
- Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)

## Need Help?

- Check the full README.md in the repository
- Review GitHub Actions logs in the Actions tab
- Ensure all files were uploaded correctly

---

Enjoy your automated book catalog! 📚
