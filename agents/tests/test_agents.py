"""Unit Tests for AI Recruitment Agents

This module contains comprehensive unit tests for the core agent components
including PDF parser, LLM aggregator, and Composio wrapper.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.pdf_parser import PDFParser, create_parser
from tools.llm_aggregator import LLMAggregator, LLMConfig, ModelProvider, create_default_aggregator
from tools.composio_wrapper import ComposioWrapper, ToolExecutionError, create_default_wrapper


class TestPDFParser(unittest.TestCase):
    """Test cases for PDFParser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = create_parser()
    
    def test_create_parser(self):
        """Test parser creation."""
        self.assertIsInstance(self.parser, PDFParser)
        self.assertIsNotNone(self.parser.email_pattern)
        self.assertIsNotNone(self.parser.phone_pattern)
    
    def test_extract_contact_info(self):
        """Test contact information extraction."""
        test_text = """
        John Doe
        Email: john.doe@example.com
        Phone: +1-555-123-4567
        LinkedIn: linkedin.com/in/johndoe
        """
        
        contact = self.parser._extract_contact_info(test_text)
        
        self.assertIsNotNone(contact['email'])
        self.assertEqual(contact['email'], 'john.doe@example.com')
        self.assertIsNotNone(contact['phone'])
        self.assertIsNotNone(contact['linkedin'])
    
    def test_extract_skills(self):
        """Test skill extraction."""
        test_text = """
        Skills: Python, Java, React, Docker, AWS, Machine Learning
        """
        
        skills = self.parser._extract_skills(test_text)
        
        self.assertIn('Python', skills)
        self.assertIn('Java', skills)
        self.assertIn('React', skills)
        self.assertIn('Docker', skills)
        self.assertGreater(len(skills), 0)
    
    def test_extract_education(self):
        """Test education extraction."""
        test_text = """
        Education:
        Bachelor of Science in Computer Science
        Master of Science in Engineering
        """
        
        education = self.parser._extract_education(test_text)
        
        self.assertIsInstance(education, list)
        # Should find at least one degree
        self.assertGreater(len(education), 0)
    
    def test_parse_pdf_file_not_found(self):
        """Test parsing non-existent file."""
        result = self.parser.parse_pdf('nonexistent_file.pdf')
        
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'File not found')
    
    @patch('builtins.open', create=True)
    @patch('PyPDF2.PdfReader')
    def test_parse_pdf_success(self, mock_pdf_reader, mock_open):
        """Test successful PDF parsing."""
        # Mock PDF page
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test resume content with Python and john@example.com"
        
        # Mock PDF reader
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        result = self.parser.parse_pdf('test_resume.pdf')
        
        self.assertIn('raw_text', result)
        self.assertIn('contact_info', result)
        self.assertIn('skills', result)


class TestLLMAggregator(unittest.TestCase):
    """Test cases for LLMAggregator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.configs = [
            LLMConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                api_key="test-key"
            )
        ]
        self.aggregator = LLMAggregator(self.configs)
    
    def test_create_aggregator(self):
        """Test aggregator creation."""
        self.assertIsInstance(self.aggregator, LLMAggregator)
        self.assertEqual(len(self.aggregator.configs), 1)
    
    def test_get_available_providers(self):
        """Test getting available providers."""
        providers = self.aggregator.get_available_providers()
        
        self.assertIsInstance(providers, list)
        # Mock implementation should have providers available
        self.assertGreater(len(providers), 0)
    
    def test_generate_with_specific_provider(self):
        """Test generation with specific provider."""
        result = self.aggregator.generate(
            prompt="Test prompt",
            provider=ModelProvider.OPENAI
        )
        
        self.assertIn('text', result)
        self.assertIn('provider', result)
        self.assertEqual(result['provider'], ModelProvider.OPENAI)
    
    def test_generate_fallback(self):
        """Test fallback to available provider."""
        result = self.aggregator.generate(
            prompt="Test prompt without specific provider"
        )
        
        self.assertIn('text', result)
        self.assertIn('provider', result)
        self.assertIn('model', result)
    
    def test_batch_generate(self):
        """Test batch generation."""
        prompts = [
            "Analyze resume 1",
            "Analyze resume 2",
            "Analyze resume 3"
        ]
        
        results = self.aggregator.batch_generate(prompts)
        
        self.assertEqual(len(results), len(prompts))
        for result in results:
            self.assertIn('text', result)
    
    def test_create_default_aggregator(self):
        """Test default aggregator creation."""
        aggregator = create_default_aggregator()
        
        self.assertIsInstance(aggregator, LLMAggregator)
        self.assertGreater(len(aggregator.configs), 0)
        providers = aggregator.get_available_providers()
        self.assertGreater(len(providers), 0)


class TestComposioWrapper(unittest.TestCase):
    """Test cases for ComposioWrapper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.wrapper = ComposioWrapper()
    
    def test_create_wrapper(self):
        """Test wrapper creation."""
        self.assertIsInstance(self.wrapper, ComposioWrapper)
        self.assertIsInstance(self.wrapper._registry, dict)
    
    def test_register_tool(self):
        """Test tool registration."""
        def test_tool(arg1, arg2):
            return arg1 + arg2
        
        self.wrapper.register('test_tool', test_tool)
        
        tools = self.wrapper.available_tools()
        self.assertIn('test_tool', tools)
    
    def test_invoke_tool(self):
        """Test tool invocation."""
        def multiply(x, y):
            return x * y
        
        self.wrapper.register('multiply', multiply)
        result = self.wrapper.invoke('multiply', x=5, y=3)
        
        self.assertEqual(result, 15)
    
    def test_invoke_nonexistent_tool(self):
        """Test invoking non-existent tool raises error."""
        with self.assertRaises(ToolExecutionError):
            self.wrapper.invoke('nonexistent_tool')
    
    def test_invoke_tool_with_error(self):
        """Test tool invocation error handling."""
        def error_tool():
            raise ValueError("Test error")
        
        self.wrapper.register('error_tool', error_tool)
        
        with self.assertRaises(ToolExecutionError):
            self.wrapper.invoke('error_tool')
    
    def test_create_default_wrapper(self):
        """Test default wrapper creation."""
        wrapper = create_default_wrapper()
        
        self.assertIsInstance(wrapper, ComposioWrapper)
        tools = wrapper.available_tools()
        
        # Default wrapper should have some pre-registered tools
        self.assertGreater(len(tools), 0)
        self.assertIn('send_email', tools)
        self.assertIn('search_candidates', tools)
    
    def test_tool_overwrite_warning(self):
        """Test warning when overwriting existing tool."""
        def tool1():
            return "version 1"
        
        def tool2():
            return "version 2"
        
        self.wrapper.register('test', tool1)
        
        # Should log warning but still work
        self.wrapper.register('test', tool2)
        
        result = self.wrapper.invoke('test')
        self.assertEqual(result, "version 2")


class TestIntegration(unittest.TestCase):
    """Integration tests for multiple components."""
    
    def test_parser_and_llm_integration(self):
        """Test integration between parser and LLM aggregator."""
        parser = create_parser()
        aggregator = create_default_aggregator()
        
        # Mock resume text
        resume_text = """
        John Doe
        Email: john.doe@example.com
        Skills: Python, Machine Learning, Docker
        
        Experience:
        Senior Software Engineer at Tech Corp
        2020 - Present
        """
        
        # Extract contact info
        contact = parser._extract_contact_info(resume_text)
        self.assertIsNotNone(contact['email'])
        
        # Use LLM to analyze
        prompt = f"Analyze candidate with email {contact['email']}"
        result = aggregator.generate(prompt)
        
        self.assertIn('text', result)
    
    def test_wrapper_and_parser_integration(self):
        """Test integration between wrapper and parser."""
        wrapper = ComposioWrapper()
        parser = create_parser()
        
        # Register parser as a tool
        def parse_resume_tool(text):
            return parser._extract_contact_info(text)
        
        wrapper.register('parse_resume', parse_resume_tool)
        
        # Use the tool
        test_text = "Email: test@example.com Phone: 555-1234"
        result = wrapper.invoke('parse_resume', text=test_text)
        
        self.assertIn('email', result)
        self.assertIsNotNone(result['email'])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_empty_resume_text(self):
        """Test parsing empty resume text."""
        parser = create_parser()
        
        contact = parser._extract_contact_info("")
        skills = parser._extract_skills("")
        
        self.assertIsNone(contact['email'])
        self.assertEqual(len(skills), 0)
    
    def test_invalid_email_format(self):
        """Test handling invalid email formats."""
        parser = create_parser()
        
        invalid_text = "Email: not-an-email"
        contact = parser._extract_contact_info(invalid_text)
        
        # Should not extract invalid email
        # (depends on regex strictness)
        self.assertIsInstance(contact, dict)
    
    def test_llm_with_empty_prompt(self):
        """Test LLM generation with empty prompt."""
        aggregator = create_default_aggregator()
        
        result = aggregator.generate("")
        
        # Should still return a result structure
        self.assertIn('text', result)
    
    def test_composio_with_no_registered_tools(self):
        """Test wrapper with no registered tools."""
        wrapper = ComposioWrapper()
        
        tools = wrapper.available_tools()
        self.assertEqual(len(tools), 0)
        
        with self.assertRaises(ToolExecutionError):
            wrapper.invoke('any_tool')


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
