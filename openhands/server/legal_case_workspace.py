
from pathlib import Path

LEGAL_CASES_DIR = "/tmp/legal_workspace/cases"

class LegalCaseWorkspace:
    def __init__(self, case_id: str, base_dir: str):
        self.case_id = case_id
        self.base_dir = Path(base_dir)
        self.case_dir = self.base_dir / f"case-{self.case_id}"

    def get_workspace_path(self, relative_path: str = "") -> Path:
        return self.case_dir / relative_path

    def get_intake_path(self) -> Path:
        return self.get_workspace_path("intake")

