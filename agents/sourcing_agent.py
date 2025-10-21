import os
from googleapiclient.discovery import build
from google.oauth2 import service_account

class SourcingAgent:
    """
    Sources candidates from Google Sheets using the Google Sheets API.
    """
    def __init__(self, source_api=None):
        self.source_api = source_api
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
    
    def source_candidates(self, job_description=None):
        """
        Fetches candidate entries from Google Sheets.
        
        Args:
            job_description: Optional job description for filtering (not used in basic implementation)
            
        Returns:
            List of candidate dictionaries
        """
        if not self.google_api_key:
            print("Error: GOOGLE_API_KEY not found in environment variables.")
            return []
        
        if not self.spreadsheet_id:
            print("Error: GOOGLE_SHEETS_ID not found in environment variables.")
            return []
        
        try:
            # Build the Google Sheets service using the API key
            service = build('sheets', 'v4', developerKey=self.google_api_key)
            
            # Call the Sheets API to fetch data
            sheet = service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Sheet1!A:Z'  # Adjust range as needed
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                print('No data found in the spreadsheet.')
                return []
            
            # Assume first row contains headers
            headers = values[0] if values else []
            candidates = []
            
            # Convert rows to dictionaries using headers
            for row in values[1:]:
                candidate = {}
                for i, header in enumerate(headers):
                    # Handle rows with fewer columns than headers
                    candidate[header] = row[i] if i < len(row) else ''
                candidates.append(candidate)
            
            print(f"Successfully sourced {len(candidates)} candidates from Google Sheets.")
            return candidates
            
        except Exception as e:
            print(f"Error sourcing candidates from Google Sheets: {e}")
            return []
