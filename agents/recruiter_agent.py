class RecruiterAgent:
    """
    Coordinates end-to-end candidate journey.
    """
    def __init__(self):
        self.candidates = {}

    def add_candidate(self, candidate_profile):
        candidate_id = candidate_profile.get("id")
        if not candidate_id:
            raise ValueError("Candidate profile must contain 'id'.")
        self.candidates[candidate_id] = candidate_profile

    def get_candidate(self, candidate_id):
        return self.candidates.get(candidate_id)
