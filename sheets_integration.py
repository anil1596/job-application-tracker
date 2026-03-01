"""
Google Sheets Integration - Read and write job application data
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SheetsManager:
    """Manage Google Sheets for job applications tracking"""

    # Required scopes for Google Sheets API
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    # Expected column headers
    HEADERS = [
        'Application Date',
        'Job URL',
        'Job Title',
        'Company',
        'Platform',
        'Match Score',
        'Recommendation',
        'Matched Skills',
        'Missing Skills',
        'Experience Required',
        'Your Experience',
        'Status',
        'Notes'
    ]

    def __init__(self, credentials_path: str, spreadsheet_url: str):
        """
        Initialize sheets manager

        Args:
            credentials_path: Path to Google service account credentials JSON
            spreadsheet_url: URL of the Google Sheet
        """
        self.credentials_path = credentials_path
        self.spreadsheet_url = spreadsheet_url
        self.client = None
        self.sheet = None

    def connect(self):
        """Connect to Google Sheets"""
        try:
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            self.client = gspread.authorize(creds)

            # Open spreadsheet
            self.sheet = self.client.open_by_url(self.spreadsheet_url).sheet1

            logger.info("Successfully connected to Google Sheets")

            # Ensure headers exist
            self._ensure_headers()

        except Exception as e:
            logger.error(f"Error connecting to Google Sheets: {e}")
            raise

    def _ensure_headers(self):
        """Ensure the sheet has proper headers"""
        try:
            existing_headers = self.sheet.row_values(1)

            if not existing_headers or existing_headers != self.HEADERS:
                logger.info("Setting up headers in spreadsheet")
                self.sheet.insert_row(self.HEADERS, 1)

        except Exception as e:
            logger.error(f"Error setting headers: {e}")

    def get_job_urls(self) -> List[Dict]:
        """
        Get all job URLs from the sheet

        Returns:
            List of dictionaries with job URL and existing data
        """
        try:
            # Get all records (skip header)
            records = self.sheet.get_all_records()

            jobs = []
            for idx, record in enumerate(records, start=2):  # Start at 2 (after header)
                job_url = record.get('Job URL', '').strip()
                if job_url:
                    jobs.append({
                        'row': idx,
                        'url': job_url,
                        'status': record.get('Status', ''),
                        'existing_data': record
                    })

            logger.info(f"Found {len(jobs)} job URLs in spreadsheet")
            return jobs

        except Exception as e:
            logger.error(f"Error reading job URLs: {e}")
            return []

    def update_job_analysis(self, row: int, analysis_data: Dict):
        """
        Update job analysis results in the sheet

        Args:
            row: Row number to update
            analysis_data: Dictionary with analysis results
        """
        try:
            # Prepare data in correct column order
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Check if application date already exists
            existing_date = self.sheet.cell(row, 1).value
            if not existing_date:
                application_date = current_date
            else:
                application_date = existing_date

            update_data = [
                application_date,
                analysis_data.get('url', ''),
                analysis_data.get('title', ''),
                analysis_data.get('company', ''),
                analysis_data.get('platform', ''),
                analysis_data.get('match_score', ''),
                analysis_data.get('recommendation', ''),
                ', '.join(analysis_data.get('matched_skills', [])[:10]),  # Limit to 10
                ', '.join(analysis_data.get('missing_skills', [])[:10]),  # Limit to 10
                analysis_data.get('experience_required', ''),
                analysis_data.get('your_experience', ''),
                analysis_data.get('status', 'Analyzed'),
                analysis_data.get('notes', '')
            ]

            # Update the entire row
            cell_range = f'A{row}:M{row}'
            self.sheet.update(cell_range, [update_data])

            logger.info(f"Updated row {row} with analysis data")

        except Exception as e:
            logger.error(f"Error updating row {row}: {e}")

    def add_new_job(self, job_data: Dict, analysis_data: Dict):
        """
        Add a new job to the sheet

        Args:
            job_data: Job information
            analysis_data: Match analysis results
        """
        try:
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            new_row = [
                current_date,
                job_data.get('url', ''),
                job_data.get('title', ''),
                job_data.get('company', ''),
                job_data.get('platform', ''),
                analysis_data.get('total_score', ''),
                analysis_data.get('recommendation', ''),
                ', '.join(analysis_data.get('matched_skills', [])[:10]),
                ', '.join(analysis_data.get('missing_skills', [])[:10]),
                analysis_data.get('experience_requirement', ''),
                analysis_data.get('your_experience', ''),
                'Analyzed',
                ''
            ]

            # Insert at row 2 (right after header) for descending order
            self.sheet.insert_row(new_row, 2)

            logger.info(f"Added new job: {job_data.get('title', 'Unknown')}")

        except Exception as e:
            logger.error(f"Error adding new job: {e}")

    def mark_as_processed(self, row: int, status: str = 'Processed'):
        """
        Mark a job as processed

        Args:
            row: Row number
            status: Status to set
        """
        try:
            # Update status column (column L, which is 12)
            self.sheet.update_cell(row, 12, status)
            logger.info(f"Marked row {row} as {status}")

        except Exception as e:
            logger.error(f"Error marking row {row}: {e}")

    def get_unprocessed_jobs(self) -> List[Dict]:
        """
        Get jobs that haven't been analyzed yet

        Returns:
            List of job dictionaries
        """
        all_jobs = self.get_job_urls()

        # Filter for jobs without status or with empty status
        unprocessed = [
            job for job in all_jobs
            if not job['status'] or job['status'].lower() in ['', 'pending', 'new']
        ]

        logger.info(f"Found {len(unprocessed)} unprocessed jobs")
        return unprocessed

    def sort_by_date_descending(self):
        """Sort sheet by application date in descending order"""
        try:
            # Get all values
            all_values = self.sheet.get_all_values()

            if len(all_values) <= 1:
                return  # No data to sort

            # Header
            header = all_values[0]

            # Data rows
            data_rows = all_values[1:]

            # Sort by first column (date) in descending order
            data_rows.sort(key=lambda x: x[0] if x[0] else '', reverse=True)

            # Update sheet
            self.sheet.clear()
            self.sheet.update('A1', [header] + data_rows)

            logger.info("Sorted sheet by date (descending)")

        except Exception as e:
            logger.error(f"Error sorting sheet: {e}")


def create_sample_sheet_template(credentials_path: str, spreadsheet_url: str):
    """
    Create a sample sheet template with headers

    Args:
        credentials_path: Path to credentials
        spreadsheet_url: Spreadsheet URL
    """
    manager = SheetsManager(credentials_path, spreadsheet_url)
    manager.connect()
    logger.info("Sheet template created successfully")


if __name__ == "__main__":
    # Test the sheets integration
    import sys

    if len(sys.argv) < 3:
        print("Usage: python sheets_integration.py <credentials_path> <spreadsheet_url>")
        sys.exit(1)

    creds_path = sys.argv[1]
    sheet_url = sys.argv[2]

    # Test connection and setup
    create_sample_sheet_template(creds_path, sheet_url)

    # Test reading
    manager = SheetsManager(creds_path, sheet_url)
    manager.connect()
    jobs = manager.get_job_urls()

    print(f"\nFound {len(jobs)} jobs in spreadsheet")
    for job in jobs[:5]:  # Show first 5
        print(f"- {job['url']}")
