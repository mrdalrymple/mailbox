
class StorageIdNotFoundError(Exception):
    """Raised when the supplied storage id was not found in the store"""

    def __init__(self, storage_id, message = None):
        self.storage_id = storage_id
        if not message:
            message = f"Unknown storage_id: {storage_id}"

        # Call the base class constructor with the parameters it needs
        super(StorageIdNotFoundError, self).__init__(message)


class StorageIdValueError(ValueError):
    """Raised when the supplied storage id was not found in the store"""

    def __init__(self, storage_id, message = None):
        self.storage_id = storage_id

        # Call the base class constructor with the parameters it needs
        super(StorageIdValueError, self).__init__(message)


class StorageMultipleFound(StorageIdValueError):
    """Raised"""

    def __init__(self, storage_id, matches, message = None):
        self.matches = matches

        super(StorageMultipleFound, self).__init__(storage_id, message)