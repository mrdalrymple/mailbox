from pathlib import Path

from libmailcd.constants import LOCAL_MB_ROOT
from libmailcd.constants import LOCAL_ENV_DIRNAME
from libmailcd.constants import LOCAL_OUTBOX_DIRNAME
from libmailcd.constants import LOCAL_INBOX_DIRNAME
from libmailcd.constants import LOCAL_MB_LOGS_BUILD_DIRNAME
from libmailcd.constants import LOCAL_MB_LOGS_ROOT_DIRNAME

from libmailcd.cli.common.constants import INSOURCE_PIPELINE_FILENAME


class Env:
    def __init__(self, root):
        self._root = root

    @property
    def root(self):
        return self._root

class Outbox:
    def __init__(self, root):
        self._root = root

    @property
    def root(self):
        return self._root

class Inbox:
    def __init__(self, root):
        self._root = root

    @property
    def root(self):
        return self._root

class Logs:
    def __init__(self, root):
        self._root = root

    @property
    def root(self):
        return self._root

    @property
    def builds(self):
        return Path(self._root, LOCAL_MB_LOGS_BUILD_DIRNAME)


class Layout:
    # TODO(Matthew): Eventually refactor this to not use api, just root
    def __init__(self, workspace, api):
        self._workspace = workspace # this complicates this pattern -- should remove workspace concept from this level
        self._root = Path(workspace, LOCAL_MB_ROOT) # should higher-level pass this in? (I think yes)
        self._api = api

    @property
    def root(self):
        return self._root

    @property
    def pipeline(self): # this case complicates this pattern (if we want to get rid of workspace from here)
        return Path(self._workspace, INSOURCE_PIPELINE_FILENAME)

    @property
    def env(self):
        return Env(Path(self._root, LOCAL_ENV_DIRNAME))

    @property
    def inbox(self):
        return Inbox(Path(self._root, LOCAL_INBOX_DIRNAME))

    @property
    def outbox(self):
        return Outbox(Path(self._root, LOCAL_OUTBOX_DIRNAME))

    @property
    def logs(self):
        return Logs(Path(self._root, LOCAL_MB_LOGS_ROOT_DIRNAME))
