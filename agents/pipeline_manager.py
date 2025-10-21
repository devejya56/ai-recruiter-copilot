from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv()

class PipelineManager:
    """
    Orchestrates and manages the recruitment workflow pipeline (with Notion integration).
    """
    def __init__(self):
        self.notion_token = os.getenv("NOTION_TOKEN")
        self.notion_db_id = os.getenv("NOTION_DATABASE_ID")
        if not self.notion_token or not self.notion_db_id:
            raise ValueError("Missing Notion credentials in .env")
        self.notion = Client(auth=self.notion_token)
        self.active_pipelines = {}

    def start_pipeline(self, pipeline_id, agent_flow):
        self.active_pipelines[pipeline_id] = agent_flow
        print(f"Pipeline {pipeline_id} started.")

    def get_pipeline(self, pipeline_id):
        return self.active_pipelines.get(pipeline_id)

    def stop_pipeline(self, pipeline_id):
        if pipeline_id in self.active_pipelines:
            del self.active_pipelines[pipeline_id]
            print(f"Pipeline {pipeline_id} stopped.")
        else:
            print(f"Pipeline {pipeline_id} not found.")

    def add_candidate_to_notion(self, candidate):
        try:
            result = self.notion.pages.create(
                parent={"database_id": self.notion_db_id},
                properties={
                    "Name": {"title": [{"text": {"content": candidate.get("name", "")}}]},
                    "Email": {"email": candidate.get("email", "")},
                    # Add more fields as needed
                }
            )
            print(f"Candidate '{candidate.get('name')}' added to Notion.")
            return result
        except Exception as e:
            print(f"Error adding candidate to Notion: {e}")
            return None
