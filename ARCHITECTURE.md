# Architecture & Workflow

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Job Application Tracker                     │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│   Resume     │        │  Job URLs    │        │  Google      │
│   (PDF)      │───────▶│  (Various    │───────▶│  Sheets      │
│              │        │   Sites)     │        │              │
└──────────────┘        └──────────────┘        └──────────────┘
       │                       │                        ▲
       │                       │                        │
       ▼                       ▼                        │
┌──────────────┐        ┌──────────────┐               │
│ Resume       │        │ Job          │               │
│ Parser       │        │ Fetcher      │               │
│              │        │              │               │
│ - Extract    │        │ - Fetch job  │               │
│   skills     │        │   description│               │
│ - Extract    │        │ - Parse HTML │               │
│   experience │        │ - Rate limit │               │
└──────────────┘        └──────────────┘               │
       │                       │                        │
       │                       │                        │
       └───────────┬───────────┘                        │
                   │                                    │
                   ▼                                    │
            ┌──────────────┐                           │
            │ Job          │                           │
            │ Matcher      │                           │
            │              │                           │
            │ - Skills     │───────────────────────────┘
            │   matching   │
            │ - Experience │
            │   matching   │
            │ - Calculate  │
            │   score      │
            └──────────────┘
```

## Component Details

### 1. Resume Parser (`resume_parser.py`)
**Input**: Resume PDF
**Output**: Structured data (skills, experience)

**Responsibilities**:
- Extract text from PDF
- Parse skills section
- Identify technical skills
- Calculate years of experience
- Extract relevant keywords

### 2. Job Fetcher (`job_fetcher.py`)
**Input**: Job URL
**Output**: Job data (title, company, description)

**Responsibilities**:
- Fetch job posting HTML
- Parse different job board formats (LinkedIn, Indeed, etc.)
- Extract job requirements
- Rate limiting (2 seconds between requests)
- Error handling for failed fetches

**Supported Platforms**:
- LinkedIn
- Indeed
- Greenhouse
- Lever
- Generic (fallback)

### 3. Job Matcher (`job_matcher.py`)
**Input**: Resume data + Job data
**Output**: Match score and recommendations

**Scoring Algorithm**:
```
Total Score = (Skills × 40%) + (Experience × 30%) +
              (Title × 20%) + (Keywords × 10%)
```

**Breakdown**:
- **Skills Match (40%)**: Overlap between resume skills and job requirements
- **Experience Match (30%)**: How well your experience fits the requirements
- **Title Relevance (20%)**: Job title matches your target roles
- **Keyword Match (10%)**: General keyword overlap

### 4. Sheets Integration (`sheets_integration.py`)
**Input**: Analysis results
**Output**: Updated Google Sheet

**Responsibilities**:
- Connect to Google Sheets API
- Read job URLs
- Write analysis results
- Update status
- Sort by date

### 5. Main Application (`main.py`)
**Orchestrator** that coordinates all components

**Modes**:
- Analyze single job (`--url`)
- Analyze new jobs (`--analyze`)
- Reanalyze all (`--analyze-all`)
- Generate report (`--report`)

### 6. Scheduler (`scheduler.py`)
**Optional**: Run automatically at 6 AM and 4 PM

## Data Flow

### Workflow 1: Single Job Analysis

```
User provides job URL
        │
        ▼
┌───────────────────┐
│ main.py           │
│ - Initialize      │
│ - Parse resume    │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ job_fetcher.py    │
│ - Fetch job page  │
│ - Extract data    │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ job_matcher.py    │
│ - Calculate match │
│ - Generate score  │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ sheets_integration│
│ - Add to sheet    │
│ - Update status   │
└───────────────────┘
        │
        ▼
    Results displayed
```

### Workflow 2: Batch Analysis

```
User adds URLs to Google Sheet
        │
        ▼
┌───────────────────┐
│ main.py           │
│ --analyze         │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ sheets_integration│
│ - Get URLs        │
│ - Filter new ones │
└───────────────────┘
        │
        ▼
    For each URL:
        │
        ▼
┌───────────────────┐
│ job_fetcher.py    │
│ - Fetch job       │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ job_matcher.py    │
│ - Calculate match │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ sheets_integration│
│ - Update row      │
└───────────────────┘
        │
        ▼
    Next URL...
        │
        ▼
    Sort sheet by date
```

## Rate Limiting & Ethics

### Rate Limiting Strategy
- **2 seconds** minimum between requests to same domain
- Tracks last request time per domain
- Prevents overwhelming servers

### Ethical Considerations
✅ **What we do**:
- Fetch publicly available job postings
- Parse content client-side
- Respect rate limits
- Provide analysis only
- User applies manually

❌ **What we DON'T do**:
- Auto-apply to jobs
- Bypass login walls
- Scrape aggressively
- Submit forms automatically
- Violate ToS

## Google Sheets Schema

```
Column A: Application Date     (auto-generated)
Column B: Job URL               (user input)
Column C: Job Title             (extracted)
Column D: Company               (extracted)
Column E: Platform              (detected)
Column F: Match Score           (calculated)
Column G: Recommendation        (generated)
Column H: Matched Skills        (calculated)
Column I: Missing Skills        (calculated)
Column J: Experience Required   (extracted)
Column K: Your Experience       (from resume)
Column L: Status                (user/system)
Column M: Notes                 (user input)
```

## Error Handling

### Graceful Degradation
1. **Failed fetch**: Log error, skip job, continue
2. **Parse error**: Use generic parser, extract what's possible
3. **Sheets API error**: Retry once, then log error
4. **Missing resume**: Exit with clear error message

### Logging Levels
- **INFO**: Normal operations
- **WARNING**: Non-critical issues (failed fetch, etc.)
- **ERROR**: Critical issues that prevent operation

## Performance Considerations

### Speed
- Single job: ~3-5 seconds
- Batch (10 jobs): ~30-60 seconds (due to rate limiting)
- Batch (100 jobs): ~5-10 minutes

### Optimization Tips
1. Process in batches of 10-20 jobs
2. Run during off-peak hours
3. Use `--analyze` (new only) vs `--analyze-all`
4. Review highly-recommended jobs first

## Extension Points

### Easy to Customize

1. **Add new skills**: Edit `COMMON_SKILLS` in `resume_parser.py`
2. **Adjust scoring weights**: Modify weights in `job_matcher.py`
3. **Support new job board**: Add parser to `job_fetcher.py`
4. **Change schedule**: Modify times in `scheduler.py`
5. **Custom recommendations**: Update `_get_recommendation()` in `job_matcher.py`

## Security

### Credentials Storage
- `credentials.json` stored locally only
- Never committed to git (.gitignore)
- Service account has minimal permissions
- Only accesses your specific spreadsheet

### Data Privacy
- All processing happens locally
- Resume never leaves your machine
- No third-party API calls
- Google Sheets encrypted by Google

## Testing

### Test Individual Components

```bash
# Test resume parser
python resume_parser.py Resume.pdf

# Test job fetcher
python job_fetcher.py "https://job-url"

# Test sheets connection
python sheets_integration.py credentials.json "sheet-url"
```

### Integration Test

```bash
# Test full workflow
python main.py --sheet "URL" --url "https://job-url"
```

## Monitoring

### Log Files (when using scheduler)
```bash
# Create logs directory
mkdir logs

# Run with logging
python scheduler.py --sheet "URL" 2>&1 | tee logs/scheduler.log
```

### Check Status
```bash
# View recent logs
tail -f logs/scheduler.log

# Count successful analyses
grep "Analysis completed successfully" logs/scheduler.log | wc -l
```

## Future Enhancements (Ideas)

- [ ] Email notifications for high-match jobs
- [ ] Machine learning to improve scoring
- [ ] Browser extension for one-click analysis
- [ ] Cover letter template generator
- [ ] Application deadline tracking
- [ ] Interview status tracking
- [ ] Salary data integration
- [ ] Company research integration

---

This architecture is designed to be:
- **Ethical**: Respects websites and users
- **Maintainable**: Clear separation of concerns
- **Extensible**: Easy to add features
- **Reliable**: Robust error handling
- **Efficient**: Rate-limited but effective
