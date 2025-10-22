import os
import base64
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class EmailMonitor:
    """
    Monitors and processes candidate communication via email.
    Implements Gmail resume fetching via Gmail API.
    """
    
    def __init__(self, email_service=None, auth_config_id=None):
        self.email_service = email_service
        self.auth_config_id = auth_config_id
        self.gmail_api_key = os.getenv('GMAIL_API_KEY')
        self.service = None
        if self.gmail_api_key:
            self._initialize_gmail_service()
    
    def _initialize_gmail_service(self):
        """
        Initialize Gmail API service using the API key from .env
        """
        try:
            # Initialize Gmail API service
            self.service = build('gmail', 'v1', developerKey=self.gmail_api_key)
        except Exception as e:
            print(f"Failed to initialize Gmail service: {e}")
            self.service = None
    
    def list_emails(self, query: str = '', max_results: int = 10) -> List[Dict]:
        """
        List emails from Gmail inbox using Gmail API.
        
        Args:
            query: Gmail search query (e.g., 'has:attachment')
            max_results: Maximum number of emails to retrieve
            
        Returns:
            List of email dictionaries with basic info
        """
        if not self.service:
            print("Gmail service not initialized. Check GMAIL_API_KEY in .env")
            return []
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            email_list = []
            
            for message in messages:
                msg_detail = self._get_email_detail(message['id'])
                if msg_detail:
                    email_list.append(msg_detail)
            
            return email_list
            
        except HttpError as error:
            print(f"An error occurred while listing emails: {error}")
            return []
    
    def _get_email_detail(self, message_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific email.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Dictionary with email details
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            subject = ''
            sender = ''
            date = ''
            
            for header in headers:
                if header['name'] == 'Subject':
                    subject = header['value']
                elif header['name'] == 'From':
                    sender = header['value']
                elif header['name'] == 'Date':
                    date = header['value']
            
            return {
                'id': message_id,
                'subject': subject,
                'from': sender,
                'date': date,
                'payload': message['payload']
            }
            
        except HttpError as error:
            print(f"An error occurred getting email detail: {error}")
            return None
    
    def filter_resume_emails(self, emails: List[Dict]) -> List[Dict]:
        """
        Filter emails that contain resume attachments (PDF or DOCX).
        
        Args:
            emails: List of email dictionaries
            
        Returns:
            List of emails containing resume attachments
        """
        resume_emails = []
        resume_keywords = ['resume', 'cv', 'curriculum vitae', 'application']
        allowed_extensions = ['.pdf', '.docx', '.doc']
        
        for email in emails:
            has_resume = False
            attachments = self._extract_attachments(email.get('payload', {}))
            
            for attachment in attachments:
                filename = attachment.get('filename', '').lower()
                
                # Check if file has resume-related extension
                if any(filename.endswith(ext) for ext in allowed_extensions):
                    # Check if filename or subject contains resume keywords
                    subject = email.get('subject', '').lower()
                    if any(keyword in filename or keyword in subject for keyword in resume_keywords):
                        has_resume = True
                        break
            
            if has_resume:
                resume_emails.append(email)
        
        return resume_emails
    
    def _extract_attachments(self, payload: Dict) -> List[Dict]:
        """
        Extract attachment information from email payload.
        
        Args:
            payload: Email payload from Gmail API
            
        Returns:
            List of attachment dictionaries
        """
        attachments = []
        
        def parse_parts(parts):
            for part in parts:
                if part.get('filename'):
                    attachments.append({
                        'filename': part['filename'],
                        'mimeType': part.get('mimeType'),
                        'attachmentId': part['body'].get('attachmentId'),
                        'size': part['body'].get('size')
                    })
                
                if 'parts' in part:
                    parse_parts(part['parts'])
        
        if 'parts' in payload:
            parse_parts(payload['parts'])
        
        return attachments
    
    def extract_candidate_data(self, email: Dict) -> Dict:
        """
        Extract candidate data from resume email.
        
        Args:
            email: Email dictionary with resume attachment
            
        Returns:
            Dictionary with extracted candidate information
        """
        candidate_data = {
            'email_id': email.get('id'),
            'candidate_email': self._parse_email_address(email.get('from', '')),
            'candidate_name': self._parse_name_from_email(email.get('from', '')),
            'subject': email.get('subject', ''),
            'received_date': email.get('date', ''),
            'attachments': []
        }
        
        # Extract attachment information
        payload = email.get('payload', {})
        attachments = self._extract_attachments(payload)
        
        # Filter for resume attachments only
        allowed_extensions = ['.pdf', '.docx', '.doc']
        for attachment in attachments:
            filename = attachment.get('filename', '')
            if any(filename.lower().endswith(ext) for ext in allowed_extensions):
                candidate_data['attachments'].append({
                    'filename': filename,
                    'mimeType': attachment.get('mimeType'),
                    'attachmentId': attachment.get('attachmentId'),
                    'size': attachment.get('size')
                })
        
        return candidate_data
    
    def _parse_email_address(self, from_header: str) -> str:
        """
        Parse email address from 'From' header.
        
        Args:
            from_header: From header string (e.g., 'John Doe <john@example.com>')
            
        Returns:
            Email address string
        """
        import re
        match = re.search(r'<(.+?)>', from_header)
        if match:
            return match.group(1)
        return from_header.strip()
    
    def _parse_name_from_email(self, from_header: str) -> str:
        """
        Parse name from 'From' header.
        
        Args:
            from_header: From header string (e.g., 'John Doe <john@example.com>')
            
        Returns:
            Name string
        """
        if '<' in from_header:
            name = from_header.split('<')[0].strip()
            # Remove quotes if present
            return name.strip('"').strip("'")
        return ''
    
    def fetch_resume_emails(self, max_results: int = 20) -> List[Dict]:
        """
        Main method to fetch and process emails with resume attachments.
        
        Args:
            max_results: Maximum number of emails to check
            
        Returns:
            List of candidate data dictionaries
        """
        # Search for emails with attachments
        query = 'has:attachment (resume OR cv OR application)'
        emails = self.list_emails(query=query, max_results=max_results)
        
        if not emails:
            print("No emails found with attachments")
            return []
        
        # Filter for resume attachments
        resume_emails = self.filter_resume_emails(emails)
        
        # Extract candidate data from each resume email
        candidates = []
        for email in resume_emails:
            candidate_data = self.extract_candidate_data(email)
            candidates.append(candidate_data)
        
        print(f"Found {len(candidates)} candidates with resume attachments")
        return candidates
    
    def fetch_emails(self, candidate_id):
        """
        Legacy method for backward compatibility.
        Fetches emails for a specific candidate.
        """
        if not self.email_service:
            print("No email service provided. Returning dummy emails.")
            return [{"id": "email1", "body": "Welcome candidate."}]
        try:
            emails = self.email_service.get_emails(candidate_id)
            return emails
        except Exception as e:
            print(f"Failed to fetch emails: {e}")
            return []
