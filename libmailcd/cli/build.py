import logging
import os
import shutil
import sys
import traceback

import click

import libmailcd.utils
import libmailcd.workflow
import libmailcd.env
import libmailcd.pipeline
from libmailcd.cli.common.exceptions import AppNotInstalledError
from libmailcd.cli.common.exceptions import AppNotRunningError
from libmailcd.cli.common.path_manager import Layout
from libmailcd.cli.common.workflow import pipeline_inbox_run
from libmailcd.cli.common.workflow import pipeline_outbox_run
from libmailcd.cli.common.workflow import pipeline_stages_run
from libmailcd.cli.common.workflow import pipeline_set_env
from libmailcd.cli.tools import agent
from libmailcd.cli.main import main


########################################

@main.command("build")
@click.pass_obj
def main_build(obj):
    exit_code = 0

    api = obj["api"]
    #logger = obj["logger"]

    try:
        workspace = api.settings("workspace")
        logging.debug(f"workspace: {workspace}")
        layout = Layout(workspace, api)


        pipeline_filepath = layout.pipeline
        logging.debug(f"pipeline_filepath: {pipeline_filepath}")

        if not pipeline_filepath.is_file():
            raise ValueError(f"no pipeline found: {pipeline_filepath.name} ({workspace})")

        # NOTE(Matthew): I don't like the name of this or how it's exposed here
        # I do like that it fails this first before parsing the pipeline
        # Maybe that's bad? What if pipeline doesn't use docker, etc.?
        agent.validate_dependencies_met()

        # TODO(Matthew): How do we get directories to not require the .root? Make the dirs a Path? or return a Path?
        mb_env_path = layout.env.root
        mb_outbox_path = layout.outbox.root
        mb_logs_path = layout.logs.root

        logging.debug(f"mb_env_path={mb_env_path}")
        logging.debug(f"mb_outbox_path={mb_outbox_path}")
        logging.debug(f"mb_logs_path={mb_logs_path}")

        pipeline_dict = libmailcd.utils.load_yaml(pipeline_filepath)
        pipeline = libmailcd.pipeline.Pipeline.from_dict(pipeline_dict)

        # TODO(matthew): Should we clean up the outbox here? for now, yes...
        if mb_outbox_path.exists():
            # TODO(matthew): what about the case where this isn't a directory?
            shutil.rmtree(mb_outbox_path)

        # TODO(matthew): Should we clean up the logs here? for now, yes...
        if mb_logs_path.exists():
            # TODO(matthew): what about the case where this isn't a directory?
            shutil.rmtree(mb_logs_path)


        show_footer = False
        env_vars = []
        mb_inbox_env_vars = {}

        #######################################
        #               INBOX                 #
        #######################################
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
                layout_logs=layout.logs,
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
    except AppNotInstalledError as e:
        print(f"Required application is not installed: {e.app}")
        if e.app == "docker":
            print()
            print(" Install Docker Desktop and try again...")
            print(" See: https://www.docker.com/get-started/")
            print()
            print(" If installed, make sure 'docker' is accessible via the PATH.")
            print()
        exit_code = 5
    except AppNotRunningError as e:
        print(f"Required application is not running: {e.app}")
        if e.app == "docker":
            print()
            print(" Start Docker Desktop and try again...")
            print()
        exit_code = 6
    except ValueError as e:
        print(f"{e}")
        exit_code = 4
    except Exception as e:
        print(f"{e}")
        traceback.print_exc()
        exit_code = 3

    sys.exit(exit_code)
