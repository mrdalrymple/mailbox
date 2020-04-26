from abc import ABC

from libmailcd.constants import *

import libmailcd.storage
import libmailcd.env

from pathlib import Path


class API(ABC):
    def __init__(self, settings):
        self.settings = settings
        pass

    def store_add(self, storage_id, package):
        package_hash = libmailcd.storage.add(storage_id, package)
        return package_hash

    def store_get(self, storage_id=None):
        files = libmailcd.storage.get(storage_id)
        return files

    def store_get_labels(self, storage_id, version):
        labels = libmailcd.storage.get_labels(storage_id, version)
        return labels

    def store_label(self, storage_id, package_hash, label):
        libmailcd.storage.label(storage_id, package_hash, label)

    def store_fully_qualify_package(self, storage_id, partial_package_hash):
        package_hash = libmailcd.storage.get_fully_qualified_package_hash(
            storage_id,
            partial_package_hash
        )
        return package_hash

    def store_find(self, storage_id, labels):
        matches = libmailcd.storage.find(storage_id, labels)
        return matches

    def store_find_matches(self, storage_id, partial_package_hash):
        matches = libmailcd.storage.get_package_hash_matches(storage_id, partial_package_hash)
        return matches

    def store_ls(self, storage_id, package_hash):
        package_fileinfos = libmailcd.storage.ls(storage_id, package_hash)
        return package_fileinfos

    def store_download(self, storage_id, package_hash, target_path):
        libmailcd.storage.download(storage_id, package_hash, target_path)

    def env_get(self, config):
        if not config:
            raise ValueError("config")

        mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
        mb_env_path = Path(self.settings.workspace, mb_env_relpath).resolve()

        config_filepath = Path(mb_env_path, config).resolve()
        if not config_filepath.exists():
            raise FileNotFoundError()

        contents = libmailcd.env.load_env_config(config_filepath)

        return contents

    def env_get_selected_config(self):
        selected_config = None

        mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
        mb_env_path = Path(self.settings.workspace, mb_env_relpath).resolve()
        selected_config = libmailcd.env.get_selected_config(mb_env_path)


        return selected_config

    def env_get_environments(self):

        mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
        mb_env_path = Path(self.settings.workspace, mb_env_relpath).resolve()

        environments = libmailcd.env.get_environments(mb_env_path)

        return environments
