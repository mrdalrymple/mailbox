from pathlib import Path

import click

import libmailcd.utils
from libmailcd.constants import INSOURCE_PIPELINE_FILENAME
from libmailcd.cli.common.workflow import inbox_run
from libmailcd.cli.main import main


########################################

@main.command("pull")
@click.option("--workspace", default=".")
def main_pull(workspace):
    arg_workspace = Path(workspace).resolve()
    pipeline_filepath = Path(arg_workspace, INSOURCE_PIPELINE_FILENAME).resolve()

    pipeline = libmailcd.utils.load_yaml(pipeline_filepath)

    pipeline_inbox = None
    if 'inbox' in pipeline:
        pipeline_inbox = pipeline['inbox']

    if pipeline_inbox:
        inbox_run(workspace, pipeline_inbox)
