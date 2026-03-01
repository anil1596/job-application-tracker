"""
Resume Parser - Extracts skills, experience, and other relevant information from resume PDFs
"""

import pdfplumber
import re
from typing import Dict, List, Set
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResumeParser:
    """Parse resume PDF and extract key information"""

    # Common technical skills to look for
    COMMON_SKILLS = {
        # Programming Languages
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
        'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab',

        # Frontend
        'react', 'angular', 'vue', 'html', 'css', 'sass', 'less', 'webpack',
        'redux', 'next.js', 'gatsby', 'tailwind',

        # Backend
        'node.js', 'express', 'django', 'flask', 'fastapi', 'spring', 'spring boot',
        '.net', 'asp.net', 'rails', 'laravel',

        # Databases
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'dynamodb', 'cassandra', 'oracle', 'sqlite',

        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab',
        'github actions', 'terraform', 'ansible', 'ci/cd',

        # Tools & Others
        'git', 'jira', 'agile', 'scrum', 'rest api', 'graphql', 'microservices',
        'linux', 'bash', 'shell scripting', 'testing', 'junit', 'pytest',
        'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'pandas',
        'numpy', 'data structures', 'algorithms', 'system design'
    }

    def __init__(self, resume_path: str):
        """
        Initialize resume parser

        Args:
            resume_path: Path to resume PDF file
        """
        self.resume_path = resume_path
        self.text = ""
        self.skills = set()
        self.years_of_experience = 0

    def parse(self) -> Dict:
        """
        Parse the resume and extract information

        Returns:
            Dictionary containing extracted information
        """
        self._extract_text()
        self._extract_skills()
        self._extract_experience()

        return {
            'skills': list(self.skills),
            'years_of_experience': self.years_of_experience,
            'raw_text': self.text
        }

    def _extract_text(self):
        """Extract text from PDF"""
        try:
            with pdfplumber.open(self.resume_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    text_parts.append(page.extract_text())
                self.text = '\n'.join(text_parts)
            logger.info(f"Extracted {len(self.text)} characters from resume")
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

    def _extract_skills(self):
        """Extract skills from resume text"""
        text_lower = self.text.lower()

        # Find skills mentioned in resume
        for skill in self.COMMON_SKILLS:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                self.skills.add(skill)

        # Also look for skills in a dedicated skills section
        skills_section = self._extract_section('skills')
        if skills_section:
            # Extract comma-separated or bullet-pointed items
            items = re.split(r'[,•\n]', skills_section)
            for item in items:
                item = item.strip().lower()
                if item and len(item) > 2:
                    self.skills.add(item)

        logger.info(f"Extracted {len(self.skills)} skills")

    def _extract_experience(self):
        """Extract years of experience from resume"""
        # Look for date ranges in experience section
        experience_section = self._extract_section('experience')

        if not experience_section:
            # Try to find dates in the entire resume
            experience_section = self.text

        # Find year patterns (e.g., "2020 - 2023", "Jan 2020 - Present")
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, experience_section)

        if years:
            years_int = [int(y) for y in years]
            # Calculate rough experience as difference between earliest and latest year
            if len(years_int) >= 2:
                self.years_of_experience = max(years_int) - min(years_int)

        # Look for explicit mentions like "5+ years of experience"
        exp_pattern = r'(\d+)\+?\s*years?\s*(of)?\s*experience'
        match = re.search(exp_pattern, self.text.lower())
        if match:
            stated_years = int(match.group(1))
            # Take the maximum of calculated and stated
            self.years_of_experience = max(self.years_of_experience, stated_years)

        logger.info(f"Estimated years of experience: {self.years_of_experience}")

    def _extract_section(self, section_name: str) -> str:
        """
        Extract a specific section from resume

        Args:
            section_name: Name of section to extract (e.g., 'skills', 'experience')

        Returns:
            Text content of the section
        """
        # Common section headers
        patterns = {
            'skills': r'(?i)(technical\s+)?skills?:?\s*\n',
            'experience': r'(?i)(work\s+|professional\s+)?experience:?\s*\n',
            'education': r'(?i)education:?\s*\n'
        }

        if section_name.lower() not in patterns:
            return ""

        pattern = patterns[section_name.lower()]
        match = re.search(pattern, self.text)

        if not match:
            return ""

        # Extract text from this section until next section or end
        start = match.end()
        # Look for next section header (all caps or Title Case followed by colon)
        next_section = re.search(r'\n[A-Z][A-Za-z\s]+:?\n', self.text[start:])

        if next_section:
            end = start + next_section.start()
            return self.text[start:end]
        else:
            # Return rest of document
            return self.text[start:start+1000]  # Limit to 1000 chars


def parse_resume(resume_path: str) -> Dict:
    """
    Convenience function to parse a resume

    Args:
        resume_path: Path to resume PDF

    Returns:
        Dictionary with extracted resume information
    """
    parser = ResumeParser(resume_path)
    return parser.parse()


if __name__ == "__main__":
    # Test the parser
    import sys

    if len(sys.argv) > 1:
        resume_path = sys.argv[1]
    else:
        resume_path = "Resume.pdf"

    result = parse_resume(resume_path)
    print(f"\nSkills found: {len(result['skills'])}")
    print(f"Skills: {', '.join(sorted(result['skills']))}")
    print(f"\nYears of experience: {result['years_of_experience']}")
