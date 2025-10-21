class EmailMonitor:
    """
    Monitors and processes candidate communication via email.
    """
    def __init__(self, email_service=None):
        self.email_service = email_service

    def fetch_emails(self, candidate_id):
        if not self.email_service:
            print("No email service provided. Returning dummy emails.")
            return [{"id": "email1", "body": "Welcome candidate."}]
        try:
            emails = self.email_service.get_emails(candidate_id)
            return emails
        except Exception as e:
            print(f"Failed to fetch emails: {e}")
            return []
