class ResumeAnalyzer:
    """
    Parses and analyzes resume contents using NLP and ML models.
    """
    def __init__(self, nlp_model=None):
        self.nlp_model = nlp_model

    def analyze(self, resume_data, job_id):
        # NLP-based analysis with keywords, experience matching, etc.
        if not self.nlp_model:
            print("No NLP model provided. Returning dummy analysis.")
            return {"summary": "Strong candidate", "skills": ["Python", "ML"]}
        try:
            analysis = self.nlp_model.run_analysis(resume_data, job_id)
            return analysis
        except Exception as e:
            print(f"Resume analysis failed: {e}")
            return {"summary": "Analysis unavailable"}
