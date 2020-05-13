import os
import logging
from pathlib import Path

import click

import libmailcd.settings
import libmailcd.storage
import libmailcd.api
import libmailcd.library

MAILCD_CONFIG_ROOT = str(Path(Path.home(), ".mailcd"))
MAILCD_LIBRARY_ROOT = Path(MAILCD_CONFIG_ROOT, "library")

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
@click.option("--workspace", default=".")
@click.option("--debug/--no-debug", default=False, help="Show debug output")
@click.pass_context
def main(ctx, workspace, debug):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.CRITICAL)

    # TODO(matthew): refactor this to not have to use get_artifact_storage_root()
    #  Maybe have an api.init()? And do all this inside there?
    settings = {}
    settings['storage_root'] = libmailcd.storage.get_artifact_storage_root()

    app_init(settings)

    settings = libmailcd.settings.Settings(
        workspace=workspace
    )

    # Detect if plugin library has been set
    library = None
    library_name = None
    library_head = None
    if 'MB_LIBRARY' in os.environ:
        library = os.environ['MB_LIBRARY']
    if 'MB_LIBRARY_NAME' in os.environ:
        library_name = os.environ['MB_LIBRARY_NAME']
    if 'MB_LIBRARY_HEAD' in os.environ:
        library_head = os.environ['MB_LIBRARY_HEAD']

    # Hard-code a sample library for development purposes
    #  TODO(Matthew): modify development env. to set the env. variable and load accordingly.
    #library = "https://gitlab.com/mrdalrymple/pymailcd_sample_library.git"

    loaded_api = libmailcd.library.load_library(
        MAILCD_LIBRARY_ROOT,
        library,
        library_name=library_name,
        library_head=library_head
    )

    default_api = libmailcd.api.DefaultAPI(settings)

    api = libmailcd.api.API(default_api, custom_api=loaded_api)
    api.on_init()

    ctx.obj = api
