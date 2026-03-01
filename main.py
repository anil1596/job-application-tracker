#!/usr/bin/env python3
"""
Job Application Tracker & Analyzer
Main application that orchestrates job analysis and tracking
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
import time

from resume_parser import parse_resume
from job_fetcher import JobFetcher
from job_matcher import JobMatcher
from sheets_integration import SheetsManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JobApplicationTracker:
    """Main application orchestrator"""

    def __init__(
        self,
        resume_path: str,
        credentials_path: str,
        spreadsheet_url: str,
        match_threshold: float = 50.0
    ):
        """
        Initialize the tracker

        Args:
            resume_path: Path to resume PDF
            credentials_path: Path to Google credentials JSON
            spreadsheet_url: Google Sheets URL
            match_threshold: Minimum match score to recommend (0-100)
        """
        self.resume_path = resume_path
        self.credentials_path = credentials_path
        self.spreadsheet_url = spreadsheet_url
        self.match_threshold = match_threshold

        # Components
        self.resume_data = None
        self.job_fetcher = None
        self.job_matcher = None
        self.sheets_manager = None

    def initialize(self):
        """Initialize all components"""
        logger.info("Initializing Job Application Tracker...")

        # Parse resume
        logger.info(f"Parsing resume from: {self.resume_path}")
        self.resume_data = parse_resume(self.resume_path)
        logger.info(f"Found {len(self.resume_data['skills'])} skills in resume")
        logger.info(f"Detected {self.resume_data['years_of_experience']} years of experience")

        # Initialize job fetcher
        self.job_fetcher = JobFetcher(rate_limit_seconds=2.0)

        # Initialize job matcher
        self.job_matcher = JobMatcher(self.resume_data)

        # Initialize sheets manager
        logger.info("Connecting to Google Sheets...")
        self.sheets_manager = SheetsManager(self.credentials_path, self.spreadsheet_url)
        self.sheets_manager.connect()

        logger.info("Initialization complete!")

    def analyze_jobs(self, process_all: bool = False):
        """
        Analyze jobs from the spreadsheet

        Args:
            process_all: If True, reanalyze all jobs. If False, only new ones.
        """
        logger.info("Starting job analysis...")

        # Get jobs to process
        if process_all:
            jobs = self.sheets_manager.get_job_urls()
        else:
            jobs = self.sheets_manager.get_unprocessed_jobs()

        if not jobs:
            logger.info("No jobs to process")
            return

        logger.info(f"Processing {len(jobs)} jobs...")

        processed_count = 0
        error_count = 0

        for idx, job_entry in enumerate(jobs, 1):
            logger.info(f"\n[{idx}/{len(jobs)}] Processing: {job_entry['url']}")

            try:
                # Fetch job description
                job_data = self.job_fetcher.fetch_job_description(job_entry['url'])

                if not job_data:
                    logger.warning(f"Failed to fetch job data, skipping")
                    error_count += 1
                    continue

                # Extract requirements
                job_requirements = self.job_fetcher.extract_requirements(job_data)

                # Calculate match
                match_result = self.job_matcher.calculate_match_score(
                    job_data,
                    job_requirements
                )

                # Prepare data for sheets
                analysis_data = {
                    'url': job_entry['url'],
                    'title': job_data['title'],
                    'company': job_data['company'],
                    'platform': job_data['platform'],
                    'match_score': f"{match_result['total_score']:.1f}%",
                    'recommendation': match_result['recommendation'],
                    'matched_skills': match_result['matched_skills'],
                    'missing_skills': match_result['missing_skills'],
                    'experience_required': match_result['experience_requirement'],
                    'your_experience': match_result['your_experience'],
                    'status': 'Analyzed',
                    'notes': ''
                }

                # Update spreadsheet
                self.sheets_manager.update_job_analysis(job_entry['row'], analysis_data)

                processed_count += 1

                # Log result
                score = match_result['total_score']
                recommendation = match_result['recommendation']
                logger.info(f"Match Score: {score:.1f}% - {recommendation}")

                # Small delay between requests
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error processing job: {e}")
                error_count += 1
                continue

        # Sort sheet by date
        logger.info("\nSorting spreadsheet by date...")
        self.sheets_manager.sort_by_date_descending()

        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"Analysis Complete!")
        logger.info(f"Processed: {processed_count}")
        logger.info(f"Errors: {error_count}")
        logger.info(f"{'='*60}")

    def analyze_single_job(self, job_url: str):
        """
        Analyze a single job URL and add to spreadsheet

        Args:
            job_url: URL of job posting
        """
        logger.info(f"Analyzing job: {job_url}")

        try:
            # Fetch job description
            job_data = self.job_fetcher.fetch_job_description(job_url)

            if not job_data:
                logger.error("Failed to fetch job data")
                return

            # Extract requirements
            job_requirements = self.job_fetcher.extract_requirements(job_data)

            # Calculate match
            match_result = self.job_matcher.calculate_match_score(
                job_data,
                job_requirements
            )

            # Display results
            print(f"\n{'='*60}")
            print(f"Job Title: {job_data['title']}")
            print(f"Company: {job_data['company']}")
            print(f"Platform: {job_data['platform']}")
            print(f"\nMatch Score: {match_result['total_score']:.1f}%")
            print(f"Recommendation: {match_result['recommendation']}")
            print(f"\nExperience Required: {match_result['experience_requirement']}")
            print(f"Your Experience: {match_result['your_experience']}")
            print(f"\nMatched Skills ({len(match_result['matched_skills'])}):")
            print(f"  {', '.join(match_result['matched_skills'][:15])}")
            if match_result['missing_skills']:
                print(f"\nMissing Skills ({len(match_result['missing_skills'])}):")
                print(f"  {', '.join(list(match_result['missing_skills'])[:15])}")
            print(f"{'='*60}\n")

            # Add to spreadsheet
            self.sheets_manager.add_new_job(job_data, match_result)
            logger.info("Added to spreadsheet")

        except Exception as e:
            logger.error(f"Error analyzing job: {e}")

    def generate_report(self):
        """Generate summary report of all analyzed jobs"""
        logger.info("Generating report...")

        jobs = self.sheets_manager.get_job_urls()

        if not jobs:
            logger.info("No jobs found in spreadsheet")
            return

        # Categorize jobs
        highly_recommended = []
        recommended = []
        consider = []
        not_recommended = []

        for job in jobs:
            status = job['existing_data'].get('Status', '')
            if status != 'Analyzed':
                continue

            recommendation = job['existing_data'].get('Recommendation', '')
            job_info = {
                'title': job['existing_data'].get('Job Title', 'Unknown'),
                'company': job['existing_data'].get('Company', 'Unknown'),
                'score': job['existing_data'].get('Match Score', 'N/A'),
                'url': job['url']
            }

            if 'HIGHLY RECOMMENDED' in recommendation:
                highly_recommended.append(job_info)
            elif 'RECOMMENDED' in recommendation:
                recommended.append(job_info)
            elif 'CONSIDER' in recommendation:
                consider.append(job_info)
            else:
                not_recommended.append(job_info)

        # Print report
        print(f"\n{'='*70}")
        print(f"JOB APPLICATION ANALYSIS REPORT")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        print(f"Total Jobs Analyzed: {len(jobs)}")
        print(f"  - Highly Recommended: {len(highly_recommended)}")
        print(f"  - Recommended: {len(recommended)}")
        print(f"  - Consider: {len(consider)}")
        print(f"  - Not Recommended: {len(not_recommended)}\n")

        if highly_recommended:
            print(f"HIGHLY RECOMMENDED JOBS ({len(highly_recommended)}):")
            print("-" * 70)
            for job in highly_recommended[:10]:  # Show top 10
                print(f"  [{job['score']}] {job['title']} - {job['company']}")
            print()

        if recommended:
            print(f"RECOMMENDED JOBS ({len(recommended)}):")
            print("-" * 70)
            for job in recommended[:10]:
                print(f"  [{job['score']}] {job['title']} - {job['company']}")
            print()

        print(f"{'='*70}\n")
        print(f"Full details available in your Google Sheet:")
        print(f"{self.spreadsheet_url}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Job Application Tracker & Analyzer - Analyze job postings and track applications"
    )

    parser.add_argument(
        '--resume',
        default='Resume.pdf',
        help='Path to resume PDF (default: Resume.pdf)'
    )

    parser.add_argument(
        '--credentials',
        default='credentials.json',
        help='Path to Google credentials JSON (default: credentials.json)'
    )

    parser.add_argument(
        '--sheet',
        required=True,
        help='Google Sheets URL'
    )

    parser.add_argument(
        '--threshold',
        type=float,
        default=50.0,
        help='Minimum match score threshold (default: 50.0)'
    )

    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyze all unprocessed jobs in spreadsheet'
    )

    parser.add_argument(
        '--analyze-all',
        action='store_true',
        help='Reanalyze ALL jobs in spreadsheet'
    )

    parser.add_argument(
        '--url',
        help='Analyze a single job URL and add to spreadsheet'
    )

    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate summary report'
    )

    args = parser.parse_args()

    # Validate paths
    if not Path(args.resume).exists():
        logger.error(f"Resume not found: {args.resume}")
        sys.exit(1)

    if not Path(args.credentials).exists():
        logger.error(f"Credentials not found: {args.credentials}")
        logger.info("Please download Google service account credentials and save as credentials.json")
        sys.exit(1)

    # Initialize tracker
    tracker = JobApplicationTracker(
        resume_path=args.resume,
        credentials_path=args.credentials,
        spreadsheet_url=args.sheet,
        match_threshold=args.threshold
    )

    tracker.initialize()

    # Execute requested action
    if args.url:
        tracker.analyze_single_job(args.url)
    elif args.analyze_all:
        tracker.analyze_jobs(process_all=True)
    elif args.analyze:
        tracker.analyze_jobs(process_all=False)
    elif args.report:
        tracker.generate_report()
    else:
        logger.info("No action specified. Use --help for usage information")
        logger.info("Try: --analyze to process new jobs, --url <job_url> to analyze a specific job")


if __name__ == "__main__":
    main()
