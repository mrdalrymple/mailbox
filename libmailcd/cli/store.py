import sys
from pathlib import Path

import click

from libmailcd.cli.main import main
from libmailcd.constants import LOCAL_INBOX_DIRNAME
import libmailcd.storage

########################################

@main.group("store")
@click.pass_context
def main_store(ctx):
    pass

@main_store.command("add")
@click.argument("storage_id")
@click.argument("package", type=click.Path(exists=True))  # can be zip or directory
@click.pass_obj
def main_store_add(obj, storage_id, package):
    """Add a PACKAGE (directory or zip file) to a specified location (STORAGE_ID).

    Example(s):

        mb store add MYPACKAGE ./mypackage_v2.zip

        mb store add MYPACKAGE ./mypackage_v3/

    """
    api = obj["api"]

    package_hash = api.store_add(storage_id, package)
    # TODO(matthew): we need the package hash here does storage.add return that?
    print(f"Package added under store '{storage_id}' ({package_hash})")

# TODO:(matthew) handle the output
@main_store.command("ls")
@click.argument("ref", default=None, required=False)
@click.option("--label")
@click.pass_obj
def main_store_ls(obj, ref, label):
    """Navigate around the package store.
    """
    api = obj["api"]

    # Case: mb store
    #  Should show list of all storage IDs
    if not ref:
        storage_ids = api.store_get()

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
        versions = api.store_get(sid)
        for version in versions:
            labels = api.store_get_labels(storage_id, version)
            labels_string = ",".join(labels)
            print(f"{version}\t{labels_string}")

        if not versions:
            print(f"{sid} - No entries")
        sys.exit(0)
    
    # Case: mb store SID/2de
    #  Should list the contents of the zip file
    #  Should show package metadata
    # Case: mb store SID/2de/...
    #  Should keep navigating through the zip file
    if storage_id and partial_package_hash:
        # fully qualify the ref
        try:
            package_hash = api.store_fully_qualify_package(storage_id, partial_package_hash)
        except ValueError as e:
            # Case: mb store SID/2de -- has more than one result
            #  Should stop here and list all found matches
            print(f"{e}")
            matches = api.store_find_matches(storage_id, partial_package_hash)
            for m in matches:
                print(f"{m}")
            sys.exit(0)

        # Add any label specified
        if label:
            try:
                api.store_label(storage_id, package_hash, label)
                print(f"Label '{label}' added successfully...\n")
            except ValueError as e:
                # Currently: Ignore if label already exists
                # Should we: Uncomment below if we want to let user know that
                #print(f"{e}")
                pass

        # get contents of the package
        package_fileinfos = api.store_ls(storage_id, package_hash)
        # get metadata of the package
        package_labels = api.store_get_labels(storage_id, package_hash)

        # list the metadata (labels)
        print(f"Metadata")
        print(f"====================\n")
        print(f"Storage ID:   {storage_id}")
        print(f"Package Hash: {package_hash}")
        print("Labels:")
        if package_labels:
            for label in package_labels:
                print(f"              {label}")
        else:
            print("No labels.")
        
        # list the contents of the package
        # TODO(matthew): Clean up the output of this, it's not well aligned or easy to view
        print(f"")
        print(f"Contents")
        print(f"====================\n")
        if package_fileinfos:
            print("{0:20}\t{1:20}".format("File Name", "Stats"))
        for fileinfo in package_fileinfos:
            to_show = fileinfo.copy()
            if 'name' in to_show:
                del to_show['name']
            filepath = str(fileinfo['name'])
            print("{0:20}\t{1:20}".format(filepath, str(to_show)))

@main_store.command("get")
@click.argument("ref")
@click.argument("labels", nargs=-1)
@click.pass_obj
def main_store_get(obj, ref, labels):
    """Get a PACKAGE from the specified REF, that have any of the specified LABELS.

    Example(s):

        mb store get MYPACKAGE/2de

        mb store get MYPACKAGE best version ever

    """
    api = obj["api"]

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
            package_hash = api.store_fully_qualify_package(storage_id, partial_package_hash)
        except ValueError as e:
            # Case: mb store get SID/2de -- has more than one result
            #  Should stop here and list all found matches
            print(f"{e}")
            matches = api.store_find_matches(storage_id, partial_package_hash)
            for m in matches:
                print(f"{m}")
            sys.exit(0)

        # need a current workspace (cwd)
        # calculate target directory
        target_relpath = Path(api.settings("local_root_relative"), LOCAL_INBOX_DIRNAME, storage_id, package_hash)
        target_path = Path(api.settings("workspace"), target_relpath)

        # find package
        api.store_download(storage_id, package_hash, target_path)
        print(f"Package downloaded: '{target_relpath}'")
    elif labels:
        matches = api.store_find(storage_id, labels)
        if len(matches) > 1:
            print(f"Many matches found for given labels: {labels}")
            for m in matches:
                m_labels = api.store_get_labels(storage_id, m)
                print(f"{m}")
                for l in m_labels:
                    print(f"-{l}")
            sys.exit(0)
        if len(matches) == 0:
            print(f"Nothing found matching labels: {labels}")
            sys.exit(0)

        package_hash = matches[0]

        target_relpath = Path(api.settings("local_root_relative"), LOCAL_INBOX_DIRNAME, storage_id, package_hash)
        target_path = Path(api.settings("workspace"), target_relpath)
        api.store_download(storage_id, package_hash, target_path)
        print(f"Package downloaded: '{target_relpath}'")
    # Case: no package hash, no labels, what do? Error?
    else:
        pass
