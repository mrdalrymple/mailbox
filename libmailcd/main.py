# -*- coding: utf-8 -*-

import sys
import os
import logging
import argparse
from pathlib import Path
import shutil

import pprint
import click

import libmailcd
import libmailcd.storage
import libmailcd.utils
import libmailcd.errors
import libmailcd.workflow

########################################

INSOURCE_PIPELINE_FILENAME = 'pipeline.yml'

########################################

def app_init(settings):
    if settings['storage_root'] is not None:
        storage_root_path = Path(settings['storage_root'])
        if not storage_root_path.exists():
            print(f"creating storage: {storage_root_path}")
            storage_root_path.mkdir(parents=True)

def log_data_structure(data, display_name = None):
    if display_name is not None:
        print(f"{display_name}:")
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(data)

########################################

def pull_artifact_by_id(config, art_id):
    sr = config['settings']['storage_root']
    artifact_path = Path(sr, art_id).resolve()
    print(f"artifact path: {artifact_path}")
    pass

########################################

def exec_inbox(config, inbox):
    print(f"Executing Inbox")
    #log_data_structure(inbox, "inbox")
    for slot in inbox:
        label = slot['label']
        print(f"slot: {label}")
        pull_artifact_by_id(config, label)
    pass

def exec_outbox(config, outbox):
    print(f"Executing Outbox")
    log_data_structure(outbox, "outbox")
    pass

def exec_steps(config, steps):
    print(f"Executing Steps")
    log_data_structure(steps, "steps")

def exec_stage(config, stage_name, stage):
    print(f"Executing Stage: {stage_name}")

    if 'inbox' in stage:
        inbox = stage['inbox']
        exec_inbox(config, inbox)

    if 'steps' in stage:
        steps = stage['steps']
        exec_steps(config, steps)

    if 'outbox' in stage:
        outbox = stage['outbox']
        exec_outbox(config, outbox)
    pass

########################################


# TODO(matthew): enable logging and set default levels here
# TODO(matthew): see if there is a way to pass --debug and update logging
#  level here for all subcommands
@click.group()
@click.option("--debug/--no-debug", default=False, help="Show debug output")
def cli(debug):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    settings = {}
    settings['storage_root'] = libmailcd.storage.get_artifact_storage_root()

    app_init(settings)
    pass

@cli.group("store")
@click.pass_context
def cli_store(ctx):
    pass

@cli_store.command("add")
@click.argument("storage_id")
@click.argument("package", type=click.Path(exists=True))  # can be zip or directory
def cli_store_add(storage_id, package):
    """Add a PACKAGE (directory or zip file) to a specified location (STORAGE_ID).

    Example(s):

        mb store add MYPACKAGE ./mypackage_v2.zip

        mb store add MYPACKAGE ./mypackage_v3/

    """
    package_hash = libmailcd.storage.add(storage_id, package)
    # todo(matthew): we need the package hash here does storage.add return that?
    print(f"Package added under store '{storage_id}' ({package_hash})")
    pass

# TODO:(matthew) handle the output
@cli_store.command("ls")
@click.argument("ref", default=None, required=False)
@click.option("--label")
def cli_store_ls(ref, label):
    """Navigate around the package store.
    """
    # Case: mb store
    #  Should show list of all storage IDs
    if not ref:
        storage_ids = libmailcd.storage.get()

        for sid in storage_ids:
            print(f"{sid}")
        
        if not storage_ids:
            print(f"Nothing currently stored")
        sys.exit(0)

    # split the ref
    try:
        storage_id, partial_package_hash = libmailcd.storage.split_ref(ref)
    except ValueError:
        storage_id = ref
        partial_package_hash = None

    # Case: mb store SID
    #  Should list all packages/versions for storage id
    if storage_id and not partial_package_hash:
        sid = storage_id.upper()
        versions = libmailcd.storage.get(sid)
        for version in versions:
            print(f"{version}")

        if not versions:
            print(f"{sid} - No entries")
        sys.exit(0)
        pass
    
    # Case: mb store SID/2de
    #  Should list the contents of the zip file
    #  Should show package metadata
    # Case: mb store SID/2de/...
    #  Should keep navigating through the zip file
    if storage_id and partial_package_hash:
        # fully qualify the ref
        try:
            package_hash = libmailcd.storage.get_fully_qualified_package_hash(storage_id, partial_package_hash)
        except ValueError as e:
            # Case: mb store SID/2de -- has more than one result
            #  Should stop here and list all found matches
            print(f"{e}")
            matches = libmailcd.storage.get_package_hash_matches(storage_id, partial_package_hash)
            for m in matches:
                print(f"{m}")
            sys.exit(0)

        # Add any label specified
        if label:
            try:
                libmailcd.storage.label(storage_id, package_hash, label)
                print(f"Label '{label}' added successfully...\n")
            except ValueError as e:
                # Currently: Ignore if label already exists
                # Should we: Uncomment below if we want to let user know that
                #print(f"{e}")
                pass

        # get contents of the package
        package_fileinfos = libmailcd.storage.ls(storage_id, package_hash)
        # get metadata of the package
        package_labels = libmailcd.storage.get_labels(storage_id, package_hash)

        # list the metadata (labels)
        print(f"Metadata")
        print(f"====================\n")
        print("Labels:")
        if package_labels:
            for label in package_labels:
                print(f"{label}")
        else:
            print("No labels.")
        
        # list the contents of the package
        # TODO(matthew): Clean up the output of this, it's not well aligned or easy to view
        print(f"")
        print(f"Contents")
        print(f"====================\n")
        if package_fileinfos:
            print(f"File Name\t\t\tStats")
        for fileinfo in package_fileinfos:
            to_show = fileinfo.copy()
            if 'name' in to_show:
                del to_show['name']
            print(f"{fileinfo['name']}\t\t{to_show}")
    pass

@cli_store.command("get")
@click.argument("ref")
@click.argument("labels", nargs=-1)
def cli_store_get(ref, labels):
    """Get a PACKAGE from the specified REF, that have any of the specified LABELS.

    Example(s):

        mb store get MYPACKAGE/2de

        mb store get MYPACKAGE best version ever

    """
    try:
        storage_id, partial_package_hash = libmailcd.storage.split_ref(ref)
    except ValueError:
        storage_id = ref
        partial_package_hash = None

    # Case: Invalid storage id
    # TODO(matthew): validate storage id here... checking for not null is not correct
    if not storage_id:
        print(f"Invalid REF: {ref} (no storage id found)")
        sys.exit(1)

    # Case: storage id and package hash
    if partial_package_hash:
        # fully qualify the ref
        try:
            package_hash = libmailcd.storage.get_fully_qualified_package_hash(storage_id, partial_package_hash)
        except ValueError as e:
            # Case: mb store get SID/2de -- has more than one result
            #  Should stop here and list all found matches
            print(f"{e}")
            matches = libmailcd.storage.get_package_hash_matches(storage_id, partial_package_hash)
            for m in matches:
                print(f"{m}")
            sys.exit(0)

        # need a current workspace (cwd)
        # calculate target directory
        target_relpath = Path(".mb", "storage", storage_id, package_hash)
        target_path = Path(Path.cwd(), target_relpath)

        # find package
        libmailcd.storage.download(storage_id, package_hash, target_path)
        print(f"Package downloaded: '{target_relpath}'")
    elif labels:
        matches = libmailcd.storage.find(storage_id, labels)
        if len(matches) > 1:
            print(f"Many matches found for given labels: {labels}")
            for m in matches:
                m_labels = libmailcd.storage.get_labels(storage_id, m)
                print(f"{m}")
                for l in m_labels:
                    print(f"-{l}")
            sys.exit(0)
        if len(matches) == 0:
            print(f"Nothing found matching labels: {labels}")
            sys.exit(0)

        package_hash = matches[0]

        target_relpath = Path(".mb", "storage", storage_id, package_hash)
        target_path = Path(Path.cwd(), target_relpath)
        libmailcd.storage.download(storage_id, package_hash, target_path)
        print(f"Package downloaded: '{target_relpath}'")
    # Case: no package hash, no labels, what do? Error?
    else:
        pass

########################################

@cli.command("build")
@click.option("--project_dir", default=".")
def cli_build(project_dir):
    exit_code = 0
    arg_project_dir = Path(project_dir).resolve()

    pipeline_filepath = Path(arg_project_dir, INSOURCE_PIPELINE_FILENAME).resolve()
    logging.debug(f"pipeline_filepath: {pipeline_filepath}")

    pipeline = libmailcd.utils.load_yaml(pipeline_filepath)
    logging.debug(f"contents:\n{pipeline}")

    workspace_outbox_relpath = Path(".mb", "outbox")
    workspace_outbox_path = Path(".mb", "outbox").resolve()

    pipeline_inbox = None
    if 'inbox' in pipeline:
        pipeline_inbox = pipeline['inbox']
        logging.debug(f"contents.inbox:\n{pipeline_inbox}")

    pipeline_outbox = None
    if 'outbox' in pipeline:
        pipeline_outbox = pipeline['outbox']
        logging.debug(f"contents.outbox:\n{pipeline_outbox}")

    # TODO(matthew): Should we clean up the outbox here? for now, yes...
    if workspace_outbox_path.exists():
        # TODO(matthew): what about the case where this isn't a directory?
        shutil.rmtree(workspace_outbox_path)

    try:
        #######################################
        #               INBOX                 #
        #######################################
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

        env_vars = []

        # Download all required packages
        # TODO(matthew): Do we need to optimize this to only actually download ones we don't already have
        print(f"========== INBOX ==========")
        for package in packages_to_download:
            storage_id = package['id']
            package_hash = package['hash']
            print(f"Downloading package: {storage_id}/{package_hash}")
            # need a current workspace (cwd)
            # calculate target directory
            target_relpath = Path(".mb", "storage", storage_id, package_hash)
            target_path = Path(arg_project_dir, target_relpath)

            # download to the target directory
            libmailcd.storage.download(storage_id, package_hash, target_path)
            print(f" --> '{target_relpath}'")

        print(f"========== ===== ==========")

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

        print(f"===========================")

        #######################################


        #######################################
        #             PROCESSING              #
        #######################################

        # Run main stage:
        # for now just print env variables
        print(f"ENV:")
        for ev in env_vars:
            print(f" {ev}={os.environ[ev]}")

        #######################################


        #######################################
        #               OUTBOX                #
        #######################################

        packages_to_upload = [] # all packages that need to be uploaded
        files_to_copy = [] # all the file copy rules

        for storage_id in pipeline_outbox:
            logging.debug(f"{storage_id}")
            rules = pipeline_outbox[storage_id]
            logging.debug(f"rules={rules}")
            root_path = arg_project_dir

            target_relpath = Path(".mb", "outbox", storage_id)
            target_path = Path(arg_project_dir, target_relpath)

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
                    ffile_destination_path = Path.joinpath(target_path, destination, ffile.name)

                    # copy file (or save it to a list to be copied later)
                    files_to_copy.append(
                        libmailcd.workflow.FileCopy(ffile_source_path, ffile_destination_path)
                    )
                    pass
                pass

            # If successfully parsed all the rules for this package, mark it to be uploaded
            # TODO(matthew): need to make sure an upload of an empty directory
            #   doesnt work
            #  i.e. we add this storage id to upload, but we are not sure that any
            #   file will actually be copied into it.
            packages_to_upload.append(
                libmailcd.workflow.PackageUpload(storage_id, target_path)
            )

        print(f"========== OUTBOX ==========")
        for ftc in files_to_copy:
            print(f"Copy {ftc.src_relative} => {ftc.dst_relative}")
            os.makedirs(ftc.dst_root, exist_ok=True)
            shutil.copy(ftc.src, ftc.dst)

        print(f"========== ======= ==========")

        for ptu in packages_to_upload:
            print(f"Upload {ptu.storage_id}")
            package_hash = libmailcd.storage.add(ptu.storage_id, ptu.package_path)
            print(f" as: {package_hash}")

        print(f"=============================")

        #######################################
    except libmailcd.errors.StorageMultipleFound as e:
        print(f"Error - {e}")
        for match in e.matches:
            print(f"{match}")
        exit_code = 2
    except libmailcd.errors.StorageIdNotFoundError as e:
        print(f"{e}")
        exit_code = 1
    except Exception as e:
        print(f"{e}")
        exit_code = 3

    sys.exit(exit_code)

########################################

# NOTE(matthew): This can eventually be removed after completed ported to click.
#  Need to see where all this code fits in.
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--project_dir", dest='project_dir', default=".")
    parser.add_argument("--env_config", dest='env_config', default="enva.yml")

    args = parser.parse_args()

    #print(f"arg(project_dir)={args.project_dir}")
    #print(f"arg(env_config)={args.env_config}")

    settings = {}
    settings['storage_root'] = libmailcd.storage.get_artifact_storage_root()

    app_init(settings)

    arg_project_dir = Path(args.project_dir).resolve()
    arg_env_config = Path(args.env_config).resolve()
    
    #print(f"arg_project_dir={arg_project_dir}")
    #print(f"arg_env_config={arg_env_config}")

    env = libmailcd.utils.load_yaml(arg_env_config)

    config = {
        'settings': settings,
        'env': env
    }


    #print(f"env={env}")

    # TODO(Matthew): Make the pipeline filepath/filename configurable
    pipeline_filepath = Path(arg_project_dir, INSOURCE_PIPELINE_FILENAME).resolve()

    #print(f"pipeline_filepath={pipeline_filepath}")

    pipeline = libmailcd.utils.load_yaml(pipeline_filepath)

    #log_data_structure(pipeline)

    for stage_name in pipeline['stages'].keys():
        stage = pipeline['stages'][stage_name]
        exec_stage(config, stage_name, stage)


    return 0

########################################
