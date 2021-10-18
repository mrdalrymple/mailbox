import os
import logging
from pathlib import Path
import shutil

import libmailcd.storage
import libmailcd.errors

from libmailcd.cli.tools import agent
from libmailcd.cli.common.constants import LOG_FILE_EXTENSION

########################################

def pipeline_outbox_run(api, pipeline_outbox):
    if not pipeline_outbox:
        raise ValueError("No outbox set")

    mb_outbox_path = api.settings("outbox_root")
    root_path = api.settings("workspace")

    packages_to_upload = [] # all packages that need to be uploaded
    files_to_copy = [] # all the file copy rules

    for storage_id in pipeline_outbox:
        logging.debug(f"{storage_id}")
        rules = pipeline_outbox[storage_id]
        logging.debug(f"rules={rules}")

        target_path = Path(mb_outbox_path, storage_id)

        for rule in rules:
            source, destination = rule.split("->")
            source = source.strip()
            destination = destination.strip()
            # Support destinations starting with "/" (in Windows)
            #  and not have it think it's the root of the drive
            #  but instead the root of the output path
            # TODO(matthew): What about linux?
            if os.name == 'nt':
                destination = destination.lstrip('/\\')

            logging.debug(f"src='{source}'")
            logging.debug(f"dst='{destination}'")
            logging.debug(f"target='{target_path}'")

            # TODO(matthew): What about the case where we may want to grab
            #  something from a pulled in package?  Shouldn't always assume
            #  searching from the root_path, but how to implement this?
            # Maybe do this format:
            #   "WORKSPACE: *.txt -> /docs/"
            #   "LUA: *.dll -> /external/lua/"
            found_files = root_path.glob("**/" + source)
            for ffile in found_files:
                ffile_source_path = ffile

                # get filename
                ffilename = ffile.name

                # generate output path
                ffile_destination_path = Path.joinpath(target_path, destination, ffilename)

                # copy file (or save it to a list to be copied later)
                files_to_copy.append(
                    libmailcd.workflow.FileCopy(ffile_source_path, ffile_destination_path)
                )

        # If successfully parsed all the rules for this package, mark it to be uploaded
        # TODO(matthew): need to make sure an upload of an empty directory
        #   doesnt work
        #  i.e. we add this storage id to upload, but we are not sure that any
        #   file will actually be copied into it.
        packages_to_upload.append(
            libmailcd.workflow.PackageUpload(storage_id, target_path)
        )

    for ftc in files_to_copy:
        print(f"Copy {ftc.src_relative} => {ftc.dst_relative}")
        os.makedirs(ftc.dst_root, exist_ok=True)
        shutil.copy(ftc.src, ftc.dst)

    print(f"========== ======= ==========")

    for ptu in packages_to_upload:
        print(f"Upload {ptu.storage_id}")
        if os.path.exists(ptu.package_path):
            package_hash = api.store_add(ptu.storage_id, ptu.package_path)
            print(f" as: {package_hash}")
        else:
            print(f" nothing to store for: {ptu.storage_id} (empty)")

def pipeline_inbox_run(api, pipeline_inbox):
    if not pipeline_inbox:
        raise ValueError("No inbox set")

    env_vars = {}
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
    if packages_to_download:
        mb_inbox_relpath = api.settings("inbox_root_relative")
        mb_inbox_path = api.settings("inbox_root")

        # TODO(matthew): Do we need to optimize this to only actually download ones we don't already have
        for package in packages_to_download:
            storage_id = package['id']
            package_hash = package['hash']
            print(f"Downloading package: {storage_id}/{package_hash}")

            # calculate target directory
            target_relpath = Path(mb_inbox_relpath, storage_id, package_hash)
            target_path = Path(mb_inbox_path, target_relpath)

            # download to the target directory
            libmailcd.storage.download(storage_id, package_hash, target_path)
            print(f" --> '{target_relpath}'")

    # set env vars
    for package in inbox_packages:
        env_var_name = f"MB_{storage_id}_ROOT"
        env_var_value = str(target_path.resolve())
        env_vars[env_var_name] = env_var_value

        env_var_name = f"MB_{storage_id}_ROOT_RELPATH"
        env_var_value = str(target_relpath)
        env_vars[env_var_name] = env_var_value

    return env_vars

def pipeline_set_env(mb_inbox_env_vars, mb_env_path):
    env_vars = []
    loaded_env = []
    # Note: Order matters here! Should inbox overwrite loaded env? Or vice versa?
    # For now, we prefer loaded env over inbox env vars.  This should give users
    #  the ability to load envs that overwrite the normal behavior.  However, this
    #  case really shouldn't happen, but we should still make a decision here.
    # I haven't thought this through enough, and could be persuaded either way.

    for key, value in mb_inbox_env_vars.items():
        os.environ[key] = value

    loaded_env = libmailcd.env.get_variables(mb_env_path)
    for key, value in loaded_env.items():
        logging.debug(f"SET {key}={value}")
        os.environ[key] = value

    # Keep a list of all the variables we've set (use case? not sure yet)
    env_vars.extend(mb_inbox_env_vars.keys())
    env_vars.extend(loaded_env.keys())

    return env_vars

def _pipeline_process_stage(workspace, stage, stage_name, logfilepath):
    print(f"> Starting Stage: {stage_name}")

    if 'node' not in stage:
        raise ValueError(f"No 'node' block in stage: {stage_name}")

    node = agent.factory(stage['node'], workspace)

    logfilepath = logfilepath.resolve()
    with open(logfilepath, 'w') as logfp:
        if 'steps' in stage:
            stage_steps = stage['steps']

            with node:
                for step in stage_steps:
                    step = step.strip()
                    print(f"{stage_name}> {step}")
                    result = node.run_step(step)

                    result_output = result.stdout.strip()
                    if result_output:
                        logfp.write(result_output)
                        print(result_output)
                    print(f"?={result.returncode}")

def pipeline_stages_run(workspace, pipeline_stages, logpath):
    # TODO(Matthew): Should do a schema validation here (or up a level) first,
    #  so we can give line numbers for issues to the end user.

    for stage_name in pipeline_stages:
        stage = pipeline_stages[stage_name]
        logfilepath = Path(logpath, f"{stage_name}{LOG_FILE_EXTENSION}")
        _pipeline_process_stage(workspace, stage, stage_name, logfilepath)
