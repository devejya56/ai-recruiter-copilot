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
from google_auth_oauthlib.flow import InstalledAppFlowr

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
        """Schedule an interview in Google Calendar for a candidate."""
        if not self.calendar_service:
            logger.error("Calendar service not initialized")
            return {
                "success": False,
                "message": "Calendar service unavailable",
                "candidate": candidate_name
            }
            
        try:
            # Create event 3 days from now at 10 AM (1 hour duration)
            start_time = datetime.now() + timedelta(days=3)
            start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)
            
            event = {
                'summary': f'Interview with {candidate_name}',
                'description': f'Technical interview with candidate {candidate_name}\nEmail: {candidate_email}',
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
            
            event_result = self.calendar_service.events().insert(calendarId='primary', body=event).execute()
            logger.info(f"Interview scheduled for {candidate_name}: {event_result.get('htmlLink')}")
            
            return {
                "success": True,
                "message": f"Interview scheduled for {start_time.strftime('%Y-%m-%d %H:%M')}",
                "candidate": candidate_name,
                "event_link": event_result.get('htmlLink')
            }
            
        except Exception as e:
            logger.error(f"Failed to schedule interview for {candidate_name}: {e}")
            return {
                "success": False,
                "message": f"Calendar scheduling failed: {str(e)}",
                "candidate": candidate_name
            }
    def update_candidate_in_sheet(self, candidate_name: str, candidate_email: str, status: str, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update candidate status in Google Sheets."""
        if not self.sheets_service:
            logger.error("Sheets service not initialized")
            return {
                "success": False,
                "message": "Sheets service unavailable",
                "candidate": candidate_name
            }
            
        if not self.sheets_spreadsheet_id:
            logger.error("SHEETS_SPREADSHEET_ID not configured")
            return {
                "success": False,
                "message": "Spreadsheet ID not configured",
                "candidate": candidate_name
            }
            
        try:
            # Prepare row data
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            row_values = [[
                candidate_name or 'Unknown',
                candidate_email or 'No email',
                status,
                timestamp,
                candidate_data.get('phone', ''),
                candidate_data.get('source_email_id', ''),
            ]]
            
            # Append to sheet
            range_name = f"{self.sheets_tab_name}!A:F"
            body = {'values': row_values}
            
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.sheets_spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            logger.info(f"Updated sheet for {candidate_name} with status: {status}")
            return {
                "success": True,
                "message": f"Status '{status}' recorded in sheet",
                "candidate": candidate_name,
                "status": status
            }
            
        except Exception as e:
            logger.error(f"Failed to update sheet for {candidate_name}: {e}")
            return {
                "success": False,
                "message": f"Sheet update failed: {str(e)}",
                "candidate": candidate_name,
                "status": status
            }
