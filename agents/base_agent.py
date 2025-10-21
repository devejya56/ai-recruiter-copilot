class BaseAgent:
    """
    Base class for all AI recruitment agents. Can be extended for specific agent logic.
    """
    def __init__(self):
        pass

    def run(self, *args, **kwargs):
        print("Base agent run method called. Override in subclass.")
