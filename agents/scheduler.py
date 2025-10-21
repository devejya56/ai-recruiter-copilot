class Scheduler:
    """
    Schedules candidate interviews and notifications.
    """
    def __init__(self, calendar_service=None):
        self.calendar_service = calendar_service

    def schedule_interview(self, candidate_id, datetime_obj):
        if not self.calendar_service:
            print("No calendar service provided. Returning dummy interview confirmation.")
            return {"status": "confirmed", "datetime": str(datetime_obj)}
        try:
            confirmation = self.calendar_service.book_event(candidate_id, datetime_obj)
            return confirmation
        except Exception as e:
            print(f"Interview scheduling failed: {e}")
            return {"status": "failed", "reason": str(e)}
