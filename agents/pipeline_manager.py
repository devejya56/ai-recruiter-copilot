class PipelineManager:
    """
    Orchestrates and manages the recruitment workflow pipeline.
    """
    def __init__(self):
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
