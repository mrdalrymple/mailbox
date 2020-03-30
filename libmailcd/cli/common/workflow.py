import os
import logging
from pathlib import Path

import libmailcd.storage
import libmailcd.errors

from libmailcd.constants import LOCAL_MB_ROOT, LOCAL_INBOX_DIRNAME

########################################

def inbox_run(workspace, pipeline_inbox):
    env_vars = []

    if pipeline_inbox:
        inbox_packages = [] # all packages
        packages_to_download = [] # all packages that need to be downloaded

        # Find required packages
        for slot in pipeline_inbox:
            logging.debug(f"{slot}")

            tag = pipeline_inbox[slot]['tag']
            logging.debug(f"tag={tag}")

            labels = tag
            storage_id = slot

            matches = libmailcd.storage.find(storage_id, labels)
            if len(matches) > 1:
                raise libmailcd.errors.StorageMultipleFound(storage_id, matches, f"multiple found in store '{storage_id}' with labels: {labels}")
            if not matches:
                raise ValueError(f"No matches found for '{storage_id}' with labels: {labels}")
            package_hash = matches[0]

            pkg = {
                "id": storage_id,
                "hash": package_hash
            }

            packages_to_download.append(pkg)
            inbox_packages.append(pkg)

        # Download all required packages
        # TODO(matthew): Do we need to optimize this to only actually download ones we don't already have
        for package in packages_to_download:
            storage_id = package['id']
            package_hash = package['hash']
            print(f"Downloading package: {storage_id}/{package_hash}")
            # need a current workspace (cwd)
            # calculate target directory
            target_relpath = Path(LOCAL_MB_ROOT, LOCAL_INBOX_DIRNAME, storage_id, package_hash)
            target_path = Path(workspace, target_relpath)

            # download to the target directory
            libmailcd.storage.download(storage_id, package_hash, target_path)
            print(f" --> '{target_relpath}'")

        # set env vars
        for package in inbox_packages:
            env_var_name = f"MB_{storage_id}_ROOT"
            env_var_value = str(target_path)
            os.environ[env_var_name] = env_var_value
            env_vars.append(env_var_name)
            logging.debug(f"SET {env_var_name}={env_var_value}")

            env_var_name = f"MB_{storage_id}_ROOT_RELPATH"
            env_var_value = str(target_relpath)
            os.environ[env_var_name] = env_var_value
            env_vars.append(env_var_name)
            logging.debug(f"SET {env_var_name}={env_var_value}")

    return env_vars

