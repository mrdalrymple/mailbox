import os
import sys
import logging

import click

#import libmailcd.utils

from libmailcd.cli.main import main


########################################

@main.group("env")
def main_env():
    pass

@main_env.command("ls")
@click.argument("config", required=False)
@click.pass_obj
def main_env_ls(api, config):
    """List the environments and their variables.

    Arguments:
        config {String} -- Config to the list the variables associated.
    """

    if config:
        try:
            contents = api.env_get(config)
        except FileNotFoundError:
            print(f"Unknown config: {config}")
            sys.exit(1)


        for key, value in contents.items():
            print(f"{key} = {value}")
    else:

        selected = api.env_get_selected_config()
        environments = api.env_get_environments()
        for env_name in environments:
            if env_name == selected:
                print(f"* {env_name}")
            else:
                print(f"  {env_name}")

@main_env.command("create")
@click.argument("config")
@click.pass_obj
def main_env_create(api, config):
    """Create an environment.

    Arguments:
        config {String} -- Name of the environment config to create.
    """
    # TODO(matthew): add '--from' option so you can copy an environment
    # TODO(matthew): add a whole 'copy' command?

    # TODO(matthew): use 'api.env_exists(config):' here?
    if api.env_is_environment(config):
        print(f"Environment already exists: {config}")
        sys.exit(1)

    api.env_create(config)

@main_env.command("delete")
@click.argument("config")
@click.pass_obj
def main_env_delete(api, config):
    """Remove an environment.

    Arguments:
        config {String} -- Name of the environment config to remove.
    """

    # TODO(matthew): use 'api.env_exists(config):' here?
    if api.env_is_environment(config):
        # TODO(matthew): Change behavior later, where any environment can be deleted?
        #  Remove concept of default environment? At least move it out of API?
        default_config = api.env_get_default_config_name()
        if config == default_config:
            print(f"Not allowed to delete the default environment: {default_config}")
            sys.exit(2)

        selected_config = api.env_get_selected_config()
        if config == selected_config:
            print(f"Now allowed to delete the selected environment: {selected_config}")
            sys.exit(3)

        api.env_delete(config)


@main_env.command("select")
@click.argument("config")
@click.pass_obj
def main_env_select(api, config):
    """Select an environment.

    Arguments:
        config {String} -- Name of the environment to select.
    """

    if not api.env_is_environment(config):
        print(f"Unknown environment: {config}")
        sys.exit(1)

    api.env_set_selected_config(config)
    logging.info(f"Selected config: {config}")

@main_env.command("set")
@click.argument("ref")
@click.argument("value")
@click.pass_obj
# TODO(matthew): add a --global flag? How would a global env work?
def main_env_set(api, ref, value):
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

    if not api.env_valid_ref(ref):
        print(f"Invalid environment ref: {ref}")
        sys.exit(1)

    config = None
    env_variable = None
    try:
        config, env_variable = ref.split("/")
    except ValueError:
        env_variable = ref
        logging.debug(f"Config not specified, only variable: {env_variable}")

    # Case #1 -- Fail out
    if config:
        if not api.env_exists(config):
            print(f"Unknown environment: {config}  (see mb env create)")
            sys.exit(2)
    else:
        # TODO(matthew): Put this code into libmailcd.env.set_variable? Probably
        # No config was supplied, see if we can detect a selected one
        selected_config = api.env_get_selected_config()
        if not selected_config:
            # Nothing selected? Select the default
            selected_config = api.env_get_default_config_name()
            api.env_set_selected_config(selected_config)
        config = selected_config

    api.env_set_variable(config, env_variable, value)

@main_env.command("unset")
@click.argument("ref")
@click.pass_obj
def main_env_unset(api, ref):
    """Remove a variable from an environment.

    Arguments:
        ref {String} -- Environment ref in the form of [CONFIG/]VARIABLE
    """

    if not api.env_valid_ref(ref):
        print(f"Invalid environment ref: {ref}")
        sys.exit(1)

    config = None
    env_variable = None
    try:
        config, env_variable = ref.split("/")
    except ValueError:
        env_variable = ref

    if not config:
        config = api.env_get_selected_config()
        logging.debug(f"No environment specified, using selected: {config}")

    api.env_unset_variable(config, env_variable)
