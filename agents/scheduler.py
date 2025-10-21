import os
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

class Scheduler:
    """
    Schedules candidate interviews using Google Calendar API.
    """
    
    def __init__(self, calendar_service=None):
        self.calendar_service = calendar_service
        self.calendar_api_key = os.getenv('GOOGLE_CALENDAR_API_KEY')
        self.service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
        self.calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        
        # Initialize Google Calendar service if API key is available
        if self.calendar_api_key or self.service_account_file:
            self._init_calendar_service()
    
    def _init_calendar_service(self):
        """
        Initialize Google Calendar API service using credentials from .env
        """
        try:
            if self.service_account_file:
                # Using service account authentication
                credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_file,
                    scopes=['https://www.googleapis.com/auth/calendar']
                )
                self.calendar_service = build('calendar', 'v3', credentials=credentials)
            elif self.calendar_api_key:
                # Using API key authentication (limited functionality)
                self.calendar_service = build('calendar', 'v3', developerKey=self.calendar_api_key)
            
            print("Google Calendar service initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize Google Calendar service: {e}")
            self.calendar_service = None
    
    def schedule_interview(self, candidate_id, datetime_obj, duration_minutes=60, 
                          candidate_email=None, candidate_name=None, 
                          interviewer_email=None, description=None):
        """
        Create a calendar event for candidate interview.
        
        Args:
            candidate_id: Unique identifier for the candidate
            datetime_obj: datetime object for interview start time
            duration_minutes: Interview duration in minutes (default: 60)
            candidate_email: Email address of the candidate
            candidate_name: Name of the candidate
            interviewer_email: Email address of the interviewer
            description: Additional details about the interview
        
        Returns:
            dict: Interview confirmation with status and event details
        """
        if not self.calendar_service:
            print("No calendar service available. Returning dummy interview confirmation.")
            return {
                "status": "confirmed",
                "datetime": str(datetime_obj),
                "candidate_id": candidate_id,
                "message": "Calendar service not configured"
            }
        
        try:
            # Calculate end time
            end_time = datetime_obj + timedelta(minutes=duration_minutes)
            
            # Prepare event details
            event_summary = f"Interview: {candidate_name or f'Candidate {candidate_id}'}"
            event_description = description or f"Interview scheduled for candidate {candidate_id}"
            
            # Build attendees list
            attendees = []
            if candidate_email:
                attendees.append({'email': candidate_email})
            if interviewer_email:
                attendees.append({'email': interviewer_email})
            
            # Create event object
            event = {
                'summary': event_summary,
                'description': event_description,
                'start': {
                    'dateTime': datetime_obj.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': attendees,
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 30},  # 30 minutes before
                    ],
                },
            }
            
            # Insert event into calendar
            created_event = self.calendar_service.events().insert(
                calendarId=self.calendar_id,
                body=event,
                sendUpdates='all'  # Send email notifications to attendees
            ).execute()
            
            print(f"Interview scheduled successfully: {created_event.get('htmlLink')}")
            
            return {
                "status": "confirmed",
                "candidate_id": candidate_id,
                "datetime": str(datetime_obj),
                "duration_minutes": duration_minutes,
                "event_id": created_event['id'],
                "event_link": created_event.get('htmlLink'),
                "message": "Interview scheduled successfully"
            }
            
        except Exception as e:
            print(f"Interview scheduling failed: {e}")
            return {
                "status": "failed",
                "candidate_id": candidate_id,
                "reason": str(e)
            }
    
    def cancel_interview(self, event_id):
        """
        Cancel a scheduled interview event.
        
        Args:
            event_id: Google Calendar event ID
        
        Returns:
            dict: Cancellation status
        """
        if not self.calendar_service:
            return {"status": "failed", "reason": "Calendar service not available"}
        
        try:
            self.calendar_service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            return {
                "status": "cancelled",
                "event_id": event_id,
                "message": "Interview cancelled successfully"
            }
        except Exception as e:
            return {
                "status": "failed",
                "event_id": event_id,
                "reason": str(e)
            }
    
    def reschedule_interview(self, event_id, new_datetime, duration_minutes=60):
        """
        Reschedule an existing interview event.
        
        Args:
            event_id: Google Calendar event ID
            new_datetime: New datetime object for interview
            duration_minutes: Interview duration in minutes
        
        Returns:
            dict: Reschedule status
        """
        if not self.calendar_service:
            return {"status": "failed", "reason": "Calendar service not available"}
        
        try:
            # Get existing event
            event = self.calendar_service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Update event times
            end_time = new_datetime + timedelta(minutes=duration_minutes)
            event['start']['dateTime'] = new_datetime.isoformat()
            event['end']['dateTime'] = end_time.isoformat()
            
            # Update the event
            updated_event = self.calendar_service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            return {
                "status": "rescheduled",
                "event_id": event_id,
                "new_datetime": str(new_datetime),
                "event_link": updated_event.get('htmlLink'),
                "message": "Interview rescheduled successfully"
            }
        except Exception as e:
            return {
                "status": "failed",
                "event_id": event_id,
                "reason": str(e)
            }
