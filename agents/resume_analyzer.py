import openai
import os
from typing import Dict, List, Any
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ResumeAnalyzer:
    """
    Analyzes resume contents using OpenAI GPT-4 for intelligent candidate evaluation.
    """
    
    def __init__(self):
        """
        Initialize the ResumeAnalyzer with OpenAI API key from environment variables.
        """
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        openai.api_key = self.openai_api_key
    
    def analyze(self, resume_data: Dict[str, Any], job_description: str = None) -> Dict[str, Any]:
        """
        Analyze resume using OpenAI GPT-4 for comprehensive candidate evaluation.
        
        Args:
            resume_data: Dictionary containing resume information
            job_description: Optional job description for targeted analysis
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Prepare resume text for analysis
            resume_text = self._extract_resume_text(resume_data)
            
            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(resume_text, job_description)
            
            # Call OpenAI GPT-4 for analysis
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert HR recruiter and resume analyst. Provide detailed, objective analysis of resumes."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            # Parse and structure the response
            analysis_result = self._parse_gpt_response(response.choices[0].message.content)
            
            return analysis_result
            
        except Exception as e:
            print(f"Resume analysis failed: {e}")
            return {
                "summary": "Analysis unavailable due to error",
                "error": str(e),
                "skills": [],
                "experience_level": "Unknown",
                "match_score": 0
            }
    
    def _extract_resume_text(self, resume_data: Dict[str, Any]) -> str:
        """
        Extract text content from resume data structure.
        
        Args:
            resume_data: Dictionary containing resume information
            
        Returns:
            Formatted resume text for analysis
        """
        if isinstance(resume_data, str):
            return resume_data
        
        text_parts = []
        
        # Extract common resume sections
        sections = [
            'name', 'contact', 'email', 'phone', 'address',
            'summary', 'objective', 'experience', 'work_experience',
            'education', 'skills', 'projects', 'certifications',
            'achievements', 'languages', 'interests'
        ]
        
        for section in sections:
            if section in resume_data and resume_data[section]:
                text_parts.append(f"{section.upper()}: {resume_data[section]}")
        
        # If no structured data, try to get raw text
        if not text_parts and 'text' in resume_data:
            text_parts.append(resume_data['text'])
        elif not text_parts:
            text_parts.append(str(resume_data))
        
        return "\n\n".join(text_parts)
    
    def _create_analysis_prompt(self, resume_text: str, job_description: str = None) -> str:
        """
        Create a comprehensive analysis prompt for GPT-4.
        
        Args:
            resume_text: The resume content to analyze
            job_description: Optional job description for targeted analysis
            
        Returns:
            Formatted prompt for GPT-4 analysis
        """
        base_prompt = f"""
Please analyze the following resume and provide a comprehensive evaluation in JSON format:

=== RESUME ===
{resume_text}

=== ANALYSIS REQUEST ===
Provide your analysis in the following JSON structure:
{{
    "summary": "Brief overall assessment (2-3 sentences)",
    "experience_level": "Entry/Mid/Senior/Executive",
    "skills": ["skill1", "skill2", "skill3"],
    "key_strengths": ["strength1", "strength2", "strength3"],
    "areas_for_improvement": ["area1", "area2"],
    "years_of_experience": "estimated years",
    "education_level": "highest education level",
    "industry_background": ["industry1", "industry2"],
    "match_score": "score out of 100 for general hirability",
    "notable_achievements": ["achievement1", "achievement2"]
}}
"""
        
        if job_description:
            base_prompt += f"""

=== JOB DESCRIPTION ===
{job_description}

=== ADDITIONAL REQUEST ===
Also provide job-specific analysis:
- Job match score (0-100)
- Specific skills alignment
- Missing qualifications
- Recommendations for interview focus
"""
        
        return base_prompt
    
    def _parse_gpt_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse GPT-4 response into structured format.
        
        Args:
            response_text: Raw response from GPT-4
            
        Returns:
            Parsed analysis results
        """
        try:
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_text = response_text[json_start:json_end]
                parsed_result = json.loads(json_text)
                
                # Ensure required fields exist
                default_result = {
                    "summary": "Candidate analysis completed",
                    "experience_level": "Mid",
                    "skills": [],
                    "key_strengths": [],
                    "areas_for_improvement": [],
                    "years_of_experience": "Unknown",
                    "education_level": "Unknown",
                    "industry_background": [],
                    "match_score": 50,
                    "notable_achievements": []
                }
                
                # Merge with defaults
                for key, default_value in default_result.items():
                    if key not in parsed_result:
                        parsed_result[key] = default_value
                
                return parsed_result
            else:
                # Fallback if JSON parsing fails
                return {
                    "summary": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                    "experience_level": "Mid",
                    "skills": [],
                    "match_score": 50
                }
                
        except json.JSONDecodeError:
            return {
                "summary": "Analysis completed but formatting error occurred",
                "experience_level": "Unknown",
                "skills": [],
                "match_score": 0,
                "error": "JSON parsing failed"
            }
    
    def bulk_analyze(self, resumes: List[Dict[str, Any]], job_description: str = None) -> List[Dict[str, Any]]:
        """
        Analyze multiple resumes in batch.
        
        Args:
            resumes: List of resume data dictionaries
            job_description: Optional job description for targeted analysis
            
        Returns:
            List of analysis results
        """
        results = []
        
        for i, resume in enumerate(resumes):
            print(f"Analyzing resume {i+1}/{len(resumes)}...")
            try:
                result = self.analyze(resume, job_description)
                result['resume_index'] = i
                results.append(result)
            except Exception as e:
                print(f"Failed to analyze resume {i+1}: {e}")
                results.append({
                    "resume_index": i,
                    "summary": "Analysis failed",
                    "error": str(e),
                    "match_score": 0
                })
        
        return results
    
    def compare_candidates(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare multiple candidate analyses and provide rankings.
        
        Args:
            analyses: List of analysis results from analyze() method
            
        Returns:
            Comparison results with rankings
        """
        if not analyses:
            return {"error": "No analyses provided"}
        
        # Sort by match score
        sorted_analyses = sorted(
            analyses, 
            key=lambda x: x.get('match_score', 0), 
            reverse=True
        )
        
        # Calculate statistics
        scores = [a.get('match_score', 0) for a in analyses]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "total_candidates": len(analyses),
            "average_score": round(avg_score, 2),
            "top_candidate": sorted_analyses[0] if sorted_analyses else None,
            "rankings": sorted_analyses,
            "score_distribution": {
                "high_performers": len([s for s in scores if s >= 80]),
                "medium_performers": len([s for s in scores if 50 <= s < 80]),
                "low_performers": len([s for s in scores if s < 50])
            }
        }
