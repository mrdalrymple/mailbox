from pathlib import Path

from libmailcd.constants import LOCAL_ENV_DIRNAME
from libmailcd.constants import LOCAL_OUTBOX_DIRNAME

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
    def __init__(self, root, api):
        self._root = root
        self._api = api

    @property
    def root(self):
        return self._root

    @property
    def pipeline(self):
        return Path(self._root, INSOURCE_PIPELINE_FILENAME)

    @property
    def env(self):
        return Env(Path(self._root, LOCAL_ENV_DIRNAME))


    @property
    def outbox(self):
        return Outbox(Path(self._root, LOCAL_OUTBOX_DIRNAME))

    @property
    def logs(self):
        return Logs(Path(self._root, LOCAL_MB_LOGS_ROOT))
