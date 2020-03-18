import os
from pathlib import Path

class FileCopy():
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst

        # TODO(matthew): handle the case where src and dst may have wildly different common paths.
        #  Maybe that isn't supported?  If it is, we'll need to pass in the src root path and the
        #  dst root path.
        common = os.path.commonpath([src, dst])

        self.src_relative = os.path.relpath(src, common)
        self.dst_relative = os.path.relpath(dst, common)

        self.dst_root = Path(dst).parent

class PackageUpload():
    def __init__(self, storage_id, package_path):
        self.storage_id = storage_id
        self.package_path = package_path
