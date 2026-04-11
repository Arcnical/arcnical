"""
Orchestrator - coordinates L1-L4 analysis pipeline.
"""


class Orchestrator:
    """Coordinates the full analysis pipeline (L1-L4)."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def run_l1_qualification(self):
        raise NotImplementedError("Orchestrator.run_l1_qualification not yet implemented")

    def run_full_analysis(self):
        raise NotImplementedError("Orchestrator.run_full_analysis not yet implemented")
