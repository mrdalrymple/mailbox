# -*- coding: utf-8 -*-

import sys
import os
import argparse
from pathlib import Path, PurePath
import pprint
import click

import libmailcd
import libmailcd.storage
import libmailcd.utils

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




@click.group()
def cli():
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

@cli.group("storage", invoke_without_command=True)
@click.pass_context
def cli_storage(ctx):
    # If no subcommand specified, default to 'list'
    if ctx.invoked_subcommand is None:
        ctx.invoke(cli_storage_list)
    pass

@cli_storage.command("add")
@click.argument("sid")
@click.argument("package", type=click.Path(exists=True)) # can be zip or directory
def cli_storage_add(sid, package):
    print(f"add({sid}, {package})")
    libmailcd.storage.add(sid, package)
    pass

@cli_storage.command("list")
@click.argument("sid", default=None, required=False)
def cli_storage_list(sid):
    if sid:
        sid = sid.upper()
        versions = libmailcd.storage.get(sid)
        for version in versions:
            print(f"{version}")

        if not versions:
            print(f"{sid} - No entries")
    else:
        storage_ids = libmailcd.storage.get()

        for sid in storage_ids:
            print(f"{sid}")
        
        if not storage_ids:
            print(f"Nothing currently stored")

    pass



#mb storage label LUA/acdef
#mb storage label LUA acdef
# TODO(matthew): Look into auto completion (https://stackoverflow.com/questions/187621/how-to-make-a-python-command-line-program-autocomplete-arbitrary-things-not-int)
@cli_storage.command("label")
@click.argument("ref")
@click.argument("label", default=None, required=False)
def cli_storage_label(ref, label):
    try:
        storage_id, partial_package_hash = libmailcd.storage.split_ref(ref)
    except ValueError:
        storage_id = ref
        partial_package_hash = None
    #print(f"sid={storage_id}, pphash={partial_package_hash}")
    if storage_id and partial_package_hash:
        matches = libmailcd.storage.get_package_hash_matches(storage_id, partial_package_hash)
        if len(matches) == 1:
            package_hash = matches[0]

            if label:
                libmailcd.storage.label(storage_id, package_hash, label)
            else:
                print(f"{storage_id}/{package_hash}:")
                labels = libmailcd.storage.get_labels(storage_id, package_hash)
                if labels:
                    for label in labels:
                        print(f"  {label}")
                else:
                    print("  No labels defined")
        else:
            print("Multiple matches found:")
            for m in matches:
                print(f"  {m}")
    elif storage_id:
        versions = libmailcd.storage.get(storage_id)
        for version in versions:
            print(f"{version}")

        if not versions:
            print(f"{storage_id} - No entries")
    pass


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
