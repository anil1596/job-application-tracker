# Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.7 or higher
- A Google account
- Your resume in PDF format

## Step 1: Install Dependencies

```bash
# Option A: Use the setup script (recommended)
./setup.sh

# Option B: Manual installation
pip install -r requirements.txt
```

## Step 2: Set Up Google Sheets API

### 2.1 Enable API and Create Service Account

1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable these APIs:
   - Google Sheets API
   - Google Drive API
4. Go to "IAM & Admin" > "Service Accounts"
5. Click "Create Service Account"
6. Name: `job-tracker`
7. Role: `Editor`
8. Click "Done"

### 2.2 Download Credentials

1. Click on the service account you created
2. Go to "Keys" tab
3. Click "Add Key" > "Create New Key"
4. Choose JSON
5. Download and save as `credentials.json` in this folder

## Step 3: Create Google Sheet

1. Go to https://sheets.google.com
2. Create a new blank spreadsheet
3. Name it "Job Applications"
4. Click "Share" button
5. Add the service account email (from credentials.json, looks like: `job-tracker@project-id.iam.gserviceaccount.com`)
6. Give "Editor" permissions
7. Copy the spreadsheet URL

## Step 4: Add Your Resume

Place your resume as `Resume.pdf` in this folder.

## Step 5: Test It!

Try analyzing a single job:

```bash
python main.py \
  --sheet "https://docs.google.com/spreadsheets/d/YOUR_ID/edit" \
  --url "https://www.linkedin.com/jobs/view/12345/"
```

If successful, you'll see:
- Match score
- Recommendation
- Matched/missing skills
- Data added to your Google Sheet

## Daily Workflow

### Method 1: Analyze Jobs from Sheet (Recommended)

1. Browse job sites manually and copy interesting job URLs
2. Paste URLs into your Google Sheet (Job URL column)
3. Run:
   ```bash
   python main.py --sheet "YOUR_SHEET_URL" --analyze
   ```
4. Review results in spreadsheet
5. Apply manually to top matches

### Method 2: Analyze Individual Jobs

```bash
python main.py --sheet "YOUR_SHEET_URL" --url "JOB_URL"
```

## Automation (Optional)

### Run automatically at 6 AM and 4 PM:

```bash
python scheduler.py --sheet "YOUR_SHEET_URL"
```

Keep this running in the background (or use screen/tmux on Linux/Mac, or run as a service).

## Troubleshooting

### "Resume not found"
- Ensure `Resume.pdf` is in this folder
- Or use `--resume path/to/resume.pdf`

### "Credentials not found"
- Ensure `credentials.json` is in this folder
- Check you downloaded it correctly from Google Cloud

### "Permission denied" on Google Sheets
- Make sure you shared the sheet with the service account email
- Give "Editor" permissions

### "Failed to fetch job"
- Some sites block scraping - this is expected
- Try a different job URL
- The tool works best with publicly accessible job boards

## What's Next?

- Read [README.md](README.md) for full documentation
- Customize match threshold: `--threshold 60`
- Generate reports: `python main.py --sheet "URL" --report`
- Test individual components:
  - `python resume_parser.py Resume.pdf`
  - `python job_fetcher.py "JOB_URL"`

## Common Commands

```bash
# Analyze new jobs in spreadsheet
python main.py --sheet "URL" --analyze

# Analyze a specific job
python main.py --sheet "URL" --url "JOB_URL"

# Reanalyze everything
python main.py --sheet "URL" --analyze-all

# Generate report
python main.py --sheet "URL" --report

# Run scheduler (6 AM & 4 PM daily)
python scheduler.py --sheet "URL"
```

## Tips

1. **Start small**: Test with 2-3 job URLs first
2. **Check your sheet**: Review the analysis results
3. **Adjust threshold**: Try different `--threshold` values (default: 50)
4. **Focus on quality**: Use the tool to prioritize, not replace, thoughtful applications
5. **Update status**: Mark jobs as "Applied", "Rejected", etc. in the Status column

Happy job hunting! 🎯
