
from pathlib import Path

from libmailcd.constants import LOCAL_ENV_DIRNAME
from libmailcd.constants import LOCAL_MB_ROOT
from libmailcd.constants import LOCAL_OUTBOX_DIRNAME
from libmailcd.constants import LOCAL_INBOX_DIRNAME
from libmailcd.constants import LOCAL_MB_LOGS_ROOT_DIRNAME
from libmailcd.constants import LOCAL_MB_LOGS_BUILD_DIRNAME
from libmailcd.constants import LOCAL_MB_STAGE_ROOT


MAILCD_CONFIG_ROOT = str(Path(Path.home(), ".mailcd"))
MAILCD_LIBRARY_ROOT = Path(MAILCD_CONFIG_ROOT, "library")


# TODO(Matthew): What if we made all these settings the "relative" path and pushed workspace out, and handle all this at the higher level?  Would that make sense?
class Settings():
    def __init__(self, workspace):
        self.workspace = Path(workspace)
        self.config_root = MAILCD_CONFIG_ROOT
        self.library_root = MAILCD_LIBRARY_ROOT

        self.local_root_relative = Path(LOCAL_MB_ROOT)
        self.local_root = Path(self.workspace, self.local_root_relative)

        self.environment_root_relative = Path(self.local_root_relative, LOCAL_ENV_DIRNAME)
        #self.environment_root = Path(self.local_root, LOCAL_ENV_DIRNAME)

        self.inbox_root_relative = Path(self.local_root_relative, LOCAL_INBOX_DIRNAME)
        #self.inbox_root = Path(self.local_root, LOCAL_INBOX_DIRNAME)

        self.outbox_root_relative = Path(self.local_root_relative, LOCAL_OUTBOX_DIRNAME)
        #self.outbox_root = Path(self.local_root, LOCAL_OUTBOX_DIRNAME)

        self.logs_root_relative = Path(self.local_root_relative, LOCAL_MB_LOGS_ROOT_DIRNAME)
        #self.logs_root = Path(self.local_root, LOCAL_MB_LOGS_ROOT_DIRNAME)

        self.logs_build_root_relative = Path(self.logs_root_relative, LOCAL_MB_LOGS_BUILD_DIRNAME)
        #self.logs_build_root = Path(self.logs_root, LOCAL_MB_LOGS_BUILD_DIRNAME)

        self.stage_root_relative = Path(self.local_root_relative, LOCAL_MB_STAGE_ROOT)
        self.stage_root = Path(self.local_root, LOCAL_MB_STAGE_ROOT)

        self.stage_outbox_root_relative = Path(self.stage_root_relative, LOCAL_OUTBOX_DIRNAME)
        self.stage_outbox_root = Path(self.stage_root, LOCAL_OUTBOX_DIRNAME)
