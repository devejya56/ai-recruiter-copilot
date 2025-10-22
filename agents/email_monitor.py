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
    
    def __init__(self, email_service=None, auth_config_id=None, connected_account_id=None):
        self.email_service = email_service
        self.auth_config_id = auth_config_id
        self.connected_account_id = connected_account_id
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
        """
