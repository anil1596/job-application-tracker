"""
Job Matcher - Matches job descriptions with resume
Calculates match scores based on skills, experience, and requirements
"""

import re
import logging
from typing import Dict, List, Set
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobMatcher:
    """Match job requirements against resume profile"""

    def __init__(self, resume_data: Dict):
        """
        Initialize matcher with resume data

        Args:
            resume_data: Parsed resume data from ResumeParser
        """
        self.resume_skills = set(skill.lower() for skill in resume_data.get('skills', []))
        self.resume_experience = resume_data.get('years_of_experience', 0)
        self.resume_text = resume_data.get('raw_text', '').lower()

    def calculate_match_score(self, job_data: Dict, job_requirements: Dict) -> Dict:
        """
        Calculate match score between resume and job

        Args:
            job_data: Job data from JobFetcher
            job_requirements: Extracted requirements from job description

        Returns:
            Dictionary with match score and details
        """
        scores = {}

        # 1. Skills match (40% weight)
        skills_score = self._calculate_skills_match(job_requirements['raw_description'])
        scores['skills'] = skills_score

        # 2. Experience match (30% weight)
        experience_score = self._calculate_experience_match(
            job_requirements['min_experience'],
            job_requirements['max_experience']
        )
        scores['experience'] = experience_score

        # 3. Title relevance (20% weight)
        title_score = self._calculate_title_match(job_requirements['title'])
        scores['title'] = title_score

        # 4. Description keyword match (10% weight)
        keyword_score = self._calculate_keyword_match(job_requirements['raw_description'])
        scores['keywords'] = keyword_score

        # Calculate weighted total
        total_score = (
            scores['skills'] * 0.40 +
            scores['experience'] * 0.30 +
            scores['title'] * 0.20 +
            scores['keywords'] * 0.10
        )

        # Extract matched and missing skills
        matched_skills, missing_skills = self._get_skill_breakdown(
            job_requirements['raw_description']
        )

        return {
            'total_score': round(total_score, 2),
            'breakdown': scores,
            'matched_skills': list(matched_skills),
            'missing_skills': list(missing_skills),
            'recommendation': self._get_recommendation(total_score),
            'experience_requirement': f"{job_requirements['min_experience']}-{job_requirements['max_experience']} years",
            'your_experience': f"{self.resume_experience} years"
        }

    def _calculate_skills_match(self, job_description: str) -> float:
        """Calculate skills match percentage"""
        job_desc_lower = job_description.lower()

        # Find skills mentioned in job description
        job_skills = set()
        for skill in self.resume_skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, job_desc_lower):
                job_skills.add(skill)

        # Also extract common technical terms from job description
        tech_terms = self._extract_tech_terms(job_desc_lower)

        if not tech_terms:
            # If no tech terms found, give benefit of doubt
            return 50.0

        # Calculate overlap
        matched = self.resume_skills.intersection(tech_terms)
        match_ratio = len(matched) / len(tech_terms) if tech_terms else 0

        # Scale to 0-100
        return min(match_ratio * 100, 100.0)

    def _calculate_experience_match(self, min_exp: int, max_exp: int) -> float:
        """Calculate experience match score"""
        if self.resume_experience < min_exp:
            # Penalize if under-qualified
            gap = min_exp - self.resume_experience
            if gap <= 1:
                return 70.0  # Close enough
            elif gap <= 2:
                return 50.0  # Might still apply
            else:
                return 30.0  # Under-qualified
        elif self.resume_experience > max_exp:
            # Penalize if over-qualified
            gap = self.resume_experience - max_exp
            if gap <= 2:
                return 80.0  # Still reasonable
            elif gap <= 5:
                return 60.0  # Might be over-qualified
            else:
                return 40.0  # Likely over-qualified
        else:
            # Perfect fit
            return 100.0

    def _calculate_title_match(self, job_title: str) -> float:
        """Calculate title relevance score"""
        title_lower = job_title.lower()

        # Software engineering related keywords
        relevant_keywords = [
            'software', 'engineer', 'developer', 'programmer', 'swe',
            'backend', 'frontend', 'full stack', 'fullstack', 'full-stack'
        ]

        # Check if title contains relevant keywords
        matches = sum(1 for keyword in relevant_keywords if keyword in title_lower)

        if matches >= 2:
            return 100.0
        elif matches == 1:
            return 70.0
        else:
            # Check if resume text contains role-related terms
            if any(keyword in self.resume_text for keyword in relevant_keywords):
                return 50.0
            return 30.0

    def _calculate_keyword_match(self, job_description: str) -> float:
        """Calculate general keyword match"""
        job_desc_lower = job_description.lower()

        # Extract important keywords from resume
        resume_words = set(re.findall(r'\b[a-z]{4,}\b', self.resume_text))

        # Extract keywords from job description
        job_words = set(re.findall(r'\b[a-z]{4,}\b', job_desc_lower))

        # Remove common stop words
        stop_words = {
            'that', 'this', 'with', 'from', 'have', 'been', 'were', 'will',
            'would', 'could', 'should', 'their', 'there', 'these', 'those',
            'about', 'more', 'such', 'other', 'into', 'through', 'where'
        }
        resume_words -= stop_words
        job_words -= stop_words

        if not job_words:
            return 50.0

        # Calculate overlap
        matched = resume_words.intersection(job_words)
        match_ratio = len(matched) / min(len(job_words), 50)  # Cap at 50 words

        return min(match_ratio * 100, 100.0)

    def _extract_tech_terms(self, text: str) -> Set[str]:
        """Extract technical terms from text"""
        tech_terms = set()

        # Common technical skills pattern
        from resume_parser import ResumeParser
        for skill in ResumeParser.COMMON_SKILLS:
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text):
                tech_terms.add(skill.lower())

        return tech_terms

    def _get_skill_breakdown(self, job_description: str) -> tuple:
        """Get matched and missing skills"""
        job_desc_lower = job_description.lower()

        # Find skills mentioned in job
        job_skills = self._extract_tech_terms(job_desc_lower)

        # Find matches
        matched = self.resume_skills.intersection(job_skills)
        missing = job_skills - self.resume_skills

        return matched, missing

    def _get_recommendation(self, score: float) -> str:
        """Get application recommendation based on score"""
        if score >= 80:
            return "HIGHLY RECOMMENDED - Strong match! Apply immediately."
        elif score >= 65:
            return "RECOMMENDED - Good match. Apply if interested."
        elif score >= 50:
            return "CONSIDER - Moderate match. Review carefully before applying."
        elif score >= 35:
            return "LOW PRIORITY - Weak match. Apply only if very interested."
        else:
            return "NOT RECOMMENDED - Poor match. Consider skipping."

    def should_apply(self, score: float, threshold: float = 50.0) -> bool:
        """
        Determine if should apply based on threshold

        Args:
            score: Match score
            threshold: Minimum score to recommend applying

        Returns:
            True if should apply
        """
        return score >= threshold


def match_job(resume_data: Dict, job_data: Dict, job_requirements: Dict) -> Dict:
    """
    Convenience function to match a job against resume

    Args:
        resume_data: Parsed resume data
        job_data: Job posting data
        job_requirements: Extracted job requirements

    Returns:
        Match result dictionary
    """
    matcher = JobMatcher(resume_data)
    return matcher.calculate_match_score(job_data, job_requirements)


if __name__ == "__main__":
    # Test the matcher
    from resume_parser import parse_resume

    resume_data = parse_resume("Resume.pdf")

    # Mock job data for testing
    job_data = {
        'title': 'Software Engineer',
        'company': 'Tech Company',
        'description': 'We are looking for a software engineer with 2-4 years of experience in Python, Django, and React...'
    }

    job_requirements = {
        'min_experience': 2,
        'max_experience': 4,
        'raw_description': job_data['description'],
        'title': job_data['title'],
        'company': job_data['company']
    }

    result = match_job(resume_data, job_data, job_requirements)

    print(f"\nMatch Score: {result['total_score']}/100")
    print(f"Recommendation: {result['recommendation']}")
    print(f"\nScore Breakdown:")
    for key, value in result['breakdown'].items():
        print(f"  {key.title()}: {value:.1f}")
    print(f"\nMatched Skills: {', '.join(result['matched_skills'][:10])}")
    if result['missing_skills']:
        print(f"Missing Skills: {', '.join(list(result['missing_skills'])[:10])}")
