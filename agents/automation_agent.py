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
from dotenv import load_dotenv
from datetime import datetime, timedelta
from agents.email_monitor import EmailMonito
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import pytzr

# Load environment variables
load_dotenv()

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
        source_email_id: The Gmail message/thread identifier
        attachment_name: The original resume filename
        filetype: Attachment file extension
        raw_text_preview: First 500 chars of extracted text for debugging
        metadata: Any additional fields parsed
    """
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    source_email_id: Optional[str] = None
    attachment_name: Optional[str] = None
    filetype: Optional[str] = None
    raw_text_preview: Optional[str] = None
    metadata: Dict[str, Any] = None

class AutomationAgent:
    """Agent for triggering and managing Composio workflows.
    
    This agent handles the integration with Composio's workflow system,
    managing configuration, error handling, and workflow execution.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the automation agent.
        
        Args:
            config: Optional configuration dictionary with workflow settings
        """
        self.config = config or {}
        self.composio_api_key = os.getenv("COMPOSIO_API_KEY")
        self.sheets_spreadsheet_id = os.getenv("SHEETS_SPREADSHEET_ID")
        self.sheets_tab_name = os.getenv("SHEETS_TAB_NAME", "Candidates")
        self.sheets_ac_id = os.getenv("SHEETS_AUTH_CONFIG_ID")
        self.sheets_ca_id = os.getenv("SHEETS_CONNECTED_ACCOUNT_ID")
        self.sheets_pg_id = os.getenv("SHEETS_PROJECT_ID")
        self.gmail_ac_id = os.getenv("GMAIL_AUTH_CONFIG_ID")
        self.gmail_ca_id = os.getenv("GMAIL_CONNECTED_ACCOUNT_ID")
        self.gmail_pg_id = os.getenv("GMAIL_PROJECT_ID")
        
        if not self.composio_api_key
        
                # Initialize Google Calendar and Sheets services using OAuth2
        self.calendar_service = None
        self.sheets_service = None
        self._initialize_google_services():
            raise ValueError("COMPOSIO_API_KEY not found in environment")
        
        logger.info("AutomationAgent initialized")


        def _initialize_google_services(self):
        """Initialize Google Calendar and Sheets API services using OAuth2."""
        SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        
        creds = None
        # Load existing token if available
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # Refresh or generate new credentials if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    logger.warning("credentials.json not found. Calendar and Sheets services not initialized.")
                    return
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        try:
            # Build Calendar and Sheets services
            self.calendar_service = build('calendar', 'v3', credentials=creds)
            self.sheets_service = build('sheets', 'v4', credentials=creds)
            logger.info("Google Calendar and Sheets services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google services: {e}")
    def parse_gmail_resumes(self, days_back: int = 7) -> List[CandidateProfile]:
        """Parse resumes from Gmail using EmailMonitor.
        
        Args:
            days_back: Number of days to look back for resume emails (default: 7)
        
        Returns:
            List of CandidateProfile objects parsed from resume emails
        """
        logger.info(f"Starting Gmail resume parsing for last {days_back} days")
        
        try:
            # Initialize EmailMonitor
            email_monitor = EmailMonitor(
                auth_config_id=self.gmail_ac_id,
                connected_account_id=self.gmail_ca_id,
                project_id=self.gmail_pg_id
            )
            
            # Fetch resume emails
            candidate_data = email_monitor.fetch_resume_emails(days_back=days_back)
            
            logger.info(f"Successfully parsed {len(candidate_data)} candidates from Gmail")
            return candidate_data
            
        except Exception as e:
            logger.error(f"Failed to parse Gmail resumes: {e}")
            raise RuntimeError(f"Gmail resume parsing failed: {e}")
    
    def upsert_to_sheet(self, candidate: CandidateProfile) -> Dict[str, Any]:
        """Write or update a candidate profile in Google Sheets.
        
        Args:
            candidate: CandidateProfile object to write
        
        Returns:
            Response from the Sheets API
        """
        try:
            from composio import ComposioClient
            client = ComposioClient(api_key=self.composio_api_key)
            
            # Read existing sheet data
            read_range = f"{self.sheets_tab_name}!A2:H"
            read_resp = client.execute(
                provider="google_sheets",
                tool_name="sheets_spreadsheets_values_get",
                input_params={
                    "spreadsheetId": self.sheets_spreadsheet_id,
                    "range": read_range,
                },
                auth_config_id=self.sheets_ac_id,
                connected_account_id=self.sheets_ca_id,
                project_id=self.sheets_pg_id,
            )
            
            existing_values = read_resp.get("result", {}).get("values", [])
            
            # Prepare row values
            row_values = [
                candidate.name or "",
                candidate.email or "",
                candidate.phone or "",
                candidate.source_email_id or "",
                candidate.attachment_name or "",
                candidate.filetype or "",
                candidate.raw_text_preview or "",
                json.dumps(candidate.metadata or {}),
            ]
            
            # Check if candidate already exists (by email or source_email_id)
            match_index = None
            for i, row in enumerate(existing_values):
                if len(row) >= 4:
                    if (candidate.email and row[1] == candidate.email) or \
                       (candidate.source_email_id and row[3] == candidate.source_email_id):
                        match_index = i + 1  # +1 for header row
                        break
            
            # Update existing or append new
            if match_index is not None:
                # Update existing row
                update_range = f"{self.sheets_tab_name}!A{match_index+1}:H{match_index+1}"
                write_resp = client.execute(
                    provider="google_sheets",
                    tool_name="sheets_spreadsheets_values_update",
                    input_params={
                        "spreadsheetId": self.sheets_spreadsheet_id,
                        "range": update_range,
                        "valueInputOption": "USER_ENTERED",
                        "body": {"values": [row_values]},
                    },
                    auth_config_id=self.sheets_ac_id,
                    connected_account_id=self.sheets_ca_id,
                    project_id=self.sheets_pg_id,
                )
            else:
                if match_index is None:
                    write_resp = client.execute(
                        provider="google_sheets",
                        tool_name="sheets_spreadsheets_values_append",
                        input_params={
                            "spreadsheetId": self.sheets_spreadsheet_id,
                            "range": f"{self.sheets_tab_name}!A2:H2",
                            "valueInputOption": "USER_ENTERED",
                            "insertDataOption": "INSERT_ROWS",
                            "body": {"values": [row_values]},
                        },
                        auth_config_id=self.sheets_ac_id,
                        connected_account_id=self.sheets_ca_id,
                        project_id=self.sheets_pg_id,
                    )
                else:
                    update_range = f"{self.sheets_tab_name}!A{match_index+1}:H{match_index+1}"
                    write_resp = client.execute(
                        provider="google_sheets",
                        tool_name="sheets_spreadsheets_values_update",
                        input_params={
                            "spreadsheetId": self.sheets_spreadsheet_id,
                            "range": update_range,
                            "valueInputOption": "USER_ENTERED",
                            "body": {"values": [row_values]},
                        },
                        auth_config_id=self.sheets_ac_id,
                        connected_account_id=self.sheets_ca_id,
                        project_id=self.sheets_pg_id,
                    )
        except Exception as e:
            logger.error(f"Failed writing to sheet: {e}")
            raise RuntimeError("Sheets write failed")
        
        result = write_resp.get("result", write_resp) if isinstance(write_resp, dict) else write_resp
        logger.info("Sheet upsert result: %s", json.dumps(result, default=str))
        return result
    
    def schedule_interview_in_calendar(self, candidate_name: str, candidate_email: str, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Schedule an interview in Google Calendar."""
    try:
        # Use the same credentials from email_monitor
        if not hasattr(self.email_monitor, 'creds') or not self.email_monitor.creds:
            self.logger.error("Calendar service not initialized - OAuth credentials missing")
            return {
                'success': False,
                'error': 'OAuth credentials not available'
            }
        
        # Build calendar service
        calendar_service = build('calendar', 'v3', credentials=self.email_monitor.creds)
        
        # Schedule interview for 2 days from now at 10 AM
        local_tz = pytz.timezone('America/New_York')  # Change to your timezone
        now = datetime.now(local_tz)
        interview_time = now + timedelta(days=2)
        interview_time = interview_time.replace(hour=10, minute=0, second=0, microsecond=0)
        
        # Create event
        event = {
            'summary': f'Interview with {candidate_name}',
            'description': f'Scheduled interview with candidate: {candidate_name}\nEmail: {candidate_email}',
            'start': {
                'dateTime': interview_time.isoformat(),
                'timeZone': str(local_tz),
            },
            'end': {
                'dateTime': (interview_time + timedelta(hours=1)).isoformat(),
                'timeZone': str(local_tz),
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
        
        # Insert event
        created_event = calendar_service.events().insert(calendarId='primary', body=event).execute()
        
        self.logger.info(f"Interview scheduled for {candidate_name} at {interview_time}")
        return {
            'success': True,
            'event_id': created_event.get('id'),
            'event_link': created_event.get('htmlLink'),
            'interview_time': interview_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        self.logger.error(f"Error scheduling interview: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    def update_candidate_in_sheet(self, candidate_name: str, candidate_email: str, status: str, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update candidate status in Google Sheets."""
    try:
        # Use the same credentials from email_monitor
        if not hasattr(self.email_monitor, 'creds') or not self.email_monitor.creds:
            self.logger.error("Sheets service not initialized - OAuth credentials missing")
            return {
                'success': False,
                'error': 'OAuth credentials not available'
            }
        
        # Build sheets service
        sheets_service = build('sheets', 'v4', credentials=self.email_monitor.creds)
        
        spreadsheet_id = os.getenv('SHEETS_SPREADSHEET_ID')
        tab_name = os.getenv('SHEETS_TAB_NAME', 'Candidates')
        
        if not spreadsheet_id:
            self.logger.error("SHEETS_SPREADSHEET_ID not set in environment variables")
            return {
                'success': False,
                'error': 'SHEETS_SPREADSHEET_ID not configured'
            }
        
        # Read existing data to find if candidate exists
        range_name = f'{tab_name}!A:G'
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        # Get interview date from candidate_data if available
        interview_date = candidate_data.get('interview_time', '') if candidate_data else ''
        
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
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=update_range,
                valueInputOption='RAW',
                body=body
            ).execute()
            self.logger.info(f"Updated existing candidate {candidate_name} in row {candidate_row}")
        else:
            # Append new row
            append_range = f'{tab_name}!A:G'
            body = {'values': [new_row]}
            sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=append_range,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            self.logger.info(f"Added new candidate {candidate_name} to sheet")
        
        return {
            'success': True,
            'action': 'updated' if candidate_row else 'added',
            'row': candidate_row if candidate_row else len(values) + 1
        }
        
    except Exception as e:
        self.logger.error(f"Error updating candidate in sheet: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
