from pathlib import Path

import click

import libmailcd.utils
from libmailcd.cli.common.constants import INSOURCE_PIPELINE_FILENAME
from libmailcd.cli.common.workflow import pipeline_outbox_deploy
from libmailcd.cli.main import main


########################################

# TODO(Matthew): Add option to specify a single storage_id/outbox to push
@main.command("push")
@click.pass_obj
def main_push(obj):
    api = obj["api"]

    workspace = api.settings("workspace")
    pipeline_filepath = Path(workspace, INSOURCE_PIPELINE_FILENAME).resolve()

    pipeline = libmailcd.utils.load_yaml(pipeline_filepath)

    pipeline_outbox = None
    if 'outbox' in pipeline:
        pipeline_outbox = pipeline['outbox']

    if pipeline_outbox:
        pipeline_outbox_deploy(api, pipeline_outbox)
        pass
        #env_vars = pipeline_inbox_run(api, pipeline_inbox)
