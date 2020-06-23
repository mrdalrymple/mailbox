
from pathlib import Path

from libmailcd.constants import LOCAL_ENV_DIRNAME
from libmailcd.constants import LOCAL_MB_ROOT


MAILCD_CONFIG_ROOT = str(Path(Path.home(), ".mailcd"))
MAILCD_LIBRARY_ROOT = Path(MAILCD_CONFIG_ROOT, "library")


class Settings():
    def __init__(self, workspace):
        self.workspace = Path(workspace).resolve()
        self.config_root = MAILCD_CONFIG_ROOT
        self.library_root = MAILCD_LIBRARY_ROOT

        self.local_root_relative = Path(LOCAL_MB_ROOT)
        self.local_root = Path(self.workspace, self.local_root_relative).resolve()

        self.environment_root_relative = Path(self.local_root_relative, LOCAL_ENV_DIRNAME)
        self.environment_root = Path(self.local_root, LOCAL_ENV_DIRNAME).resolve()
