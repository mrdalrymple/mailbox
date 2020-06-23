from .interface import IAPIEvents

from .default import DefaultAPI

class API(IAPIEvents):
    def __init__(self, default_api, custom_api=None):
        if not default_api:
            raise ValueError(f"Invalid Argument: default_api ({default_api})")

        self.default_api = default_api
        self.custom_api = custom_api

    def settings(self, key=None):
        setting = None
        if key:
            setting = getattr(self.default_api.settings, key)
        else:
            setting = self.default_api.settings
        return setting

    def on_init(self):
        if self.custom_api and hasattr(self.custom_api, 'on_init'):
            self.custom_api.on_init(self.default_api)
        else:
            self.default_api.on_init()

    def store_add(self, storage_id, package):
        package_hash = None
        if self.custom_api and hasattr(self.custom_api, 'store_add'):
            package_hash = self.custom_api.store_add(storage_id, package)
        else:
            package_hash = self.default_api.store_add(storage_id, package)
        return package_hash

    def store_get(self, storage_id=None):
        files = None
        if self.custom_api and hasattr(self.custom_api, 'store_get'):
            files = self.custom_api.store_get(storage_id)
        else:
            files = self.default_api.store_get(storage_id)
        return files

    def store_get_labels(self, storage_id, version):
        labels = None
        if self.custom_api and hasattr(self.custom_api, 'store_get_labels'):
            labels = self.custom_api.store_get_labels(storage_id, version)
        else:
            labels = self.default_api.store_get_labels(storage_id, version)
        return labels

    def store_label(self, storage_id, package_hash, label):
        if self.custom_api and hasattr(self.custom_api, 'store_label'):
            self.custom_api.store_label(storage_id, package_hash, label)
        else:
            self.default_api.store_label(storage_id, package_hash, label)

    def store_fully_qualify_package(self, storage_id, partial_package_hash):
        package_hash = None
        if self.custom_api and hasattr(self.custom_api, 'store_fully_qualify_package'):
            package_hash = self.custom_api.store_fully_qualify_package(storage_id, partial_package_hash)
        else:
            package_hash = self.default_api.store_fully_qualify_package(storage_id, partial_package_hash)
        return package_hash

    def store_find(self, storage_id, labels):
        matches = None
        if self.custom_api and hasattr(self.custom_api, 'store_find'):
            matches = self.custom_api.store_find(storage_id, labels)
        else:
            matches = self.default_api.store_find(storage_id, labels)
        return matches

    def store_find_matches(self, storage_id, partial_package_hash):
        matches = None
        if self.custom_api and hasattr(self.custom_api, 'store_find_matches'):
            matches = self.custom_api.store_find_matches(storage_id, partial_package_hash)
        else:
            matches = self.default_api.store_find_matches(storage_id, partial_package_hash)
        return matches

    def store_ls(self, storage_id, package_hash):
        package_fileinfos = None
        if self.custom_api and hasattr(self.custom_api, 'store_ls'):
            package_fileinfos = self.custom_api.store_ls(storage_id, package_hash)
        else:
            package_fileinfos = self.default_api.store_ls(storage_id, package_hash)
        return package_fileinfos

    def store_download(self, storage_id, package_hash, target_path):
        if self.custom_api and hasattr(self.custom_api, 'store_download'):
            self.custom_api.store_download(storage_id, package_hash, target_path)
        else:
            self.default_api.store_download(storage_id, package_hash, target_path)

    def env_get(self, config):
        contents = None
        if self.custom_api and hasattr(self.custom_api, 'env_get'):
            contents = self.custom_api.env_get(config)
        else:
            contents = self.default_api.env_get(config)
        return contents

    def env_get_selected_config(self):
        selected_config = None
        if self.custom_api and hasattr(self.custom_api, 'env_get_selected_config'):
            selected_config = self.custom_api.env_get_selected_config()
        else:
            selected_config = self.default_api.env_get_selected_config()
        return selected_config

    def env_get_environments(self):
        environments = None
        if self.custom_api and hasattr(self.custom_api, 'env_get_environments'):
            environments = self.custom_api.env_get_environments()
        else:
            environments = self.default_api.env_get_environments()
        return environments
