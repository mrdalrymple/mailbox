import logging
from pathlib import Path

import click

import libmailcd.storage

def app_init(settings):
    if settings['storage_root'] is not None:
        storage_root_path = Path(settings['storage_root'])
        if not storage_root_path.exists():
            print(f"creating storage: {storage_root_path}")
            storage_root_path.mkdir(parents=True)

# TODO(matthew): enable logging and set default levels here
# TODO(matthew): see if there is a way to pass --debug and update logging
#  level here for all subcommands
@click.group()
@click.option("--debug/--no-debug", default=False, help="Show debug output")
def main(debug):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    settings = {}
    settings['storage_root'] = libmailcd.storage.get_artifact_storage_root()

    app_init(settings)

