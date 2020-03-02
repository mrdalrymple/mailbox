# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path, PurePath
import yaml
import shutil

import libmailcd.utils

########################################

INSOURCE_PIPELINE_FILENAME = 'pipeline.yml'

STORAGE_ROOT = str(Path(Path.home(), ".mailcd", "storage"))
STORAGE_DB_FILENAME = "db.yml"

########################################

def load_yaml(yaml_file):
    contents = {}

    with open(yaml_file, 'r') as stream:
        try:
            contents = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    return contents

########################################

def get_artifact_storage_root():
    return STORAGE_ROOT

########################################

def get(sid=None):
    path = Path(STORAGE_ROOT)

    if sid:
        path = Path(path, sid)

    raw_files = os.listdir(path)

    # Parse out any files that not package hashes
    # TODO(matthew): This has to be done because of the database file, is there
    #  a better spot we can put that file? Better way to filter it out?
    files = []
    for rf in raw_files:
        should_get = True
        if sid and not libmailcd.utils.is_hex(rf):
            should_get = False

        if should_get:
            files.append(rf)

    return files

def add(storage_id, package):
    # calculate hash

    # Directory vs Zip file
    # TODO(matthew): This looks like it could be refactored for code re-use here
    if os.path.isdir(package):
        package_hash = libmailcd.utils.hash_directory(package)
        print(f"package_hash={package_hash}")
        # lookup hash in store
        ## return out if already exists
        if _exists(storage_id, package_hash):
            print(f"Already exists")
            return
        # create space in store (cleanup on failure? thinking yes)
        _create(storage_id, package_hash)

        # if directory, zip up
        # move zip to store (maybe do this with zip up step, so dont have to worry about where to temp put zip)
        _archive(storage_id, package_hash, package)
    else:
        package_hash = libmailcd.utils.hash_file(package)
        print(f"package_hash={package_hash}")
        # lookup hash in store
        ## return out if already exists
        if _exists(storage_id, package_hash):
            print(f"Already exists")
            return
        # create space in store (cleanup on failure? thinking yes)
        _create(storage_id, package_hash)

        _save(storage_id, package_hash, package)

    # TODO(matthew): What if it's some other compressed archive format?
    pass

########################################

def ls(storage_id, package_hash, relpath = None):
    # get file for package_hash
    filepath = _get_archive(storage_id, package_hash)

    # ls file
    return libmailcd.utils.zip_ls(filepath, relpath)

########################################


def label(storage_id, package_hash, label):
    labels = get_labels(storage_id, package_hash)

    if label in labels:
        raise ValueError(f"Label '{label}' already exists")

    add_label(storage_id, package_hash, label)
    pass

def add_label(storage_id, package_hash, label):
    # TODO(matthew): Do we need to validate that storage_id exists first, or can we make the assumption it
    #  does?

    # get full package_hash
    full_package_hash = package_hash # TODO(matthew): actually get the full package hash

    # get database (db) location
    # <storage_id>/db.json
    # The reason it's not <storage_id>/<package_hash>/db.json is so that it's an easier lookup when searching
    #  for a package via a label later.
    db_file_path = Path(STORAGE_ROOT, storage_id, STORAGE_DB_FILENAME)

    db = None

    # load db if one currently exists
    
    if db_file_path.exists():
        db = libmailcd.utils.load_yaml(db_file_path)

    # handle special case where db file exists, but no contents (without this, there would be a failure)
    if not db:
        db = {}

    # add label (noop if already exists)
    # NOTE(matthew): This might be more complex than needed.  Might just need a
    #  1:1 mapping of label to package, as query by a label should return only
    #  one package.
    if not full_package_hash in db:
        db[full_package_hash] = {}
        db[full_package_hash]["labels"] = []

    if len(db[full_package_hash]["labels"]):
        db[full_package_hash]["labels"].append(label)
    else:
        db[full_package_hash]["labels"] = [ label ]

    # keep only unique labels
    db[full_package_hash]["labels"] = list(set(db[full_package_hash]["labels"]))

    # save db
    libmailcd.utils.save_yaml(db_file_path, db)
    pass

# TODO(matthew): refactor these label calls, so they use the same db code.

def get_labels(storage_id, package_hash):
    labels = []

    # get full package_hash
    full_package_hash = package_hash # TODO(matthew): actually get the full package hash

    # get database (db) location
    db_file_path = Path(STORAGE_ROOT, storage_id, STORAGE_DB_FILENAME)

    if db_file_path.exists():
        db = libmailcd.utils.load_yaml(db_file_path)
        if db:
            if full_package_hash in db:
                labels = db[full_package_hash]["labels"]

    return labels

########################################

def split_ref(ref):
    return ref.split('/')

def get_ref_matches(ref):
    matches = []
    sid, phash = split_ref(ref)
    if sid and phash:
        matches = get_package_hash_matches(sid, phash)

    return matches

def get_package_hash_matches(storage_id, partial_package_hash):
    matches = []

    full_matches = Path(STORAGE_ROOT, storage_id).glob(partial_package_hash + "*")
    for m in full_matches:
        matches.append(m.name)

    return list(matches)

# TODO(Matthew): because of the exception raise, should this logic go into the CLI as helper function there?
def get_fully_qualified_package_hash(storage_id, partial_package_hash):
    matches = libmailcd.storage.get_package_hash_matches(storage_id, partial_package_hash)
    if len(matches) != 1:
        raise ValueError(f"More than one result for: {partial_package_hash}")

    package_hash = matches[0]

    return package_hash

########################################

# Note: these methods are a layer around the actual file system structure
#  They all use STORAGE_ROOT

def _archive(storage_id, package_hash, package):
    output_filename = os.path.basename(Path(package))
    output_file_path = Path(STORAGE_ROOT, storage_id, package_hash, output_filename)
    print(f"archiving: {output_file_path}")
    #print(f"output_filename={output_filename}")
    shutil.make_archive(output_file_path, 'zip', root_dir=package)
    pass

def _save(storage_id, package_hash, package):
    output_filename = os.path.basename(Path(package))
    output_file_path = Path(STORAGE_ROOT, storage_id, package_hash, output_filename)
    shutil.copyfile(package, output_file_path)
    print(f"archiving: {output_file_path}")
    pass

def _exists(storage_id, package_hash):
    # TODO(matthew): check that at least one (zip) file exists in this directory
    path = Path(STORAGE_ROOT, storage_id, package_hash)
    return os.path.exists(path)

def _create(storage_id, package_hash):
    # TODO(Matthew): what is an id (spec/format of one)? do I need to pass around a clean up version (like spaces to _)?
    path = Path(STORAGE_ROOT, storage_id, package_hash)
    os.makedirs(path, exist_ok=True)
    print(f"created: {storage_id} -- {path}")

def _get_archive(storage_id, package_hash):
    package_root = Path(STORAGE_ROOT, storage_id, package_hash)
    # what zip exists here?
    files = os.listdir(package_root)

    # TODO(matthew): should error out if more than one file found here
    #  I don't know what to show to the user or how they would fix it, this is an interanl error
    #  where someone messed up the backend structure... we could add more logic here to find the package with
    #  the same hash and use that zip.  If multiple zips have same hash, do we just pick one? or error?
    #  We could probably just pick one... but let's see if this error ever happens in the wild!

    # For now, just return the first file found
    # TODO(matthew): what if no files found?
    return Path(package_root, files[0])


########################################
