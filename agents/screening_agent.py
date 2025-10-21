class ScreeningAgent:
    """
    Screens candidate profiles based on predefined criteria or rule sets.
    """
    def __init__(self, criteria=None):
        self.criteria = criteria if criteria is not None else {}

    def screen(self, candidate_profile):
        for key, expected in self.criteria.items():
            if candidate_profile.get(key) != expected:
                return False
        return True
