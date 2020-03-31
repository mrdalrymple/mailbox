import os
import sys
import logging
import shutil
from pathlib import Path

import traceback

import click

import libmailcd.utils
import libmailcd.workflow
from libmailcd.cli.common.workflow import inbox_run
from libmailcd.cli.main import main
from libmailcd.constants import INSOURCE_PIPELINE_FILENAME, LOCAL_MB_ROOT, LOCAL_OUTBOX_DIRNAME

########################################

@main.command("build")
@click.option("--workspace", default=".")
@click.pass_obj
def main_build(api, workspace):
    exit_code = 0
    arg_workspace = Path(workspace).resolve()

    pipeline_filepath = Path(arg_workspace, INSOURCE_PIPELINE_FILENAME).resolve()
    logging.debug(f"pipeline_filepath: {pipeline_filepath}")

    pipeline = libmailcd.utils.load_yaml(pipeline_filepath)
    #logging.debug(f"pipeline:\n{pipeline}")

    workspace_outbox_relpath = Path(LOCAL_MB_ROOT, LOCAL_OUTBOX_DIRNAME)
    workspace_outbox_path = Path(LOCAL_MB_ROOT, LOCAL_OUTBOX_DIRNAME).resolve()

    pipeline_inbox = None
    if 'inbox' in pipeline:
        pipeline_inbox = pipeline['inbox']
        logging.debug(f"pipeline.inbox:\n{pipeline_inbox}")

    pipeline_outbox = None
    if 'outbox' in pipeline:
        pipeline_outbox = pipeline['outbox']
        logging.debug(f"pipeline.outbox:\n{pipeline_outbox}")

    pipeline_stages = None
    if 'stages' in pipeline:
        pipeline_stages = pipeline['stages']
        logging.debug(f"pipeline.stages:\n{pipeline_stages}")

    # TODO(matthew): Should we clean up the outbox here? for now, yes...
    if workspace_outbox_path.exists():
        # TODO(matthew): what about the case where this isn't a directory?
        shutil.rmtree(workspace_outbox_path)

    try:
        env_vars = []

        #######################################
        #               INBOX                 #
        #######################################
        if pipeline_inbox:
            print(f"========== INBOX ==========")
            env_vars = inbox_run(api, arg_workspace, pipeline_inbox)
            print(f"===========================")
        #######################################


        #######################################
        #             PROCESSING              #
        #######################################

        # Run main stage:
        # for now just print env variables
        if env_vars:
            print(f"ENV:")
            for ev in env_vars:
                print(f" {ev}={os.environ[ev]}")

        if pipeline_stages:
            for stage_name in pipeline_stages:
                print(f"Stage: {stage_name}")
                stage = pipeline_stages[stage_name]

                if 'steps' in stage:
                    stage_steps = stage['steps']

                    for step in stage_steps:
                        print(f"{stage_name}: {step}")
                        os.system(step)

        #######################################


        #######################################
        #               OUTBOX                #
        #######################################

        if pipeline_outbox:
            packages_to_upload = [] # all packages that need to be uploaded
            files_to_copy = [] # all the file copy rules

            for storage_id in pipeline_outbox:
                logging.debug(f"{storage_id}")
                rules = pipeline_outbox[storage_id]
                logging.debug(f"rules={rules}")
                root_path = arg_workspace

                target_relpath = Path(LOCAL_MB_ROOT, LOCAL_OUTBOX_DIRNAME, storage_id)
                target_path = Path(arg_workspace, target_relpath)

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

            print(f"========== OUTBOX ==========")
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
        traceback.print_exc()
        exit_code = 3

    sys.exit(exit_code)
