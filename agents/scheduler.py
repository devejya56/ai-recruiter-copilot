"""
Scheduler Agent
- Proposes interview slots
- Sends calendar invites via email + calendar integrations
- Manages confirmations and rescheduling
"""

import datetime
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
import uuid

from config import EMAIL_CONFIG, CALENDAR_CONFIG

@dataclass
class TimeSlot:
    start: datetime.datetime
    end: datetime.datetime
    timezone: str = 'UTC'

@dataclass
class InterviewSlot:
    slot_id: str
    candidate_email: str
    interviewer_emails: List[str]
    slot: TimeSlot
    status: str  # 'proposed', 'confirmed', 'declined', 'rescheduled'
    meeting_link: Optional[str] = None
    meeting_id: Optional[str] = None
    notes: str = ''

class Scheduler:
    def __init__(self, email_config: Dict[str, Any], calendar_config: Dict[str, Any]):
        self.email_config = email_config
        self.calendar_config = calendar_config
        self.logger = self._setup_logging()
        self.calendar_provider = self._init_calendar_provider()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(), logging.FileHandler('scheduler.log')]
        )
        return logging.getLogger(__name__)

    def _init_calendar_provider(self):
        provider = self.calendar_config.get('provider', 'email_only')
        if provider == 'google':
            return self._init_google_calendar()
        elif provider == 'outlook':
            return self._init_outlook_calendar()
        return None

    def _init_google_calendar(self):
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            creds = Credentials.from_authorized_user_file(self.calendar_config.get('credentials_file', 'token.json'))
            return build('calendar', 'v3', credentials=creds)
        except Exception as e:
            self.logger.warning(f"Google Calendar init failed: {e}")
            return None

    def _init_outlook_calendar(self):
        try:
            import msal
            app = msal.ConfidentialClientApplication(
                self.calendar_config['client_id'],
                authority=self.calendar_config.get('authority', 'https://login.microsoftonline.com/common'),
                client_credential=self.calendar_config['client_secret']
            )
            return app
        except Exception as e:
            self.logger.warning(f"Outlook Calendar init failed: {e}")
            return None

    def _generate_ical(self, slot: InterviewSlot) -> str:
        ical = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//AI Recruiter//Interview Scheduler//EN',
            'CALSCALE:GREGORIAN',
            'METHOD:REQUEST',
            'BEGIN:VEVENT',
            f'UID:{slot.slot_id}',
            f'DTSTAMP:{datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}',
            f'DTSTART:{slot.slot.start.strftime("%Y%m%dT%H%M%SZ")}',
            f'DTEND:{slot.slot.end.strftime("%Y%m%dT%H%M%SZ")}',
            'SUMMARY:Interview - Technical Round',
            f'DESCRIPTION:{slot.notes}',
            'STATUS:CONFIRMED',
            'SEQUENCE:0',
            f'ORGANIZER:mailto:{self.email_config["email"]}',
        ]
        for attendee in [slot.candidate_email] + slot.interviewer_emails:
            ical.append(f'ATTENDEE:mailto:{attendee}')
        if slot.meeting_link:
            ical.append(f'LOCATION:{slot.meeting_link}')
        ical.append('END:VEVENT')
        ical.append('END:VCALENDAR')
        return '\r\n'.join(ical)

    def _send_email_invite(self, slot: InterviewSlot, action: str = 'invite') -> bool:
        try:
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config.get('smtp_port', 587))
            server.starttls()
            server.login(self.email_config['email'], self.email_config['password'])

            msg = MIMEMultipart()
            msg['From'] = self.email_config['email']
            msg['To'] = slot.candidate_email
            msg['Cc'] = ','.join(slot.interviewer_emails)
            if action == 'invite':
                msg['Subject'] = f'Interview Invitation - {slot.slot.start.strftime("%B %d, %Y at %I:%M %p")}'
                body = f"""Dear Candidate,

We are pleased to invite you to an interview.

Date & Time: {slot.slot.start.strftime('%B %d, %Y at %I:%M %p')} {slot.slot.timezone}
Duration: {int((slot.slot.end - slot.slot.start).total_seconds() / 60)} minutes
{f'Meeting Link: {slot.meeting_link}' if slot.meeting_link else ''}

Please confirm your availability by replying to this email.

Best regards,
Hiring Team"""
            elif action == 'confirm':
                msg['Subject'] = 'Interview Confirmed'
                body = f"""Dear Candidate,

Your interview has been confirmed.

Date & Time: {slot.slot.start.strftime('%B %d, %Y at %I:%M %p')} {slot.slot.timezone}
Duration: {int((slot.slot.end - slot.slot.start).total_seconds() / 60)} minutes
{f'Meeting Link: {slot.meeting_link}' if slot.meeting_link else ''}

We look forward to meeting you!

Best regards,
Hiring Team"""
            else:
                msg['Subject'] = 'Interview Update'
                body = slot.notes

            msg.attach(MIMEText(body, 'plain'))

            # Attach iCal
            ical = self._generate_ical(slot)
            ical_part = MIMEApplication(ical.encode('utf-8'), _subtype='ics')
            ical_part.add_header('Content-Disposition', 'attachment', filename='invite.ics')
            msg.attach(ical_part)

            recipients = [slot.candidate_email] + slot.interviewer_emails
            server.sendmail(self.email_config['email'], recipients, msg.as_string())
            server.quit()

            self.logger.info(f"Email invite sent to {slot.candidate_email}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email invite: {e}")
            return False

    def _create_google_event(self, slot: InterviewSlot) -> Optional[str]:
        if not self.calendar_provider:
            return None
        try:
            event = {
                'summary': 'Interview - Technical Round',
                'description': slot.notes,
                'start': {'dateTime': slot.slot.start.isoformat(), 'timeZone': slot.slot.timezone},
                'end': {'dateTime': slot.slot.end.isoformat(), 'timeZone': slot.slot.timezone},
                'attendees': [{'email': e} for e in [slot.candidate_email] + slot.interviewer_emails],
            }
            if slot.meeting_link:
                event['location'] = slot.meeting_link
            result = self.calendar_provider.events().insert(calendarId='primary', body=event).execute()
            return result.get('id')
        except Exception as e:
            self.logger.error(f"Failed to create Google event: {e}")
            return None

    def propose_slots(self, candidate_email: str, interviewer_emails: List[str], available_slots: List[TimeSlot], notes: str = '') -> List[InterviewSlot]:
        """Generate interview slot proposals"""
        proposals = []
        for slot_time in available_slots:
            slot = InterviewSlot(
                slot_id=str(uuid.uuid4()),
                candidate_email=candidate_email,
                interviewer_emails=interviewer_emails,
                slot=slot_time,
                status='proposed',
                notes=notes
            )
            proposals.append(slot)
        return proposals

    def send_interview_invite(self, slot: InterviewSlot, meeting_link: Optional[str] = None) -> bool:
        """Send interview invitation with calendar integration"""
        if meeting_link:
            slot.meeting_link = meeting_link

        # Try calendar provider first
        if self.calendar_provider and self.calendar_config.get('provider') == 'google':
            event_id = self._create_google_event(slot)
            if event_id:
                slot.meeting_id = event_id
                slot.status = 'confirmed'

        # Always send email
        return self._send_email_invite(slot, action='invite')

    def confirm_interview(self, slot: InterviewSlot) -> bool:
        """Confirm an interview slot"""
        slot.status = 'confirmed'
        return self._send_email_invite(slot, action='confirm')

    def reschedule_interview(self, old_slot: InterviewSlot, new_time: TimeSlot) -> InterviewSlot:
        """Reschedule an existing interview"""
        old_slot.status = 'rescheduled'
        new_slot = InterviewSlot(
            slot_id=str(uuid.uuid4()),
            candidate_email=old_slot.candidate_email,
            interviewer_emails=old_slot.interviewer_emails,
            slot=new_time,
            status='proposed',
            meeting_link=old_slot.meeting_link,
            notes=f'Rescheduled from {old_slot.slot.start}. {old_slot.notes}'
        )
        return new_slot

    def to_json(self, slot: InterviewSlot) -> str:
        obj = asdict(slot)
        obj['slot'] = {
            'start': slot.slot.start.isoformat(),
            'end': slot.slot.end.isoformat(),
            'timezone': slot.slot.timezone
        }
        return json.dumps(obj, indent=2)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--interviewers', nargs='+', required=True)
    parser.add_argument('--start', required=True, help='ISO format datetime')
    parser.add_argument('--duration', type=int, default=60, help='Minutes')
    parser.add_argument('--link', help='Meeting link')
    parser.add_argument('--notes', default='')
    args = parser.parse_args()

    scheduler = Scheduler(EMAIL_CONFIG, CALENDAR_CONFIG)
    start_dt = datetime.datetime.fromisoformat(args.start)
    end_dt = start_dt + datetime.timedelta(minutes=args.duration)
    time_slot = TimeSlot(start=start_dt, end=end_dt)

    proposals = scheduler.propose_slots(args.candidate, args.interviewers, [time_slot], args.notes)
    if proposals:
        slot = proposals[0]
        success = scheduler.send_interview_invite(slot, args.link)
        print(f"Invite sent: {success}")
        print(scheduler.to_json(slot))

if __name__ == '__main__':
    main()
