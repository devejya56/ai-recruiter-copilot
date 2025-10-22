"""Automation Agent for Composio Workflow Integration.
This module provides an agent that integrates with Composio workflows,
allowing automated execution of workflows with proper error handling
and configuration management.
"""
import os
import io
import re
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from agents.email_monitor import EmailMonitor
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import pytz



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CandidateProfile:
    """Structured representation of a parsed candidate profile.
    
    Attributes:
        name: Candidate full name, if detected
        email: Candidate email address, if detected
        phone: Candidate phone number, if detected
        skills: List of identified skills
        experience: Parsed years of experience
        education: Educational background info
        resume_text: Full text extracted from resume
        status: Current candidate status (e.g., "New", "Screened", "Interviewed")
    """
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    resume_text: Optional[str] = None
    status: str = "New"

class AutomationAgent:
    
    # OAuth2 scopes required for Google API access
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/gmail.readonly'
    ]
    
    def __init__(self):
        """Initialize the AutomationAgent with required services and configurations."""
        try:
            # Get Gmail Auth Config and Connected Account IDs from environment
            self.gmail_ac_id = os.getenv('GMAIL_AUTH_CONFIG_ID')
            self.gmail_ca_id = os.getenv('GMAIL_CONNECTED_ACCOUNT_ID')
            self.gmail_pg_id = os.getenv('PROJECT_ID')
            
            # Initialize Google services and store credentials
            self._initialize_google_services()
            
            logger.info("AutomationAgent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AutomationAgent: {str(e)}")
            raise
    
    def _initialize_google_services(self):
        """Initialize Google Calendar and Sheets services with OAuth2 credentials."""
        try:
            creds = None
            
            # Check if token.json exists with stored credentials
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
            
            # If credentials don't exist or are invalid, run OAuth2 flow
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', self.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for future use
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            # Store credentials for reuse
            self.creds = creds
            
            # Build Google API services with valid credentials
            self.calendar_service = build('calendar', 'v3', credentials=creds)
            self.sheets_service = build('sheets', 'v4', credentials=creds)
            
            logger.info("Google services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google services: {str(e)}")
            raise
    
    def parse_gmail_resumes(self, days_back: int = 7) -> List[CandidateProfile]:
        """Parse candidate resumes from Gmail emails.
        
        Args:
            days_back: Number of days to look back for emails (default: 7)
        
        Returns:
            List of parsed CandidateProfile objects
        """
        try:
            # Initialize EmailMonitor with OAuth credentials
            email_monitor = EmailMonitor(
                auth_config_id=self.gmail_ac_id,
                connected_account_id=self.gmail_ca_id,
                project_id=self.gmail_pg_id,
                creds=self.creds  # Pass prebuilt credentials
            )
            
            # Fetch resume emails from Gmail
            resume_emails = email_monitor.fetch_resume_emails(days_back=days_back)
            
            if not resume_emails:
                logger.info("No resume emails found in the specified time period")
                return []
            
            logger.info(f"Found {len(resume_emails)} resume emails")
            
            # Parse each email into a CandidateProfile
            candidates = []
            for email_data in resume_emails:
                try:
                    candidate = self._parse_single_candidate(email_data)
                    if candidate:
                        candidates.append(candidate)
                except Exception as e:
                    logger.error(f"Error parsing candidate email {email_data.get('sender_email', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Successfully parsed {len(candidates)} candidate profiles")
            return candidates
        
        except Exception as e:
            logger.error(f"Error in parse_gmail_resumes: {str(e)}")
            return []
    
    def _parse_single_candidate(self, email_data: Dict[str, Any]) -> Optional[CandidateProfile]:
        """Parse a single email into a CandidateProfile.
        
        Args:
            email_data: Dictionary containing email information
        
        Returns:
            CandidateProfile object or None if parsing fails
        """
        try:
            # Extract basic info from email
            name = email_data.get('sender_name', 'Unknown')
            email = email_data.get('sender_email', '')
            
            # Extract skills, experience, etc. from email body/attachments
            # This is a simplified version - you'd want more sophisticated parsing
            resume_text = email_data.get('subject', '') + ' ' + email_data.get('snippet', '')
            
            candidate = CandidateProfile(
                name=name,
                email=email,
                resume_text=resume_text,
                status="New"
            )
            
            return candidate
        
        except Exception as e:
            logger.error(f"Error parsing candidate data: {str(e)}")
            return None
    
    def schedule_interview_in_calendar(
        self, 
        candidate_name: str, 
        candidate_email: str, 
        interview_date: str,
        duration_minutes: int = 60
    ) -> Dict[str, Any]:
        """Schedule an interview in Google Calendar.
        
        Args:
            candidate_name: Name of the candidate
            candidate_email: Email address of the candidate
            interview_date: Interview date/time in ISO format
            duration_minutes: Duration of interview in minutes (default: 60)
        
        Returns:
            Dictionary with scheduling result
        """
        try:
            # Use prebuilt calendar service
            start_time = datetime.fromisoformat(interview_date.replace('Z', '+00:00'))
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            event = {
                'summary': f'Interview with {candidate_name}',
                'description': f'Interview scheduled with candidate {candidate_name}',
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': [
                    {'email': candidate_email},
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }
            
            # Use self.calendar_service directly - no need to rebuild
            event_result = self.calendar_service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'
            ).execute()
            
            logger.info(f"Interview scheduled for {candidate_name}: {event_result.get('htmlLink')}")
            return {
                'success': True,
                'event_id': event_result.get('id'),
                'event_link': event_result.get('htmlLink')
            }
        
        except Exception as e:
            logger.error(f"Error scheduling interview: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_candidate_in_sheet(
        self,
        candidate_name: str,
        candidate_email: str,
        status: str = "New",
        interview_date: str = "",
        spreadsheet_id: Optional[str] = None,
        tab_name: str = "Candidates"
    ) -> Dict[str, Any]:
        """Update or add candidate information in Google Sheets.
        
        Args:
            candidate_name: Name of the candidate
            candidate_email: Email address of the candidate
            status: Current status of the candidate
            interview_date: Scheduled interview date (if any)
            spreadsheet_id: ID of the Google Sheet (uses env var if not provided)
            tab_name: Name of the sheet tab (default: "Candidates")
        
        Returns:
            Dictionary with update result
        """
        try:
            # Use prebuilt sheets service
            if not spreadsheet_id:
                spreadsheet_id = os.getenv('SPREADSHEET_ID')
            
            if not spreadsheet_id:
                raise ValueError("No spreadsheet ID provided or found in environment")
            
            # Get existing data to check if candidate already exists
            range_name = f'{tab_name}!A:G'
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            # Prepare new row data
            new_row = [
                candidate_name,
                candidate_email,
                '',  # Phone (empty for now)
                '',  # Resume link (empty for now)
                status,
                interview_date,
                f'Auto-updated at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            ]
            
            # Check if candidate already exists
            candidate_row = None
            for idx, row in enumerate(values[1:], start=2):  # Skip header row
                if len(row) > 1 and row[1] == candidate_email:
                    candidate_row = idx
                    break
            
            if candidate_row:
                # Update existing row
                update_range = f'{tab_name}!A{candidate_row}:G{candidate_row}'
                body = {'values': [new_row]}
                self.sheets_service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=update_range,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                logger.info(f"Updated existing candidate {candidate_name} in row {candidate_row}")
            else:
                # Append new row
                append_range = f'{tab_name}!A:G'
                body = {'values': [new_row]}
                self.sheets_service.spreadsheets().values().append(
                    spreadsheetId=spreadsheet_id,
                    range=append_range,
                    valueInputOption='RAW',
                    insertDataOption='INSERT_ROWS',
                    body=body
                ).execute()
                logger.info(f"Added new candidate {candidate_name} to sheet")
            
            return {
                'success': True,
                'action': 'updated' if candidate_row else 'added',
                'row': candidate_row if candidate_row else len(values) + 1
            }
        
        except Exception as e:
            logger.error(f"Error updating candidate in sheet: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
