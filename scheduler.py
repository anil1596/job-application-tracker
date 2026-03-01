#!/usr/bin/env python3
"""
Scheduler - Run job analysis at scheduled times (6 AM and 4 PM)
Alternative to cron for simpler setup
"""

import schedule
import time
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JobScheduler:
    """Schedule job analysis runs"""

    def __init__(self, resume_path: str, credentials_path: str, spreadsheet_url: str):
        """
        Initialize scheduler

        Args:
            resume_path: Path to resume
            credentials_path: Path to credentials
            spreadsheet_url: Google Sheets URL
        """
        self.resume_path = resume_path
        self.credentials_path = credentials_path
        self.spreadsheet_url = spreadsheet_url

    def run_analysis(self):
        """Run the job analysis"""
        logger.info(f"{'='*60}")
        logger.info(f"Starting scheduled job analysis at {datetime.now()}")
        logger.info(f"{'='*60}")

        try:
            # Run main.py with --analyze flag
            cmd = [
                sys.executable,
                'main.py',
                '--sheet', self.spreadsheet_url,
                '--resume', self.resume_path,
                '--credentials', self.credentials_path,
                '--analyze'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            # Log output
            if result.stdout:
                logger.info(f"Output:\n{result.stdout}")

            if result.stderr:
                logger.error(f"Errors:\n{result.stderr}")

            if result.returncode == 0:
                logger.info("Analysis completed successfully")
            else:
                logger.error(f"Analysis failed with return code {result.returncode}")

        except subprocess.TimeoutExpired:
            logger.error("Analysis timed out after 10 minutes")
        except Exception as e:
            logger.error(f"Error running analysis: {e}")

        logger.info(f"{'='*60}\n")

    def start(self):
        """Start the scheduler"""
        logger.info("Job Application Tracker Scheduler")
        logger.info("Running analysis at 6:00 AM and 4:00 PM daily")
        logger.info("Press Ctrl+C to stop\n")

        # Schedule jobs
        schedule.every().day.at("06:00").do(self.run_analysis)
        schedule.every().day.at("16:00").do(self.run_analysis)

        # Optional: Run immediately on start (comment out if not desired)
        # logger.info("Running initial analysis...")
        # self.run_analysis()

        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("\nScheduler stopped by user")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Schedule automated job analysis at 6 AM and 4 PM daily"
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

    args = parser.parse_args()

    # Validate paths
    if not Path(args.resume).exists():
        logger.error(f"Resume not found: {args.resume}")
        sys.exit(1)

    if not Path(args.credentials).exists():
        logger.error(f"Credentials not found: {args.credentials}")
        sys.exit(1)

    # Start scheduler
    scheduler = JobScheduler(
        resume_path=args.resume,
        credentials_path=args.credentials,
        spreadsheet_url=args.sheet
    )

    scheduler.start()


if __name__ == "__main__":
    main()
