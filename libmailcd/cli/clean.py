import os
import logging
from pathlib import Path
import shutil
import sys
import traceback

import click

import libmailcd.utils
from libmailcd.constants import LOCAL_INBOX_DIRNAME
from libmailcd.constants import LOCAL_OUTBOX_DIRNAME
from libmailcd.cli.common.path_manager import *
from libmailcd.cli.main import main

########################################

@main.command("clean")
@click.option("--env", is_flag=True)
@click.pass_obj
def main_clean(obj, env):
    """Cleans the mb files in the workspace.
    
    Arguments:
        workspace {Path} -- Path to the workspace to clean.
        env {Bool} -- Clean the environment out as well.
    """
    exit_code = 0

    api = obj["api"]

    try:
        workspace = api.settings("workspace")

        layout = Layout(workspace, api)

        pipeline_filepath = layout.pipeline
        logging.debug(f"pipeline_filepath: {pipeline_filepath}")

        if not pipeline_filepath.is_file():
            raise ValueError(f"no pipeline found: {pipeline_filepath.name} ({workspace})")
        pipeline = libmailcd.utils.load_yaml(pipeline_filepath)

        pipeline_clean = None
        if 'clean' in pipeline:
            pipeline_clean = pipeline['clean']
            logging.debug(f"pipeline.clean:\n{pipeline_clean}")

        if pipeline_clean:
            root_path = workspace
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
                ffile_relpath = os.path.relpath(ffile, workspace)
                if ffile.is_dir():
                    shutil.rmtree(ffile)
                    print(f"Removed custom directory: {ffile_relpath}")
                else:
                    ffile.unlink()
                    print(f"Removed custom file: {ffile_relpath}")

        #local_mb_relpath = api.settings("local_root_relative")

        #inbox_relpath = Path(local_mb_relpath, LOCAL_INBOX_DIRNAME)
        #outbox_relpath = Path(local_mb_relpath, LOCAL_OUTBOX_DIRNAME)

        #inbox_path = Path(workspace, inbox_relpath).resolve()
        #outbox_path = Path(workspace, outbox_relpath).resolve()

        inbox_path = layout.inbox.root
        outbox_path = layout.outbox.root
        logs_path = layout.logs.root
        stages_path = layout.stages.root
        
        if inbox_path.exists():
            shutil.rmtree(inbox_path)
            print(f"Removed local storage ({inbox_path})...")

        if outbox_path.exists():
            shutil.rmtree(outbox_path)
            print(f"Removed local outbox ({outbox_path})...")

        if logs_path.exists():
            shutil.rmtree(logs_path)
            print(f"Removed local logs ({logs_path})...")

        if stages_path.exists():
            shutil.rmtree(stages_path)
            print(f"Removed local stages ({stages_path})...")

        if env:
            #env_relpath = api.settings("environment_root_relative")
            #env_path = api.settings("environment_root")
            env_path = layout.env.root
            if env_path.exists():
                shutil.rmtree(env_path)
                print(f"Removed local env ({env_path})...")
    except ValueError as e:
        print(f"{e}")
        exit_code = 4
    except Exception as e:
        print(f"{e}")
        traceback.print_exc()
        exit_code = 3

    sys.exit(exit_code)