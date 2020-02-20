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

import hashlib
import os

def hash_directory(directory):
    SHAhash = hashlib.sha1()
    if not os.path.exists (directory):
        return -1

    # TODO(matthew): create file list first, then sort, then read for hashing
    #  What is the impact for packaging something with lots of files?
    for root, _, files in os.walk(directory):
        for filename in sorted(files):

            # Calculate various paths required
            reldir = os.path.relpath(root, directory)
            relfilepath = os.path.join(reldir, filename)
            filepath = os.path.join(root,filename)

            # Hash file path (relative to package root)
            relfilepath_bytes = relfilepath.encode()
            relfilepath_sha = hashlib.sha1(relfilepath_bytes)
            SHAhash.update(relfilepath_sha.digest())

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
                        SHAhash.update(digest)

    return SHAhash.hexdigest()
