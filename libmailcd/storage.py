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

########################################

def load_yaml(yaml_file):
    contents = {}

    with open(yaml_file, 'r') as stream:
        try:
            contents = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    return contents

def get_artifact_storage_root():
    return STORAGE_ROOT

def get(sid=None):
    path = Path(STORAGE_ROOT)

    if sid:
        path = Path(path, sid)

    files = os.listdir(path)
    return files

def add(storage_id, package):
    # calculate hash

    dir_hash = libmailcd.utils.hash_directory(package)

    print(f"dir_hash={dir_hash}")

    # lookup hash in store
    ## return out if already exists
    if _exists(storage_id, dir_hash):
        print(f"Already exists")
        return

    # create space in store (cleanup on failure? thinking yes)
    _create(storage_id, dir_hash)

    # if directory, zip up
    # move zip to store (maybe do this with zip up step, so dont have to worry about where to temp put zip)
    _archive(storage_id, dir_hash, package)

    # TODO(matthew): What if it's some other compressed archive format?




    pass


########################################

def _archive(storage_id, dir_hash, package):
    output_filename = os.path.basename(Path(package))
    output_file_path = Path(STORAGE_ROOT, storage_id, dir_hash, output_filename)
    print(f"archiving: {output_file_path}")
    print(f"output_filename={output_filename}")
    shutil.make_archive(output_file_path, 'zip', root_dir=package)
    pass

def _exists(storage_id, dir_hash):
    pass

def _create(storage_id, dir_hash):
    # TODO(Matthew): what is an id (spec/format of one)? do I need to pass around a clean up version (like spaces to _)?
    path = Path(STORAGE_ROOT, storage_id, dir_hash)
    os.makedirs(path, exist_ok=True)
    print(f"created: {storage_id} -- {path}")


########################################
