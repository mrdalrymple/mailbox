import os
import sys
from pathlib import Path

import click

import libmailcd.utils
import libmailcd.env
from libmailcd.constants import LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME, LOCAL_ENV_SELECT_FILENAME, DEFAULT_ENV_CONFIG_NAME
from libmailcd.cli.common.workflow import inbox_run
from libmailcd.cli.main import main


########################################

@main.group("env")
def main_env():
    pass

@main_env.command("ls")
@click.argument("config", required=False)
@click.option("--workspace", default=".")
def main_env_ls(config, workspace):
    """List the environments and their variables.

    Arguments:
        config {String} -- Config to the list the variables associated.
    """
    arg_workspace = Path(workspace).resolve()
    mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
    mb_env_path = Path(arg_workspace, mb_env_relpath).resolve()

    if config:
        config_filepath = Path(mb_env_path, config).resolve()

        if not config_filepath.exists():
            print(f"Unknown config: {config}")
            sys.exit(1)

        contents = libmailcd.env.load_env_config(config_filepath)

        for key, value in contents.items():
            print(f"{key} = {value}")
    else:
        selected = libmailcd.env.get_selected_config(mb_env_path)
        environments = libmailcd.env.get_environments(mb_env_path)
        for env_name in environments:
            if env_name == selected:
                print(f"{env_name} *")
            else:
                print(f"{env_name}")


@main_env.command("rm")
@click.argument("ref")
@click.option("--workspace", default=".")
def main_env_rm(ref, workspace):
    """Remove an environment or a variable inside of it.

    Arguments:
        ref {String} -- Environment ref in the form of [CONFIG/]VARIABLE
    """

    if not libmailcd.env.valid_env_ref(ref):
        print(f"Invalid environment ref: {ref}")
        sys.exit(1)

    config = None
    env_variable = None
    try:
        config, env_variable = ref.split("/")
    except ValueError:
        env_variable = ref

    arg_workspace = Path(workspace).resolve()
    mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
    mb_env_path = Path(arg_workspace, mb_env_relpath).resolve()

    if env_variable:
        libmailcd.env.unset_variable(mb_env_path, env_variable, config)
    else:
        libmailcd.env.delete_config(mb_env_path, config)

@main_env.command("create")
@click.argument("config")
@click.option("--workspace", default=".")
def main_env_create(config, workspace):
    """Create an environment.

    Arguments:
        config {String} -- Name of the config to create.
    """
    arg_workspace = Path(workspace).resolve()
    mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
    mb_env_path = Path(arg_workspace, mb_env_relpath).resolve()

    if libmailcd.env.is_environment(mb_env_path, config):
        print(f"Environment already exists: {config}")
        sys.exit(1)

    libmailcd.env.create_config(mb_env_path, config)

@main_env.command("select")
@click.argument("config")
@click.option("--workspace", default=".")
def main_env_select(config, workspace):
    """Select an environment.

    Arguments:
        config {String} -- Name of the environment to select.
    """
    arg_workspace = Path(workspace).resolve()
    mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
    mb_env_path = Path(arg_workspace, mb_env_relpath).resolve()

    if not libmailcd.env.is_environment(mb_env_path, config):
        print(f"Unknown environment: {config}")
        sys.exit(1)

    libmailcd.env.set_selected_config(mb_env_path, config)

@main_env.command("set")
@click.argument("ref")
@click.argument("value", required=False)
@click.option("--workspace", default=".")
# TODO(matthew): add a --global flag? How would a global env work?
def main_env_set(ref, value, workspace):
    """Set the value for an environment variable.

    Arguments:
        ref {String} -- Environment ref in the form of [CONFIG/]VARIABLE
        value {String} -- Value to set the specified environment variable.
    """
    # Note: What are all the scenarios we need to worry about here?
    # 1. config is specified, but doesn't exist => error message out
    # 2. config is not specified, none selected => use default
    # 3. config is not specified, selected, but doesn't exist => create anyway
    # ?.

    if not libmailcd.env.valid_env_ref(ref):
        print(f"Invalid environment ref: {ref}")
        sys.exit(1)

    config = None
    env_variable = None
    try:
        config, env_variable = ref.split("/")
    except ValueError:
        env_variable = ref

    arg_workspace = Path(workspace).resolve()
    mb_env_relpath = Path(LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME)
    mb_env_path = Path(arg_workspace, mb_env_relpath).resolve()

    # Case #1 -- Fail out
    if config:
        config_filepath = Path(mb_env_relpath, config).resolve()
        if not config_filepath.exists():
            print(f"Unknown environment: {config}  (see mb env create)")
            sys.exit(2)
    else:
        # TODO(matthew): Put this code into libmailcd.env.set_variable? Probably
        # No config was supplied, see if we can detect a selected one
        selected_config = libmailcd.env.get_selected_config(mb_env_path)
        if not selected_config:
            # Nothing selected? Select the default
            selected_config = DEFAULT_ENV_CONFIG_NAME
            libmailcd.env.set_selected_config(mb_env_path, selected_config)
        config = selected_config

    libmailcd.env.set_variable(mb_env_path, env_variable, value, config)
