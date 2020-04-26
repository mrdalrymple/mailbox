
from pathlib import Path

class Settings():
    def __init__(self, workspace):
        self.workspace = Path(workspace).resolve()
