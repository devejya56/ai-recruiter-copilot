"""
Resume Analyzer Agent
- Extracts resume text from PDFs/Docs
- Evaluates against job description using multiple LLMs (OpenAI, Anthropic, local)
- Produces structured scoring, gaps, and recommendations
"""

import io
import re
import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import pdfminer.high_level as pdfminer
except Exception:
    pdfminer = None

from config import LLM_CONFIG

@dataclass
class AnalysisScore:
    overall: float
    skills_match: float
    experience_match: float
    education_match: float
    keywords_coverage: float

@dataclass
class AnalysisResult:
    candidate_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    summary: str
    strengths: List[str]
    gaps: List[str]
    recommendations: List[str]
    matched_keywords: List[str]
    missing_keywords: List[str]
    score: AnalysisScore
    model_votes: Dict[str, float]
    created_at: str

class ResumeAnalyzer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logging()
        self.models = self._init_models()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(), logging.FileHandler('resume_analyzer.log')]
        )
        return logging.getLogger(__name__)

    def _init_models(self):
        models = {}
        # OpenAI
        if self.config.get('openai', {}).get('api_key'):
            try:
                from openai import OpenAI
                models['openai'] = OpenAI(api_key=self.config['openai']['api_key'])
                models['openai_model'] = self.config['openai'].get('model', 'gpt-4o-mini')
            except Exception as e:
                self.logger.warning(f"OpenAI init failed: {e}")
        # Anthropic
        if self.config.get('anthropic', {}).get('api_key'):
            try:
                import anthropic
                models['anthropic'] = anthropic.Anthropic(api_key=self.config['anthropic']['api_key'])
                models['anthropic_model'] = self.config['anthropic'].get('model', 'claude-3-5-sonnet-latest')
            except Exception as e:
                self.logger.warning(f"Anthropic init failed: {e}")
        # Local LLM (optional)
        if self.config.get('local', {}).get('endpoint'):
            models['local'] = self.config['local']
        return models

    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        name_lower = filename.lower()
        if name_lower.endswith('.pdf') and pdfminer:
            try:
                with io.BytesIO(file_bytes) as f:
                    return pdfminer.extract_text(f)
            except Exception as e:
                self.logger.warning(f"PDF extraction failed: {e}")
        # Fallback: basic decode
        try:
            return file_bytes.decode('utf-8', errors='ignore')
        except Exception:
            return ''

    def _simple_parse_contacts(self, text: str) -> Dict[str, Optional[str]]:
        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        phone_match = re.search(r"(\+\d{1,3}[- ]?)?\d{10,}", text)
        name_match = re.search(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b", text.splitlines()[0] if text else '')
        return {
            'email': email_match.group(0) if email_match else None,
            'phone': phone_match.group(0) if phone_match else None,
            'name': name_match.group(0) if name_match else None,
        }

    def _build_prompt(self, resume_text: str, job_desc: str) -> str:
        return (
            "You are an expert technical recruiter. Analyze the resume against the job description. "
            "Return STRICT JSON with keys: summary, strengths, gaps, recommendations, matched_keywords, missing_keywords, "
            "scores:{overall,skills_match,experience_match,education_match,keywords_coverage} in 0-100."
            f"\n\nJOB DESCRIPTION:\n{job_desc}\n\nRESUME:\n{resume_text[:12000]}"
        )

    def _call_openai(self, prompt: str) -> Optional[Dict[str, Any]]:
        try:
            client = self.models.get('openai')
            if not client:
                return None
            model = self.models.get('openai_model', 'gpt-4o-mini')
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            text = resp.choices[0].message.content
            return json.loads(text)
        except Exception as e:
            self.logger.warning(f"OpenAI call failed: {e}")
            return None

    def _call_anthropic(self, prompt: str) -> Optional[Dict[str, Any]]:
        try:
            client = self.models.get('anthropic')
            if not client:
                return None
            model = self.models.get('anthropic_model', 'claude-3-5-sonnet-latest')
            resp = client.messages.create(
                model=model,
                max_tokens=1200,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            text = ''.join([b.text for b in resp.content if hasattr(b, 'text')])
            return json.loads(text)
        except Exception as e:
            self.logger.warning(f"Anthropic call failed: {e}")
            return None

    def _call_local(self, prompt: str) -> Optional[Dict[str, Any]]:
        try:
            local = self.models.get('local')
            if not local:
                return None
            import requests
            r = requests.post(local['endpoint'], json={"prompt": prompt, "max_tokens": 1200, "temperature": 0.2}, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            self.logger.warning(f"Local LLM call failed: {e}")
            return None

    def _ensemble(self, outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        valid = [o for o in outputs if o]
        if not valid:
            return {}
        # Average numeric scores, union lists, combine text
        def avg(key_path):
            vals = []
            for o in valid:
                try:
                    vals.append(float(o['scores'][key_path]))
                except Exception:
                    pass
            return sum(vals) / len(vals) if vals else 0.0

        def list_union(key):
            s = []
            for o in valid:
                s.extend(o.get(key, []))
            dedup = []
            seen = set()
            for item in s:
                if isinstance(item, str):
                    k = item.strip().lower()
                    if k not in seen:
                        seen.add(k)
                        dedup.append(item)
            return dedup[:25]

        summary = ' '.join([o.get('summary', '') for o in valid])[:1000]
        strengths = list_union('strengths')
        gaps = list_union('gaps')
        recs = list_union('recommendations')
        mk = list_union('matched_keywords')
        missk = list_union('missing_keywords')
        result = {
            'summary': summary,
            'strengths': strengths,
            'gaps': gaps,
            'recommendations': recs,
            'matched_keywords': mk,
            'missing_keywords': missk,
            'scores': {
                'overall': round(avg('overall'), 2),
                'skills_match': round(avg('skills_match'), 2),
                'experience_match': round(avg('experience_match'), 2),
                'education_match': round(avg('education_match'), 2),
                'keywords_coverage': round(avg('keywords_coverage'), 2),
            }
        }
        # model votes
        votes = {}
        for o in valid:
            try:
                name = o.get('_model', 'unknown')
                votes[name] = float(o['scores']['overall'])
            except Exception:
                pass
        result['_model_votes'] = votes
        return result

    def analyze(self, file_bytes: bytes, filename: str, job_description: str, target_keywords: Optional[List[str]] = None) -> AnalysisResult:
        text = self.extract_text(file_bytes, filename)
        contacts = self._simple_parse_contacts(text)
        prompt = self._build_prompt(text, job_description)

        outputs = []
        oai = self._call_openai(prompt)
        if oai:
            oai['_model'] = 'openai'
            outputs.append(oai)
        claude = self._call_anthropic(prompt)
        if claude:
            claude['_model'] = 'anthropic'
            outputs.append(claude)
        local = self._call_local(prompt)
        if local:
            local['_model'] = 'local'
            outputs.append(local)

        ensembled = self._ensemble(outputs) if outputs else {
            'summary': 'Automated parsing only. LLM analysis unavailable.',
            'strengths': [], 'gaps': [], 'recommendations': [],
            'matched_keywords': [], 'missing_keywords': [],
            'scores': {k: 0.0 for k in ['overall','skills_match','experience_match','education_match','keywords_coverage']},
            '_model_votes': {}
        }

        # keyword pass using target_keywords
        if target_keywords:
            text_lower = text.lower()
            matched = [k for k in target_keywords if k.lower() in text_lower]
            missing = [k for k in target_keywords if k.lower() not in text_lower]
            ensembled['matched_keywords'] = list(set(ensembled.get('matched_keywords', []) + matched))
            ensembled['missing_keywords'] = list(set(ensembled.get('missing_keywords', []) + missing))

        result = AnalysisResult(
            candidate_name=contacts.get('name'),
            email=contacts.get('email'),
            phone=contacts.get('phone'),
            summary=ensembled['summary'],
            strengths=ensembled['strengths'],
            gaps=ensembled['gaps'],
            recommendations=ensembled['recommendations'],
            matched_keywords=ensembled['matched_keywords'],
            missing_keywords=ensembled['missing_keywords'],
            score=AnalysisScore(**ensembled['scores']),
            model_votes=ensembled.get('_model_votes', {}),
            created_at=datetime.utcnow().isoformat()
        )
        return result

    def to_json(self, analysis: AnalysisResult) -> str:
        obj = asdict(analysis)
        obj['score'] = asdict(analysis.score)
        return json.dumps(obj, indent=2)


def main():
    import argparse, base64, sys
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    parser.add_argument('--job', required=True, help='Path to job description text file')
    parser.add_argument('--keywords', nargs='*', default=[])
    args = parser.parse_args()

    with open(args.file, 'rb') as f:
        fb = f.read()
    with open(args.job, 'r', encoding='utf-8', errors='ignore') as f:
        jd = f.read()
    analyzer = ResumeAnalyzer(LLM_CONFIG)
    result = analyzer.analyze(fb, args.file, jd, args.keywords)
    print(ResumeAnalyzer(LLM_CONFIG).to_json(result))

if __name__ == '__main__':
    main()
