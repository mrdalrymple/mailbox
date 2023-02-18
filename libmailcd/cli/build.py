import logging
import os
from pathlib import Path
import shutil
import sys
import traceback

import click

import libmailcd.utils
import libmailcd.workflow
import libmailcd.env
import libmailcd.pipeline
from libmailcd.cli.common.workflow import pipeline_inbox_run
from libmailcd.cli.common.workflow import pipeline_outbox_run
from libmailcd.cli.common.workflow import pipeline_stages_run
from libmailcd.cli.common.workflow import pipeline_set_env
from libmailcd.cli.main import main

from libmailcd.cli.common.path_manager import *

########################################

@main.command("build")
@click.pass_obj
def main_build(obj):
    exit_code = 0

    api = obj["api"]
    logger = obj["logger"]

    try:
        workspace = api.settings("workspace")
        logging.debug(f"workspace: {workspace}")

        layout = Layout(workspace, api)


        pipeline_filepath = layout.pipeline
        logging.debug(f"pipeline_filepath: {pipeline_filepath}")

        if not pipeline_filepath.is_file():
            raise ValueError(f"no pipeline found: {pipeline_filepath.name} ({workspace})")

        # TODO(Matthew): How do we get directories to not require the .root? Make the dirs a Path? or return a Path?
        mb_env_path = layout.env.root
        mb_outbox_path = layout.outbox.root
        mb_logs_build_path = layout.logs.builds

        logging.debug(f"mb_env_path={mb_env_path}")
        logging.debug(f"mb_outbox_path={mb_outbox_path}")
        logging.debug(f"mb_logs_build_path={mb_logs_build_path}")
        #return

        pipeline_dict = libmailcd.utils.load_yaml(pipeline_filepath)
        pipeline = libmailcd.pipeline.Pipeline.from_dict(pipeline_dict)

        # TODO(matthew): Should we clean up the outbox here? for now, yes...
        if mb_outbox_path.exists():
            # TODO(matthew): what about the case where this isn't a directory?
            shutil.rmtree(mb_outbox_path)

        # TODO(matthew): Should we clean up the logs here? for now, yes...
        if mb_logs_build_path.exists():
            # TODO(matthew): what about the case where this isn't a directory?
            shutil.rmtree(mb_logs_build_path)

        mb_logs_build_path.mkdir(parents=True, exist_ok=True)


        show_footer = False
        env_vars = []
        mb_inbox_env_vars = {}

        #######################################
        #               INBOX                 #
        #######################################
        logger = logging.getLogger()

        if pipeline.inbox:
            print(f"========== INBOX ==========")
            mb_inbox_env_vars = pipeline_inbox_run(layout.inbox, pipeline.inbox)
            show_footer = True

        #######################################
        #             PROCESSING              #
        #######################################

        env_vars = pipeline_set_env(mb_inbox_env_vars, mb_env_path)
        if env_vars:
            print(f"======= ENVIRONMENT =======")
            for ev in env_vars:
                print(f" {ev}={os.environ[ev]}")
            show_footer = True

        if pipeline.stages:
            print(f"========== STAGES ==========")
            pipeline_stages_run(
                api,
                workspace.resolve(),
                pipeline.stages,
                logpath=mb_logs_build_path,
                env=env_vars
            )
            show_footer = True

        #######################################
        #               OUTBOX                #
        #######################################

        if pipeline.outbox:
            print(f"========== OUTBOX ==========")
            pipeline_outbox_run(workspace, layout.outbox, pipeline.outbox)
            show_footer = True

        if show_footer:
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
