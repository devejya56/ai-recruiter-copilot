"""
Pipeline Manager Agent
- Orchestrates end-to-end recruiting pipeline across agents:
  EmailMonitor -> ResumeAnalyzer -> LinkedInEnricher -> Scheduler
- Maintains state, retries, and persistence via JSONL storage
"""

import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime

from .email_monitor import EmailMonitor
from .resume_analyzer import ResumeAnalyzer
from .linkedin_enricher import LinkedInEnricher
from .scheduler import Scheduler, TimeSlot

from config import EMAIL_CONFIG, LLM_CONFIG, ENRICHMENT_CONFIG, CALENDAR_CONFIG

@dataclass
class CandidateRecord:
    id: str
    email: str
    name: Optional[str]
    source: str
    subject: str
    created_at: str
    resume_analysis: Optional[Dict[str, Any]] = None
    linkedin_profile: Optional[Dict[str, Any]] = None
    stage: str = 'new'  # new -> analyzed -> enriched -> scheduled -> completed
    notes: str = ''

class Storage:
    def __init__(self, path: str = 'pipeline.jsonl'):
        self.path = path

    def append(self, record: Dict[str, Any]):
        with open(self.path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record) + '\n')

    def load_all(self) -> List[Dict[str, Any]]:
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                return [json.loads(line) for line in f if line.strip()]
        except FileNotFoundError:
            return []

    def upsert(self, key: str, value: str, new_record: Dict[str, Any]):
        records = self.load_all()
        updated = False
        with open(self.path, 'w', encoding='utf-8') as f:
            for rec in records:
                if rec.get(key) == value:
                    f.write(json.dumps(new_record) + '\n')
                    updated = True
                else:
                    f.write(json.dumps(rec) + '\n')
        if not updated:
            self.append(new_record)

class PipelineManager:
    def __init__(self):
        self.logger = self._setup_logging()
        self.email_monitor = EmailMonitor(EMAIL_CONFIG)
        self.analyzer = ResumeAnalyzer(LLM_CONFIG)
        self.enricher = LinkedInEnricher(ENRICHMENT_CONFIG)
        self.scheduler = Scheduler(EMAIL_CONFIG, CALENDAR_CONFIG)
        self.storage = Storage()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(), logging.FileHandler('pipeline_manager.log')]
        )
        return logging.getLogger(__name__)

    def ingest_email_application(self, email_data: Dict[str, Any]) -> CandidateRecord:
        sender = email_data.get('sender')
        email_addr = sender
        import re
        m = re.search(r'<(.+?)>', sender)
        if m:
            email_addr = m.group(1)
        name = sender.split('<')[0].strip().strip('"') if '<' in sender else None
        rec = CandidateRecord(
            id=email_data.get('thread_id') or email_addr,
            email=email_addr,
            name=name,
            source='email',
            subject=email_data.get('subject',''),
            created_at=datetime.utcnow().isoformat(),
            stage='new'
        )
        self.storage.append(asdict(rec))
        return rec

    def analyze_resume(self, rec: CandidateRecord, resume_bytes: Optional[bytes], filename: str, job_description: str, keywords: List[str]) -> CandidateRecord:
        analysis = self.analyzer.analyze(resume_bytes or b'', filename, job_description, keywords)
        rec.resume_analysis = asdict(analysis)
        rec.stage = 'analyzed'
        self.storage.upsert('id', rec.id, asdict(rec))
        return rec

    def enrich_linkedin(self, rec: CandidateRecord) -> CandidateRecord:
        query_name = rec.name or (rec.resume_analysis or {}).get('candidate_name') or rec.email.split('@')[0]
        profile = self.enricher.enrich(
            type('Q', (), {'name': query_name, 'email': rec.email, 'company': None, 'title': None, 'location': None})
        )
        rec.linkedin_profile = asdict(profile)
        rec.stage = 'enriched'
        self.storage.upsert('id', rec.id, asdict(rec))
        return rec

    def schedule_interview(self, rec: CandidateRecord, interviewer_emails: List[str], start_iso: str, duration_min: int = 60, link: Optional[str] = None) -> CandidateRecord:
        start_dt = datetime.fromisoformat(start_iso)
        end_dt = start_dt + timedelta(minutes=duration_min)
        from datetime import timedelta
        slot = TimeSlot(start=start_dt, end=end_dt)
        proposals = self.scheduler.propose_slots(rec.email, interviewer_emails, [slot], notes='Auto-scheduled by PipelineManager')
        if proposals:
            slot = proposals[0]
            self.scheduler.send_interview_invite(slot, link)
            rec.stage = 'scheduled'
            self.storage.upsert('id', rec.id, asdict(rec))
        return rec

    def run_once(self, job_description: str, keywords: List[str]) -> List[CandidateRecord]:
        """Poll new application emails and process them end-to-end"""
        processed = []
        emails = self.email_monitor.process_emails(hours_back=24, send_acks=True)
        for e in emails.get('emails', []):
            if e.get('category') != 'application':
                continue
            rec = self.ingest_email_application(e)
            # Note: attachment download not implemented in this simplified version
            rec = self.analyze_resume(rec, resume_bytes=None, filename='resume.txt', job_description=job_description, keywords=keywords)
            rec = self.enrich_linkedin(rec)
            processed.append(rec)
        self.logger.info(f"Pipeline processed {len(processed)} candidates")
        return processed


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--job', required=True, help='Path to job description file')
    parser.add_argument('--keywords', nargs='*', default=[])
    args = parser.parse_args()

    with open(args.job, 'r', encoding='utf-8', errors='ignore') as f:
        jd = f.read()
    manager = PipelineManager()
    recs = manager.run_once(jd, args.keywords)
    print(json.dumps([asdict(r) for r in recs], indent=2))

if __name__ == '__main__':
    main()
