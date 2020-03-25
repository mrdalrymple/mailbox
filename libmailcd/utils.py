# http://code.activestate.com/recipes/576973-getting-the-sha-1-or-md5-hash-of-a-directory/

# http://akiscode.com/articles/sha-1directoryhash.shtml
# Copyright (c) 2009 Stephen Akiki
# MIT License (Means you can do whatever you want with this)
#  See http://www.opensource.org/licenses/mit-license.php
# Error Codes:
#   -1 -> Directory does not exist
#   -2 -> General error (see stack traceback)

# NOTE: This original code was written for python2 (has bad practicies and unnecessary steps)
# TODO(matthew): sort directories/files so this is consistent across os'
#  This should be handled before shipping, but we can work with what we have for now

# https://stackoverflow.com/questions/24937495/how-can-i-calculate-a-hash-for-a-filesystem-directory-using-python

import os
import hashlib
import zipfile


def hash_file(filepath):
    content_hash = hashlib.sha1()

    if not os.path.exists(filepath):
        raise ValueError(f"File to hash doesn't exist: {filepath}")

    # Note: This is a little bit differant that hash_directory
    #  Need to check if file, as directories show up in the return file listing
    if zipfile.is_zipfile(filepath):
        with zipfile.ZipFile(filepath) as zfile:
            for afile in zfile.infolist():
                if not afile.is_dir():
                    name = afile.filename

                    # Hash file path (relative to package root)
                    relfilepath_bytes = name.encode()
                    relfilepath_sha = hashlib.sha1(relfilepath_bytes)
                    content_hash.update(relfilepath_sha.digest())

                    with zfile.open(name) as f:
                        while True:
                            buf = f.read(4096)
                            if not buf:
                                break
                            mysha = hashlib.sha1(buf)
                            content_hash.update(mysha.digest())


    return content_hash.hexdigest()

def hash_directory(directory):
    content_hash = hashlib.sha1()

    if not os.path.exists(directory):
        raise ValueError(f"Directory to hash doesn't exist: {directory}")

    # TODO(matthew): create file list first, then sort, then read for hashing
    #  What is the impact for packaging something with lots of files?
    for root, _, files in os.walk(directory):
        for filename in sorted(files):

            # Calculate various paths required
            reldir = os.path.relpath(root, directory)
            relfilepath = os.path.join(reldir, filename)
            filepath = os.path.join(root,filename)

            # Hash file path (relative to package root)
            relfilepath = relfilepath.replace('\\', '/') # make sure file separator is consistent across os'
            relfilepath_bytes = relfilepath.encode()
            relfilepath_sha = hashlib.sha1(relfilepath_bytes)
            content_hash.update(relfilepath_sha.digest())

            # Hash file contents
            if os.path.isfile(filepath):
                with open(filepath, 'rb') as f:
                    while True:
                        # Read file in as little chunks
                        buf = f.read(4096)
                        if not buf:
                            break
                        mysha = hashlib.sha1(buf)

                        digest = mysha.digest()
                        content_hash.update(digest)

    return content_hash.hexdigest()

########################################

# TODO(matthew): filter down based on relpath, currently lists all files (using path)
#  Maybe current way is what we want... unless zip file has many files
#  What would that threshold be? i.e. if more than 10 files, only show what's in topdir
#   unless relpath specified? Then turn it into a full ls-style implementation
def zip_ls(filepath, relpath = None):
    files = []

    with zipfile.ZipFile(filepath, 'r') as zip: 
        #zip.printdir()
        #files = zip.namelist()
        infolist = zip.infolist()

    for fileinfo in infolist:
        files.append({
            "name" : fileinfo.filename,
            "size" : fileinfo.file_size
        })

    return files

def zip_extract(filepath, target_path):
    with zipfile.ZipFile(filepath, 'r') as zip_ref:
        zip_ref.extractall(target_path)

########################################

import re

def is_hex(s):
    return re.fullmatch(r"^[0-9a-fA-F]+$", s or "") is not None

########################################

import yaml

def load_yaml(yaml_file):
    contents = {}

    with open(yaml_file, 'r') as stream:
        try:
            contents = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    return contents

def save_yaml(yaml_file, data):
    with open(yaml_file, 'w') as stream:
        yaml.dump(data, stream, default_flow_style=False)
