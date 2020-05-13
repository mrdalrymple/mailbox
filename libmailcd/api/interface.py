from abc import ABC, abstractmethod

class IAPIEvents(ABC):
    @abstractmethod
    def store_add(self, storage_id, package):
        raise NotImplementedError

    @abstractmethod
    def store_get(self, storage_id=None):
        raise NotImplementedError

    @abstractmethod
    def store_get_labels(self, storage_id, version):
        raise NotImplementedError

    @abstractmethod
    def store_label(self, storage_id, package_hash, label):
        raise NotImplementedError

    @abstractmethod
    def store_fully_qualify_package(self, storage_id, partial_package_hash):
        raise NotImplementedError

    @abstractmethod
    def store_find(self, storage_id, labels):
        raise NotImplementedError

    @abstractmethod
    def store_find_matches(self, storage_id, partial_package_hash):
        raise NotImplementedError

    @abstractmethod
    def store_ls(self, storage_id, package_hash):
        raise NotImplementedError

    @abstractmethod
    def store_download(self, storage_id, package_hash, target_path):
        raise NotImplementedError

    @abstractmethod
    def env_get(self, config):
        raise NotImplementedError

    @abstractmethod
    def env_get_selected_config(self):
        raise NotImplementedError

    @abstractmethod
    def env_get_environments(self):
        raise NotImplementedError
