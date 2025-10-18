"""Tests for resume parser."""

import pytest
from pathlib import Path
from tools.resume_parser import ResumeParser, ParsedResume


class TestResumeParser:
    """Test suite for ResumeParser."""
    
    @pytest.fixture
    def parser(self):
        """Create a ResumeParser instance."""
        return ResumeParser()
    
    def test_parse_text_with_email(self, parser):
        """Test parsing text with email."""
        text = """
        John Doe
        john.doe@example.com
        +1-555-123-4567
        
        Skills: Python, Java, Machine Learning
        """
        
        result = parser._parse_text(text)
        
        assert isinstance(result, ParsedResume)
        assert result.email == "john.doe@example.com"
        assert result.raw_text == text
    
    def test_extract_email(self, parser):
        """Test email extraction."""
        text = "Contact me at test@example.com for more info"
        email = parser._extract_email(text)
        assert email == "test@example.com"
    
    def test_extract_email_not_found(self, parser):
        """Test email extraction when no email present."""
        text = "This text has no email address"
        email = parser._extract_email(text)
        assert email is None
    
    def test_extract_phone(self, parser):
        """Test phone number extraction."""
        text = "Call me at (555) 123-4567"
        phone = parser._extract_phone(text)
        assert phone is not None
        assert "555" in phone
    
    def test_extract_phone_not_found(self, parser):
        """Test phone extraction when no phone present."""
        text = "This text has no phone number"
        phone = parser._extract_phone(text)
        assert phone is None
    
    def test_extract_skills(self, parser):
        """Test skill extraction."""
        text = "I have experience with Python, JavaScript, and Docker"
        skills = parser._extract_skills(text)
        
        assert "python" in skills
        assert "javascript" in skills
        assert "docker" in skills
    
    def test_parse_bytes_txt(self, parser):
        """Test parsing text bytes."""
        text = "John Doe\njohn@example.com\nSkills: Python, Java"
        result = parser.parse_bytes(text.encode('utf-8'), '.txt')
        
        assert isinstance(result, ParsedResume)
        assert result.email == "john@example.com"
    
    def test_unsupported_format(self, parser):
        """Test handling of unsupported file format."""
        with pytest.raises(ValueError, match="Unsupported file format"):
            parser.parse_bytes(b"content", '.xyz')
