from abc import ABC

import libmailcd.storage

class API(ABC):
    def __init__(self):
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
