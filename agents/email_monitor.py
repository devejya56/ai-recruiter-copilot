import os
import base64
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class EmailMonitor:
    """
    Monitors and processes candidate communication via email.
    Implements Gmail resume fetching via Gmail API with OAuth2 authentication.
    """
    
    # OAuth2 scopes for Gmail readonly and Calendar full access (supports both APIs with single credentials.json)
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/calendar'
    ]
    
    def __init__(self, email_service=None, auth_config_id=None, connected_account_id=None, project_id=None):
        self.email_service = email_service
        self.auth_config_id = auth_config_id
        self.connected_account_id = connected_account_id
        self.project_id = project_id
        self.creds = None
        self.service = None
        self._initialize_gmail_service()
    
    def _initialize_gmail_service(self):
        """
        Initialize Gmail API service using OAuth2 credentials.
        Uses credentials.json for OAuth2 flow and stores token in token.json.
        """
        try:
            # Check if token.json exists with stored credentials
            if os.path.exists('token.json'):
                self.creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
            
            # If credentials don't exist or are invalid, run OAuth2 flow
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    # Refresh expired credentials
                    from google.auth.transport.requests import Request
                    self.creds.refresh(Request())
                else:
                    # Run OAuth2 flow using credentials.json to generate new token
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', self.SCOPES)
                    self.creds = flow.run_local_server(port=0)
                
                # Save credentials to token.json for future use
                with open('token.json', 'w') as token:
                    token.write(self.creds.to_json())
            
            # Build Gmail API service with OAuth2 credentials
            self.service = build('gmail', 'v1', credentials=self.creds)
            
        except Exception as e:
            print(f"Failed to initialize Gmail service: {e}")
            self.service = None
    
    def list_emails(self, query: str = '', max_results: int = 10) -> List[Dict]:
        """
        List emails from Gmail inbox using Gmail API.
        """
        if not self.service:
            print("Gmail service not initialized")
            return []
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            return messages
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def fetch_resume_emails(self, days_back: int = 7) -> List[Dict]:
        """
        Fetch emails containing resumes from the last N days.
        
        Steps:
        1. Calculate date range (last N days)
        2. Build Gmail query to search for messages with attachments (PDF/DOCX)
           and keywords (resume, CV, application) in subject/body
        3. Fetch matching messages using Gmail API
        4. For each message, extract: sender name/email, subject, date, and attachment info
        5. Parse candidate information from email metadata and content
        6. Return list of structured candidate data
        """
        if not self.service:
            print("Gmail service not initialized")
            return []
        
        try:
            # Step 1: Calculate date range
            date_after = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            
            # Step 2: Build query for resume emails with attachments
            # Search for messages with PDF/DOCX attachments and resume-related keywords
            query = f"after:{date_after} (has:attachment filename:pdf OR filename:docx OR filename:doc) (subject:(resume OR CV OR application) OR (resume OR CV OR application))"
            
            # Step 3: Fetch matching messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50
            ).execute()
            
            messages = results.get('messages', [])
            resume_emails = []
            
            # Step 4 & 5: Extract and parse candidate information
            for msg in messages:
                try:
                    # Get full message details
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Extract headers
                    headers = message['payload'].get('headers', [])
                    subject = ''
                    sender = ''
                    date = ''
                    
                    for header in headers:
                        if header['name'].lower() == 'subject':
                            subject = header['value']
                        elif header['name'].lower() == 'from':
                            sender = header['value']
                        elif header['name'].lower() == 'date':
                            date = header['value']
                    
                    # Extract sender name and email
                    sender_name = ''
                    sender_email = ''
                    email_match = re.search(r'<(.+?)>', sender)
                    if email_match:
                        sender_email = email_match.group(1)
                        sender_name = sender.split('<')[0].strip().strip('"')
                    else:
                        sender_email = sender
                        sender_name = sender
                    
                    # Extract attachments
                    attachments = []
                    parts = message['payload'].get('parts', [])
                    
                    def extract_attachments(parts_list):
                        for part in parts_list:
                            if part.get('filename'):
                                filename = part['filename']
                                # Check if it's a resume file (PDF, DOC, DOCX)
                                if filename.lower().endswith(('.pdf', '.doc', '.docx')):
                                    attachments.append({
                                        'filename': filename,
                                        'mimeType': part.get('mimeType', ''),
                                        'size': part.get('body', {}).get('size', 0)
                                    })
                            # Recursively check nested parts
                            if part.get('parts'):
                                extract_attachments(part['parts'])
                    
                    extract_attachments(parts)
                    
                    # Step 6: Build candidate info dictionary
                    if attachments:  # Only include if attachments found
                        candidate_info = {
                            'message_id': msg['id'],
                            'sender_name': sender_name,
                            'sender_email': sender_email,
                            'subject': subject,
                            'date': date,
                            'attachments': attachments,
                            'thread_id': message.get('threadId', '')
                        }
                        resume_emails.append(candidate_info)
                        
                except Exception as e:
                    print(f"Error processing message {msg['id']}: {e}")
                    continue
            
            print(f"Found {len(resume_emails)} resume emails from the last {days_back} days")
            return resume_emails
            
        except HttpError as error:
            print(f"An error occurred while fetching resume emails: {error}")
            return []
        except Exception as e:
            print(f"Unexpected error in fetch_resume_emails: {e}")
            return []
