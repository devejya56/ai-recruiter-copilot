"""
Email Monitor Agent
Monitors inbox for new job applications and candidate responses
"""

import imaplib
import email
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from config import EMAIL_CONFIG

@dataclass
class EmailData:
    sender: str
    subject: str
    body: str
    timestamp: datetime
    attachments: List[str]
    thread_id: Optional[str] = None
    category: str = 'general'  # 'application', 'response', 'inquiry', 'general'

class EmailMonitor:
    def __init__(self, config: dict):
        self.config = config
        self.imap_server = config.get('imap_server')
        self.smtp_server = config.get('smtp_server')
        self.email = config.get('email')
        self.password = config.get('password')
        self.smtp_port = config.get('smtp_port', 587)
        self.imap_port = config.get('imap_port', 993)
        self.logger = self._setup_logging()
        
        # Email classification patterns
        self.classification_patterns = {
            'application': [
                r'apply|application|resume|cv|position|job|career',
                r'interested in.*position',
                r'applying for',
                r'attached.*resume'
            ],
            'response': [
                r'thank you|thanks',
                r're:',  # Reply indicator
                r'response to',
                r'following up'
            ],
            'inquiry': [
                r'question|inquiry|information',
                r'would like to know',
                r'can you tell me',
                r'more information'
            ]
        }
    
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('email_monitor.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def connect_imap(self) -> imaplib.IMAP4_SSL:
        """Connect to IMAP server"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email, self.password)
            return mail
        except Exception as e:
            self.logger.error(f"IMAP connection failed: {e}")
            raise
    
    def connect_smtp(self) -> smtplib.SMTP:
        """Connect to SMTP server"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            return server
        except Exception as e:
            self.logger.error(f"SMTP connection failed: {e}")
            raise
    
    def classify_email(self, subject: str, body: str) -> str:
        """Classify email based on content"""
        content = f"{subject} {body}".lower()
        
        for category, patterns in self.classification_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return category
        
        return 'general'
    
    def extract_attachments(self, msg) -> List[str]:
        """Extract attachment information"""
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        attachments.append(filename)
        
        return attachments
    
    def parse_email(self, raw_email: bytes) -> EmailData:
        """Parse raw email into EmailData object"""
        try:
            msg = email.message_from_bytes(raw_email)
            
            # Extract basic info
            sender = msg.get('From', '')
            subject = msg.get('Subject', '')
            date_str = msg.get('Date', '')
            thread_id = msg.get('Message-ID', '')
            
            # Parse date
            try:
                timestamp = email.utils.parsedate_to_datetime(date_str)
            except:
                timestamp = datetime.now()
            
            # Extract body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            # Extract attachments
            attachments = self.extract_attachments(msg)
            
            # Classify email
            category = self.classify_email(subject, body)
            
            return EmailData(
                sender=sender,
                subject=subject,
                body=body,
                timestamp=timestamp,
                attachments=attachments,
                thread_id=thread_id,
                category=category
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing email: {e}")
            return None
    
    def monitor_new_emails(self, hours_back: int = 1) -> List[EmailData]:
        """Monitor for new emails within specified time window"""
        new_emails = []
        
        try:
            mail = self.connect_imap()
            mail.select('INBOX')
            
            # Calculate date filter
            since_date = (datetime.now() - timedelta(hours=hours_back)).strftime('%d-%b-%Y')
            
            # Search for recent emails
            status, message_ids = mail.search(None, f'(SINCE "{since_date}")')
            
            if status == 'OK':
                for msg_id in message_ids[0].split():
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    
                    if status == 'OK':
                        email_data = self.parse_email(msg_data[0][1])
                        if email_data:
                            new_emails.append(email_data)
                            self.logger.info(f"New email from {email_data.sender}: {email_data.subject}")
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            self.logger.error(f"Error monitoring emails: {e}")
        
        return new_emails
    
    def send_acknowledgment(self, to_email: str, subject: str, template_type: str = 'application') -> bool:
        """Send automatic acknowledgment email"""
        templates = {
            'application': {
                'subject': f'Re: {subject} - Application Received',
                'body': '''Dear Candidate,

Thank you for your interest in our position. We have received your application and will review it carefully.

Our team will get back to you within 3-5 business days with next steps.

Best regards,
HR Team'''
            },
            'inquiry': {
                'subject': f'Re: {subject} - Thank you for your inquiry',
                'body': '''Hello,

Thank you for reaching out. We have received your inquiry and will respond shortly.

If this is urgent, please don't hesitate to call us directly.

Best regards,
Support Team'''
            }
        }
        
        try:
            template = templates.get(template_type, templates['application'])
            
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = template['subject']
            
            msg.attach(MIMEText(template['body'], 'plain'))
            
            server = self.connect_smtp()
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Acknowledgment sent to {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending acknowledgment: {e}")
            return False
    
    def process_emails(self, hours_back: int = 1, send_acks: bool = True) -> Dict:
        """Main processing function - monitor and categorize emails"""
        results = {
            'total_processed': 0,
            'categories': {'application': 0, 'response': 0, 'inquiry': 0, 'general': 0},
            'emails': [],
            'acknowledgments_sent': 0
        }
        
        try:
            new_emails = self.monitor_new_emails(hours_back)
            
            for email_data in new_emails:
                results['emails'].append({
                    'sender': email_data.sender,
                    'subject': email_data.subject,
                    'category': email_data.category,
                    'timestamp': email_data.timestamp.isoformat(),
                    'has_attachments': len(email_data.attachments) > 0,
                    'attachments': email_data.attachments
                })
                
                results['categories'][email_data.category] += 1
                results['total_processed'] += 1
                
                # Send acknowledgment for applications and inquiries
                if send_acks and email_data.category in ['application', 'inquiry']:
                    sender_email = re.search(r'<(.+?)>', email_data.sender)
                    if sender_email:
                        sender_email = sender_email.group(1)
                    else:
                        sender_email = email_data.sender
                    
                    if self.send_acknowledgment(sender_email, email_data.subject, email_data.category):
                        results['acknowledgments_sent'] += 1
            
            self.logger.info(f"Processed {results['total_processed']} emails")
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing emails: {e}")
            return results
    
    def get_email_stats(self, days_back: int = 7) -> Dict:
        """Get email statistics for the past period"""
        stats = {
            'total_emails': 0,
            'daily_breakdown': {},
            'category_breakdown': {'application': 0, 'response': 0, 'inquiry': 0, 'general': 0},
            'top_senders': {},
            'peak_hours': {}
        }
        
        try:
            mail = self.connect_imap()
            mail.select('INBOX')
            
            since_date = (datetime.now() - timedelta(days=days_back)).strftime('%d-%b-%Y')
            status, message_ids = mail.search(None, f'(SINCE "{since_date}")')
            
            if status == 'OK':
                for msg_id in message_ids[0].split():
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    
                    if status == 'OK':
                        email_data = self.parse_email(msg_data[0][1])
                        if email_data:
                            stats['total_emails'] += 1
                            
                            # Daily breakdown
                            day = email_data.timestamp.date().isoformat()
                            stats['daily_breakdown'][day] = stats['daily_breakdown'].get(day, 0) + 1
                            
                            # Category breakdown
                            stats['category_breakdown'][email_data.category] += 1
                            
                            # Top senders
                            sender = email_data.sender
                            stats['top_senders'][sender] = stats['top_senders'].get(sender, 0) + 1
                            
                            # Peak hours
                            hour = email_data.timestamp.hour
                            stats['peak_hours'][str(hour)] = stats['peak_hours'].get(str(hour), 0) + 1
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            self.logger.error(f"Error getting email stats: {e}")
        
        return stats

def main():
    """Example usage"""
    monitor = EmailMonitor(EMAIL_CONFIG)
    
    # Process recent emails
    results = monitor.process_emails(hours_back=24)
    print(f"Processed {results['total_processed']} emails")
    print(f"Categories: {results['categories']}")
    print(f"Acknowledgments sent: {results['acknowledgments_sent']}")
    
    # Get weekly stats
    stats = monitor.get_email_stats(days_back=7)
    print(f"\nWeekly Stats:")
    print(f"Total emails: {stats['total_emails']}")
    print(f"Category breakdown: {stats['category_breakdown']}")

if __name__ == "__main__":
    main()
