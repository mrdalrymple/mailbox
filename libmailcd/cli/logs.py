import os
from pathlib import Path

import click

from libmailcd.cli.main import main

from libmailcd.cli.common.constants import ENV_LOG_FILE_EXTENSION, LOG_FILE_EXTENSION


@main.command("logs")
@click.argument("log", default=None, required=False)
@click.option("--env", "-e", is_flag=True, help="Display the environment instead of output.")
@click.pass_obj
def main_logs(api, log, env):
    """View various logs
    
    Arguments:
        log {Path} -- Path to the log to view.
    """
    # TODO(Matthew): I'm not happy with this code, however, it works and I don't know what to change.

    log_refs = []

    mb_logs_root = api.settings("logs_root")

    # Look in a specific category / file
    if log:
        log_refpath = Path(mb_logs_root, log)

        # Feature where the user doesn't need to type ".log" all the time
        log_refpath_ext = log_refpath
        if not str(log_refpath).endswith(LOG_FILE_EXTENSION):
            if not str(log_refpath).endswith(ENV_LOG_FILE_EXTENSION):
                # If 'ENV" flag is set, print the environment file instead of log file
                if env:
                    log_refpath_ext = Path(f"{log_refpath}{ENV_LOG_FILE_EXTENSION}")
                else:
                    log_refpath_ext = Path(f"{log_refpath}{LOG_FILE_EXTENSION}")

        # Found a specific log?
        if os.path.isfile(log_refpath_ext):
            with open(log_refpath_ext, encoding="utf-8") as file:
                print(f"||||| {log_refpath_ext} |||||")
                # Note: need to use .read() with .splitlines() instead of
                #  readlines() directly on the file objects. Otherwise we
                #  print an extra line (bug with .readlines()?).
                contents = file.read()
                contents = contents.replace("\r\n", "\n")
                for line in contents.splitlines():
                    print(line)
                print(f"||||| {log_refpath_ext} |||||")
        else: # Found a category, show logs
            if os.path.isdir(log_refpath):
                raw_files = os.listdir(log_refpath)
                for log_file in raw_files:
                    if log_file.endswith(ENV_LOG_FILE_EXTENSION):
                        continue
                    log_refs.append(log_file)
    else: # No category selected, show the list of available sections
        if mb_logs_root.exists():
            if os.path.isdir(mb_logs_root):
                raw_files = os.listdir(mb_logs_root)
                for category in raw_files:
                    log_refs.append(category)

    # Display the list of options
    for log_ref in log_refs:
        # Feature to not even show the file extension
        if str(log_ref).endswith(LOG_FILE_EXTENSION):
            log_ref = str(log_ref)[:-len(LOG_FILE_EXTENSION)]

        print(log_ref)
