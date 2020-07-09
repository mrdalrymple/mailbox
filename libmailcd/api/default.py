from .interface import IAPIEvents

from libmailcd.constants import LOCAL_ENV_DIRNAME
from libmailcd.constants import DEFAULT_ENV_CONFIG_NAME
from libmailcd.constants import LOCAL_MB_ROOT

import libmailcd.storage
import libmailcd.env
import libmailcd.cred

from pathlib import Path


class DefaultAPI(IAPIEvents):
    def __init__(self, settings):
        self.settings = settings
        pass

    def on_init(self):
        pass

    ########################################

    def cred_get_ids(self):
        mb_config_path = self.settings.config_root
        cred_ids = libmailcd.cred.get_ids(mb_config_path)
        return cred_ids

    # NOTE(matthew): This secrets framework just uses a KVP dict (no need to
    #  specify 'username' 'password' 'token' etc as hard-coded strings)
    def cred_set(self, cred_id, **kwargs):
        mb_config_path = self.settings.config_root
        libmailcd.cred.set_cred(mb_config_path, cred_id, **kwargs)

    def cred_unset(self, cred_id):
        mb_config_path = self.settings.config_root
        libmailcd.cred.unset_cred(mb_config_path, cred_id)

    def cred_exists(self, cred_id):
        mb_config_path = self.settings.config_root
        exists = libmailcd.cred.exists(mb_config_path, cred_id)
        return exists

    ########################################

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

    ########################################

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

    def env_create(self, config):
        mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
        mb_env_path = Path(self.settings.workspace, mb_env_relpath).resolve()
        libmailcd.env.create_config(mb_env_path, config)

    def env_delete(self, config):
        mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
        mb_env_path = Path(self.settings.workspace, mb_env_relpath).resolve()
        libmailcd.env.delete_config(mb_env_path, config)

    def env_exists(self, config):
        mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
        mb_env_path = Path(self.settings.workspace, mb_env_relpath).resolve()
        config_filepath = Path(mb_env_path, config).resolve()
        return config_filepath.exists()

    def env_is_environment(self, config):
        # TODO(matthew): is this the same as env_exists?
        mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
        mb_env_path = Path(self.settings.workspace, mb_env_relpath).resolve()
        return libmailcd.env.is_environment(mb_env_path, config)

    def env_get_default_config_name(self):
        return DEFAULT_ENV_CONFIG_NAME

    def env_get_selected_config(self):
        selected_config = None
        mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
        mb_env_path = Path(self.settings.workspace, mb_env_relpath).resolve()
        selected_config = libmailcd.env.get_selected_config(mb_env_path)
        return selected_config

    def env_set_selected_config(self, config):
        mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
        mb_env_path = Path(self.settings.workspace, mb_env_relpath).resolve()
        libmailcd.env.set_selected_config(mb_env_path, config)

    def env_get_environments(self):
        mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
        mb_env_path = Path(self.settings.workspace, mb_env_relpath).resolve()
        environments = libmailcd.env.get_environments(mb_env_path)
        return environments

    def env_valid_ref(self, ref):
        return libmailcd.env.valid_env_ref(ref)

    def env_set_variable(self, config, variable_name, variable_value):
        mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
        mb_env_path = Path(self.settings.workspace, mb_env_relpath).resolve()
        libmailcd.env.set_variable(mb_env_path, variable_name, variable_value, config)

    def env_unset_variable(self, config, variable_name):
        mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
        mb_env_path = Path(self.settings.workspace, mb_env_relpath).resolve()
        libmailcd.env.unset_variable(mb_env_path, variable_name, config)
