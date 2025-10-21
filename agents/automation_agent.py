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
    providing a clean interface to trigger workflows with input data.
    It manages API authentication and provides robust error handling.

    It also includes helper methods for multi-app orchestration such as
    scheduling interviews on Calendar and updating candidate records in
    Google Sheets via Composio.
    """

    def __init__(self):
        self.auth_config_id = os.getenv("COMPOSIO_AUTH_CONFIG_ID")
        self.connected_account_id = os.getenv("COMPOSIO_CONNECTED_ACCOUNT_ID")

        # Calendar auth IDs (with provided defaults)
        self.calendar_ac_id = os.getenv("CALENDAR_AC_ID", "ac_1yKLf7OF2IUO")
        self.calendar_ca_id = os.getenv("CALENDAR_CA_ID", "ca_E7xe6Jp2R_yR")
        self.calendar_pg_id = os.getenv("CALENDAR_PG_ID", "pg-test-1fa290b1-5b25-4c36-92ef-f2ec447cd721")

        # Sheets auth IDs (with provided defaults)
        self.sheets_ac_id = os.getenv("SHEETS_AC_ID", "ac_9l1YOPV1YGgz")
        self.sheets_ca_id = os.getenv("SHEETS_CA_ID", "ca_xbZ9WD5rHO1Y")
        self.sheets_pg_id = os.getenv("SHEETS_PG_ID", "pg-test-1fa290b1-5b25-4c36-92ef-f2ec447cd721")

        # Sheet and calendar configs
        self.sheets_spreadsheet_id = os.getenv("SHEETS_SPREADSHEET_ID")
        self.sheets_tab_name = os.getenv("SHEETS_TAB_NAME", "Candidates")
        self.calendar_primary_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
        self.default_interview_duration_minutes = int(os.getenv("DEFAULT_INTERVIEW_DURATION_MIN", "45"))
        self.timezone = os.getenv("DEFAULT_TIMEZONE", "UTC")

        self._composio_client = None

    def _get_composio_client(self):
        if self._composio_client is None:
            try:
                from composio import Composio
                self._composio_client = Composio()
            except Exception as e:
                logger.error(f"Failed to initialize Composio client: {e}")
                raise
        return self._composio_client

    def schedule_interview_in_calendar(self, candidate: Dict[str, Any], interviewer: Dict[str, Any], datetime_obj: datetime) -> Dict[str, Any]:
        """Schedule an interview event in Google Calendar using Composio.

        - Auth: uses CALENDAR_AC_ID, CALENDAR_CA_ID, CALENDAR_PG_ID from env.
        - Returns event details from provider on success.
        - Raises ValueError for bad inputs and RuntimeError for provider/SDK failures.
        """
        if not candidate or not interviewer:
            raise ValueError("candidate and interviewer are required")
        if not candidate.get("email") or not interviewer.get("email"):
            raise ValueError("candidate.email and interviewer.email are required")

        try:
            start_dt = datetime_obj
            if start_dt.tzinfo is None:
                import pytz
                start_dt = pytz.timezone(self.timezone).localize(start_dt)
            end_dt = start_dt + timedelta(minutes=self.default_interview_duration_minutes)
        except Exception as e:
            raise ValueError(f"Invalid datetime provided: {e}")

        title = f"Interview: {candidate.get('name') or candidate.get('email')} x {interviewer.get('name') or interviewer.get('email')}"
        description = (
            f"Interview between {candidate.get('name') or candidate.get('email')} and {interviewer.get('name') or interviewer.get('email')}\n"
            f"Created by AutomationAgent via Composio."
        )
        attendees = [
            {"email": candidate.get("email"), "displayName": candidate.get("name")},
            {"email": interviewer.get("email"), "displayName": interviewer.get("name")},
        ]
        body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": self.timezone},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": self.timezone},
            "attendees": attendees,
            "conferenceData": {"createRequest": {"requestId": f"req-{int(start_dt.timestamp())}"}},
        }

        client = self._get_composio_client()
        try:
            resp = client.execute(
                provider="google_calendar",
                tool_name="calendar_events_insert",
                input_params={
                    "calendarId": self.calendar_primary_id,
                    "body": body,
                    "sendUpdates": "all",
                    "conferenceDataVersion": 1,
                },
                auth_config_id=self.calendar_ac_id,
                connected_account_id=self.calendar_ca_id,
                project_id=self.calendar_pg_id,
            )
        except Exception as e:
            logger.error(f"Failed to create calendar event via Composio: {e}")
            raise RuntimeError("Calendar scheduling failed")

        event = resp.get("result", resp) if isinstance(resp, dict) else resp
        logger.info("Scheduled interview event: %s", json.dumps(event, default=str))
        return event

    def update_candidate_in_sheet(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert candidate in Google Sheets using Composio.

        - Looks up candidate by Email column in the configured tab.
        - Updates row if found; appends new if not found.
        - Auth: uses SHEETS_AC_ID, SHEETS_CA_ID, SHEETS_PG_ID from env.
        - Requires SHEETS_SPREADSHEET_ID and optionally SHEETS_TAB_NAME.
        """
        if not candidate or not candidate.get("email"):
            raise ValueError("candidate.email is required")
        if not self.sheets_spreadsheet_id:
            raise ValueError("SHEETS_SPREADSHEET_ID must be set in environment")

        email = candidate.get("email")
        columns = [
            "Email", "Name", "Phone", "Interview Status", "Last Updated", "Source Email Id", "Attachment Name", "Filetype"
        ]

        def row_from_candidate(c: Dict[str, Any]) -> List[Any]:
            now_str = datetime.utcnow().isoformat()
            return [
                c.get("email"),
                c.get("name"),
                c.get("phone"),
                c.get("interview_status") or c.get("status"),
                now_str,
                c.get("source_email_id"),
                c.get("attachment_name"),
                c.get("filetype"),
            ]

        client = self._get_composio_client()

        # Read current values
        try:
            read_resp = client.execute(
                provider="google_sheets",
                tool_name="sheets_spreadsheets_values_get",
                input_params={
                    "spreadsheetId": self.sheets_spreadsheet_id,
                    "range": f"{self.sheets_tab_name}!A1:Z",
                },
                auth_config_id=self.sheets_ac_id,
                connected_account_id=self.sheets_ca_id,
                project_id=self.sheets_pg_id,
            )
        except Exception as e:
            logger.error(f"Failed reading sheet: {e}")
            raise RuntimeError("Sheets read failed")

        values = []
        payload = read_resp.get("result", read_resp) if isinstance(read_resp, dict) else read_resp
        if isinstance(payload, dict):
            values = payload.get("values") or []

        header = values[0] if values else []
        need_header = not header or header[:len(columns)] != columns

        match_index = None
        for idx, row in enumerate(values[1:] if values else []):
            if row and len(row) > 0 and isinstance(row[0], str) and row[0].strip().lower() == email.strip().lower():
                match_index = idx + 1
                break

        row_values = row_from_candidate(candidate)

        try:
            if need_header and not values:
                batch_body = {
                    "valueInputOption": "USER_ENTERED",
                    "data": [
                        {"range": f"{self.sheets_tab_name}!A1:H1", "values": [columns]},
                        {"range": f"{self.sheets_tab_name}!A2:H2", "values": [row_values]},
                    ],
                }
                write_resp = client.execute(
                    provider="google_sheets",
                    tool_name="sheets_spreadsheets_values_batchUpdate",
                    input_params={
                        "spreadsheetId": self.sheets_spreadsheet_id,
                        "body": batch_body,
                    },
                    auth_config_id=self.sheets_ac_id,
                    connected_account_id=self.sheets_ca_id,
                    project_id=self.sheets_pg_id,
                )
            elif need_header and values:
                _ = client.execute(
                    provider="google_sheets",
                    tool_name="sheets_spreadsheets_values_update",
                    input_params={
                        "spreadsheetId": self.sheets_spreadsheet_id,
                        "range": f"{self.sheets_tab_name}!A1:H1",
                        "valueInputOption": "RAW",
                        "body": {"values": [columns]},
                    },
                    auth_config_id=self.sheets_ac_id,
                    connected_account_id=self.sheets_ca_id,
                    project_id=self.sheets_pg_id,
                )
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
