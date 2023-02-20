from pathlib import Path

import click

import libmailcd.utils
from libmailcd.cli.common.constants import INSOURCE_PIPELINE_FILENAME
from libmailcd.cli.common.workflow import pipeline_inbox_run
from libmailcd.cli.main import main


########################################

@main.command("pull")
@click.pass_obj
def main_pull(obj):
    api = obj["api"]

    workspace = api.settings("workspace")
    pipeline_filepath = Path(workspace, INSOURCE_PIPELINE_FILENAME).resolve()

    pipeline = libmailcd.utils.load_yaml(pipeline_filepath)

    pipeline_inbox = None
    if 'inbox' in pipeline:
        pipeline_inbox = pipeline['inbox']

    if pipeline_inbox:
        env_vars = pipeline_inbox_run(api, pipeline_inbox)
