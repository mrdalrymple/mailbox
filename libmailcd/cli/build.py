import os
import sys
import logging
import shutil
from pathlib import Path

import traceback

import click

import libmailcd.utils
import libmailcd.workflow
import libmailcd.env
import libmailcd.pipeline
from libmailcd.cli.common.workflow import inbox_run
from libmailcd.cli.tools import agent
from libmailcd.cli.main import main
from libmailcd.constants import INSOURCE_PIPELINE_FILENAME
from libmailcd.constants import LOCAL_OUTBOX_DIRNAME

########################################

def pipeline_set_env(mb_inbox_env_vars, mb_env_path):
    env_vars = []
    loaded_env = []
    # Note: Order matters here! Should inbox overwrite loaded env? Or vice versa?
    # For now, we prefer loaded env over inbox env vars.  This should give users
    #  the ability to load envs that overwrite the normal behavior.  However, this
    #  case really shouldn't happen, but we should still make a decision here.
    # I haven't thought this through enough, and could be persuaded either way.

    for key, value in mb_inbox_env_vars.items():
        os.environ[key] = value

    loaded_env = libmailcd.env.get_variables(mb_env_path)
    for key, value in loaded_env.items():
        os.environ[key] = value

    # Keep a list of all the variables we've set (use case? not sure yet)
    env_vars.extend(mb_inbox_env_vars.keys())
    env_vars.extend(loaded_env.keys())

    return env_vars

def pipeline_process_stage(stage, stage_name):
    print(f"> Starting Stage: {stage_name}")

    if 'node' not in stage:
        raise ValueError(f"No 'node' block in stage: {stage_name}")

    node = agent.factory(stage['node'])

    if 'steps' in stage:
        stage_steps = stage['steps']

        with node:
            for step in stage_steps:
                step = step.strip()
                print(f"{stage_name}> {step}")
                result = node.run_step(step)

                print(f"?={result.returncode}")
                print(result.stdout)

def pipeline_process(env_vars, pipeline_stages):
    # TODO(Matthew): Should do a schema validation here (or up a level) first,
    #  so we can give line numbers for issues to the end user.

    # Run main stage:
    # for now just print env variables
    if env_vars:
        print(f"======= ENVIRONMENT =======")
        for ev in env_vars:
            print(f" {ev}={os.environ[ev]}")

    if pipeline_stages:
        print(f"========== STAGES ==========")
        for stage_name in pipeline_stages:
            stage = pipeline_stages[stage_name]
            pipeline_process_stage(stage, stage_name)

##########################

@main.command("build")
@click.pass_obj
def main_build(api):
    exit_code = 0

    try:
        workspace = api.settings("workspace")
        logging.debug(f"workspace: {workspace}")

        pipeline_filepath_rel = Path(workspace, INSOURCE_PIPELINE_FILENAME)
        pipeline_filepath = pipeline_filepath_rel.resolve()
        logging.debug(f"pipeline_filepath: {pipeline_filepath}")

        if not pipeline_filepath.is_file():
            raise ValueError(f"no pipeline found: {INSOURCE_PIPELINE_FILENAME} ({workspace})")

        mb_env_path = api.settings("environment_root")
        logging.debug(f"env_root: {mb_env_path}")
        mb_local_root = api.settings("local_root")
        workspace_outbox_path = Path(mb_local_root, LOCAL_OUTBOX_DIRNAME).resolve()


        pipeline_dict = libmailcd.utils.load_yaml(pipeline_filepath)
        pipeline = libmailcd.pipeline.Pipeline.from_dict(pipeline_dict)

        # TODO(matthew): Should we clean up the outbox here? for now, yes...
        if workspace_outbox_path.exists():
            # TODO(matthew): what about the case where this isn't a directory?
            shutil.rmtree(workspace_outbox_path)

        env_vars = []
        mb_inbox_env_vars = {}

        #######################################
        #               INBOX                 #
        #######################################

        if pipeline.inbox:
            print(f"========== INBOX ==========")
            mb_inbox_env_vars = inbox_run(api, workspace, pipeline.inbox)

        #######################################
        #             PROCESSING              #
        #######################################

        env_vars = pipeline_set_env(mb_inbox_env_vars, mb_env_path)

        pipeline_process(env_vars, pipeline.stages)

        #######################################
        #               OUTBOX                #
        #######################################

        if pipeline.outbox:
            packages_to_upload = [] # all packages that need to be uploaded
            files_to_copy = [] # all the file copy rules

            for storage_id in pipeline.outbox:
                logging.debug(f"{storage_id}")
                rules = pipeline.outbox[storage_id]
                logging.debug(f"rules={rules}")
                root_path = workspace

                target_path = Path(workspace_outbox_path, storage_id)

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
    except ValueError as e:
        print(f"{e}")
        exit_code = 4
    except Exception as e:
        print(f"{e}")
        traceback.print_exc()
        exit_code = 3

    sys.exit(exit_code)
