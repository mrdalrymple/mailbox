import logging
import os
import sys
import traceback

import click

from libmailcd.cli.main import main

from libmailcd.cli.common.path_manager import Layout


@main.command("logs")
@click.argument("log", default=None, required=False)
@click.option("--env", "-e", is_flag=True, help="Display the environment instead of output.")
@click.pass_obj
def main_logs(obj, log, env):
    """View various logs

    Arguments:
        log {Path} -- Path to the log to view.
    """
    exit_code = 0

    api = obj["api"]

    try:
        # TODO(Matthew): I'm not happy with this code, however, it works and I don't know what to change.
        workspace = api.settings("workspace")
        logging.debug(f"workspace: {workspace}")
        layout = Layout(workspace, api)

        log_refs = []

        layout_logs = layout.logs

        # Look in a specific category / file
        if log:

            if env:
                log_refpath = layout_logs.get_env_log_path(log)
            else:
                log_refpath = layout_logs.get_build_log_path(log)

            logging.debug(f"log_refpath: {log_refpath}")

            if not log_refpath.exists():
                raise ValueError(f"Unknown log: {log}")

            # Found a specific log?
            if os.path.isfile(log_refpath):
                #print(f"||||| {log_refpath} |||||")
                with open(log_refpath) as file:
                    # Note: need to use .read() with .splitlines() instead of
                    #  readlines() directly on the file objects. Otherwise we
                    #  print an extra line (bug with .readlines()?).
                    contents = file.read()
                for line in contents.splitlines():
                    print(line)
                #print(f"||||| {log_refpath} |||||")
            else:
                raise RuntimeError(f"Log isn't a file (as expected): {log_refpath}")

        else: # No category selected, show the list of available sections
            for stage in layout_logs.get_stages():
                log_refs.append(stage)

            # Display the list of options
            for log_ref in log_refs:
                print(log_ref)
    except ValueError as e:
        print(f"{e}")
        exit_code = 4
    except Exception as e:
        print(f"{e}")
        traceback.print_exc()
        exit_code = 3

    sys.exit(exit_code)
