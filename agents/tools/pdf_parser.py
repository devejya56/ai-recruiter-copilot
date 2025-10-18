"""PDF Parser Tool for Resume Extraction

This module provides functionality to parse PDF resumes and extract
structured information using PyPDF2 and custom extraction logic.
"""

import re
import logging
from typing import Dict, List, Optional
from pathlib import Path
import PyPDF2
from io import BytesIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFParser:
    """Parse PDF resumes and extract structured candidate information."""
    
    def __init__(self):
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'\+?\d[\d\s\-\(\)]{7,}\d'
        self.linkedin_pattern = r'linkedin\.com/in/[\w\-]+'
        
    def parse_pdf(self, file_path: str) -> Dict:
        """Parse PDF file and extract text content.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing parsed resume data
        """
        try:
            with open(file_path, 'rb') as file:
                return self._extract_from_file(file)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return {"error": "File not found"}
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            return {"error": str(e)}
    
    def parse_pdf_bytes(self, pdf_bytes: bytes) -> Dict:
        """Parse PDF from bytes object.
        
        Args:
            pdf_bytes: PDF content as bytes
            
        Returns:
            Dictionary containing parsed resume data
        """
        try:
            file_obj = BytesIO(pdf_bytes)
            return self._extract_from_file(file_obj)
        except Exception as e:
            logger.error(f"Error parsing PDF bytes: {str(e)}")
            return {"error": str(e)}
    
    def _extract_from_file(self, file_obj) -> Dict:
        """Extract structured data from PDF file object.
        
        Args:
            file_obj: File object containing PDF data
            
        Returns:
            Dictionary with extracted resume information
        """
        pdf_reader = PyPDF2.PdfReader(file_obj)
        text = ""
        
        # Extract text from all pages
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        # Extract structured information
        resume_data = {
            "raw_text": text,
            "contact_info": self._extract_contact_info(text),
            "skills": self._extract_skills(text),
            "experience": self._extract_experience(text),
            "education": self._extract_education(text),
            "summary": self._extract_summary(text)
        }
        
        return resume_data
    
    def _extract_contact_info(self, text: str) -> Dict:
        """Extract contact information from resume text."""
        contact = {
            "email": None,
            "phone": None,
            "linkedin": None
        }
        
        # Extract email
        email_match = re.search(self.email_pattern, text)
        if email_match:
            contact["email"] = email_match.group()
        
        # Extract phone
        phone_match = re.search(self.phone_pattern, text)
        if phone_match:
            contact["phone"] = phone_match.group().strip()
        
        # Extract LinkedIn
        linkedin_match = re.search(self.linkedin_pattern, text, re.IGNORECASE)
        if linkedin_match:
            contact["linkedin"] = linkedin_match.group()
        
        return contact
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from resume text."""
        # Common skill keywords to look for
        skill_keywords = [
            'Python', 'Java', 'JavaScript', 'C++', 'SQL', 'React', 'Node.js',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Machine Learning',
            'Deep Learning', 'NLP', 'Computer Vision', 'TensorFlow', 'PyTorch',
            'Git', 'Agile', 'Scrum', 'REST API', 'GraphQL', 'MongoDB', 'PostgreSQL'
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in skill_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience from resume text."""
        experience = []
        
        # Look for experience section
        experience_patterns = [
            r'(?i)experience.*?(?=education|skills|$)',
            r'(?i)work history.*?(?=education|skills|$)',
            r'(?i)employment.*?(?=education|skills|$)'
        ]
        
        for pattern in experience_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                exp_text = match.group()
                # Extract years (simple pattern)
                years = re.findall(r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current)', exp_text, re.IGNORECASE)
                
                for year_range in years:
                    experience.append({
                        "period": f"{year_range[0]} - {year_range[1]}",
                        "details": "Extracted from resume"
                    })
                break
        
        return experience
    
    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education information from resume text."""
        education = []
        
        # Common degree patterns
        degree_patterns = [
            r'(?i)(bachelor|master|phd|b\.?s\.?|m\.?s\.?|b\.?a\.?|m\.?a\.?|doctorate)',
            r'(?i)(computer science|engineering|business|mathematics|physics)'
        ]
        
        for pattern in degree_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match and match not in [e.get('degree', '') for e in education]:
                    education.append({
                        "degree": match,
                        "field": "Not specified"
                    })
        
        return education
    
    def _extract_summary(self, text: str) -> str:
        """Extract or generate a summary from the resume."""
        # Look for summary section
        summary_patterns = [
            r'(?i)summary.*?(?=experience|education|skills)',
            r'(?i)objective.*?(?=experience|education|skills)',
            r'(?i)profile.*?(?=experience|education|skills)'
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                summary = match.group().strip()
                # Limit to first 500 characters
                return summary[:500] if len(summary) > 500 else summary
        
        # If no summary section, return first 300 characters
        return text[:300].strip()


def create_parser() -> PDFParser:
    """Factory function to create a PDFParser instance."""
    return PDFParser()


if __name__ == "__main__":
    # Example usage
    parser = create_parser()
    result = parser.parse_pdf("sample_resume.pdf")
    print(f"Parsed resume: {result}")
