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
from libmailcd.cli.common.constants import INSOURCE_PIPELINE_FILENAME

########################################

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
        mb_outbox_path = api.settings("outbox_root")
        mb_logs_build_path = api.settings("logs_build_root")

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

        if pipeline.inbox:
            print(f"========== INBOX ==========")
            mb_inbox_env_vars = pipeline_inbox_run(api, pipeline.inbox)
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
            pipeline_stages_run(workspace.resolve(), pipeline.stages, logpath=mb_logs_build_path)
            show_footer = True

        #######################################
        #               OUTBOX                #
        #######################################

        if pipeline.outbox:
            print(f"========== OUTBOX ==========")
            pipeline_outbox_run(api, pipeline.outbox)
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
