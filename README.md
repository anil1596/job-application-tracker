# Job Application Tracker & Analyzer

An ethical, legitimate tool that helps you work smarter in your job search by analyzing job postings against your resume and tracking applications in Google Sheets.

## Features

- **Resume Parser**: Extracts skills and experience from your PDF resume
- **Job Description Fetcher**: Fetches job descriptions from various job boards (LinkedIn, Indeed, Greenhouse, Lever, etc.)
- **Smart Matching Algorithm**: Scores jobs based on:
  - Skills match (40% weight)
  - Experience requirements (30% weight)
  - Title relevance (20% weight)
  - Keyword match (10% weight)
- **Google Sheets Integration**: Automatically tracks analyzed jobs in a spreadsheet
- **Recommendations**: Provides clear recommendations on which jobs to prioritize
- **Rate Limiting**: Respects website policies with built-in rate limiting

## What This Tool Does (Ethically)

✅ **DOES:**
- Parse your resume to extract skills
- Fetch publicly available job descriptions
- Calculate match scores
- Help you prioritize which jobs to apply to manually
- Track your applications in Google Sheets
- Provide insights on skills gaps

❌ **DOES NOT:**
- Automatically apply to jobs (you apply manually)
- Violate any terms of service
- Use bots or automation to interact with job sites
- Submit applications on your behalf
- Scrape data aggressively

## Installation

### 1. Clone or Download

```bash
cd /path/to/autoApply
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable Google Sheets API and Google Drive API
4. Create a Service Account:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Name it (e.g., "job-tracker")
   - Grant it "Editor" role
   - Click "Done"
5. Create credentials:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" > "Create New Key"
   - Choose JSON format
   - Download the JSON file
   - Save it as `credentials.json` in this directory

### 4. Create Google Spreadsheet

1. Create a new Google Sheet
2. Share it with the service account email (found in credentials.json)
   - Give "Editor" permissions
3. Copy the spreadsheet URL

### 5. Add Your Resume

Place your resume PDF as `Resume.pdf` in this directory (or specify a different path when running).

## Usage

### Analyze a Single Job

```bash
python main.py --sheet "YOUR_SPREADSHEET_URL" --url "JOB_POSTING_URL"
```

Example:
```bash
python main.py --sheet "https://docs.google.com/spreadsheets/d/abc123/edit" --url "https://www.linkedin.com/jobs/view/123456789"
```

### Analyze All New Jobs from Spreadsheet

First, manually add job URLs to your spreadsheet (in the "Job URL" column), then:

```bash
python main.py --sheet "YOUR_SPREADSHEET_URL" --analyze
```

### Reanalyze All Jobs

```bash
python main.py --sheet "YOUR_SPREADSHEET_URL" --analyze-all
```

### Generate Report

```bash
python main.py --sheet "YOUR_SPREADSHEET_URL" --report
```

### Custom Options

```bash
python main.py \
  --sheet "YOUR_SPREADSHEET_URL" \
  --resume "path/to/resume.pdf" \
  --credentials "path/to/credentials.json" \
  --threshold 60.0 \
  --analyze
```

Options:
- `--resume`: Path to resume PDF (default: Resume.pdf)
- `--credentials`: Path to Google credentials JSON (default: credentials.json)
- `--sheet`: Google Sheets URL (required)
- `--threshold`: Minimum match score (default: 50.0)
- `--analyze`: Analyze unprocessed jobs
- `--analyze-all`: Reanalyze all jobs
- `--url`: Analyze single job URL
- `--report`: Generate summary report

## Scheduling (Optional)

To run automatically at 6 AM and 4 PM daily:

### On macOS/Linux (cron)

1. Open crontab:
```bash
crontab -e
```

2. Add this line (replace paths):
```bash
0 6,16 * * * cd /Users/yourname/autoApply && /usr/bin/python3 main.py --sheet "YOUR_SPREADSHEET_URL" --analyze >> logs/tracker.log 2>&1
```

3. Create logs directory:
```bash
mkdir logs
```

### On Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 6:00 AM
4. Action: Start a program
   - Program: `python`
   - Arguments: `main.py --sheet "YOUR_SPREADSHEET_URL" --analyze`
   - Start in: `C:\path\to\autoApply`
5. Repeat for 4:00 PM

## Workflow

### Recommended Daily Workflow

1. **Manually browse job boards** (LinkedIn, Indeed, etc.) and copy URLs of interesting jobs
2. **Paste URLs** into your Google Sheet in the "Job URL" column
3. **Run the analyzer**:
   ```bash
   python main.py --sheet "YOUR_SHEET_URL" --analyze
   ```
4. **Review results** in the spreadsheet:
   - Jobs are scored 0-100
   - Sorted by date (newest first)
   - See matched/missing skills
   - Get clear recommendations
5. **Prioritize applications**:
   - Focus on "HIGHLY RECOMMENDED" jobs first
   - Review "RECOMMENDED" jobs
   - Consider "CONSIDER" jobs if they interest you
6. **Apply manually** to the jobs you select
7. **Update status** in the spreadsheet as you apply

### Alternative: Single Job Analysis

For quick checks:
```bash
python main.py --sheet "YOUR_SHEET_URL" --url "https://job-posting-url"
```

## Google Sheet Columns

The tool maintains these columns:

| Column | Description |
|--------|-------------|
| Application Date | When the job was analyzed |
| Job URL | Link to job posting |
| Job Title | Position title |
| Company | Company name |
| Platform | Job board (LinkedIn, Indeed, etc.) |
| Match Score | Your match score (0-100%) |
| Recommendation | Application recommendation |
| Matched Skills | Skills you have that match |
| Missing Skills | Skills mentioned that you lack |
| Experience Required | Years required |
| Your Experience | Your years of experience |
| Status | Analyzed, Applied, Rejected, etc. |
| Notes | Your personal notes |

## Understanding Match Scores

- **80-100%**: HIGHLY RECOMMENDED - Strong match, apply immediately
- **65-79%**: RECOMMENDED - Good match, apply if interested
- **50-64%**: CONSIDER - Moderate match, review carefully
- **35-49%**: LOW PRIORITY - Weak match, only if very interested
- **0-34%**: NOT RECOMMENDED - Poor match, likely skip

## Troubleshooting

### "Failed to fetch job description"

- Some sites have anti-scraping measures
- Try accessing the URL manually first
- The tool respects rate limits - wait and retry
- Some job boards require login (tool cannot access those)

### "Error connecting to Google Sheets"

- Verify credentials.json is in the directory
- Check that the service account email has access to the sheet
- Ensure Google Sheets API is enabled in your project

### "No skills found in resume"

- Ensure resume is a readable PDF (not scanned image)
- Check that skills are listed clearly in resume
- The parser looks for common technical terms

## Testing Individual Components

### Test Resume Parser
```bash
python resume_parser.py Resume.pdf
```

### Test Job Fetcher
```bash
python job_fetcher.py "JOB_URL"
```

### Test Sheets Connection
```bash
python sheets_integration.py credentials.json "SPREADSHEET_URL"
```

## Limitations

- Only works with publicly accessible job postings
- Cannot access jobs behind login walls
- Parsing accuracy depends on job posting structure
- Some job boards may block automated access
- Match scores are estimates - use your judgment

## Privacy & Security

- Your resume data stays local
- Google Sheets data is only accessible to you and your service account
- No data is sent to third parties
- Credentials are stored locally
- Rate limiting prevents aggressive scraping

## Contributing

This is a personal tool, but suggestions are welcome! Keep all modifications ethical and legal.

## License

MIT License - Use responsibly and ethically.

## Disclaimer

This tool is for personal use only. Always:
- Respect websites' terms of service
- Apply to jobs manually with genuine interest
- Customize applications for each position
- Use the tool as a helper, not a replacement for thoughtful job searching

**This tool does not automatically apply to jobs. You must review and apply manually to each position.**

---

Good luck with your job search! 🎯
