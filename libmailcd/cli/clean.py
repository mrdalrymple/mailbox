import os
import logging
from pathlib import Path
import shutil

import click

import libmailcd.utils
from libmailcd.constants import INSOURCE_PIPELINE_FILENAME, LOCAL_MB_ROOT, LOCAL_INBOX_DIRNAME, LOCAL_OUTBOX_DIRNAME
from libmailcd.cli.main import main

########################################

@main.command("clean")
@click.option("--workspace", default=".")
def main_clean(workspace):
    arg_workspace = Path(workspace).resolve()
    pipeline_filepath = Path(arg_workspace, INSOURCE_PIPELINE_FILENAME).resolve()

    # TODO(matthew): validate there exists a pipeline file before doing any
    #  actions that require a workspace (not just clean).  Should show an
    #  error message.
    pipeline = libmailcd.utils.load_yaml(pipeline_filepath)

    pipeline_clean = None
    if 'clean' in pipeline:
        pipeline_clean = pipeline['clean']
        logging.debug(f"pipeline.clean:\n{pipeline_clean}")

    if pipeline_clean:
        root_path = arg_workspace
        clean_rules = pipeline_clean

        # Grab all files to clean found from all rules
        files_to_clean = []
        for rule in clean_rules:
            rule = rule.strip()

            found_files = root_path.glob("**/" + rule)
            files_to_clean.extend(found_files)

        # Reduce list so it only has unique files
        # Otherwise we might try to delete the same file twice
        files_to_clean = list(set(files_to_clean))

        # Actually remove all specified files
        for ffile in files_to_clean:
            ffile_relpath = os.path.relpath(ffile, arg_workspace)
            if ffile.is_dir():
                shutil.rmtree(ffile)
                print(f"Removed custom directory: {ffile_relpath}")
            else:
                ffile.unlink()
                print(f"Removed custom file: {ffile_relpath}")

    inbox_relpath = Path(LOCAL_MB_ROOT, LOCAL_INBOX_DIRNAME)
    outbox_relpath = Path(LOCAL_MB_ROOT, LOCAL_OUTBOX_DIRNAME)

    inbox_path = Path(workspace, inbox_relpath).resolve()
    outbox_path = Path(workspace, outbox_relpath).resolve()
    
    if inbox_path.exists():
        shutil.rmtree(inbox_path)
        print(f"Removed local storage ({inbox_relpath})...")

    if outbox_path.exists():
        shutil.rmtree(outbox_path)
        print(f"Removed local outbox ({outbox_relpath})...")
