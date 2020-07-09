import sys

import click

from libmailcd.cli.main import main

########################################

# NOTE(matthew): Probably go route of using --local/global and allow settings to set which is default

@main.group("cred")
@click.pass_obj
def main_cred(api):
    """Manages credentials.
    """
    pass

@main_cred.command("ls")
@click.pass_obj
def cred_ls(api):
    """List all credential IDs
    """
    # Get all cred IDs
    cred_ids = api.cred_get_ids()

    if not cred_ids:
        print(f"No credientials found (see `cred set')")
        sys.exit(0)

    for cred_id in cred_ids:
        print(f"{cred_id}")

# NOTE(matthew): Currently, only supports username/password combos
# TODO(matthew): Support user supplying key/value pairs (username=..., password=...)
@main_cred.command("set")
@click.argument("cred_id")
@click.argument("username")
@click.argument("password")
@click.option("-f", "--force", "force", is_flag=True)
@click.pass_obj
def cred_set(api, cred_id, username, password, force):
    if not force and api.cred_exists(cred_id):
        print(f"Cannot set credential: {cred_id} (already exists)")
        print(f'  (use the "--force" option to override)')
        sys.exit(2) # TODO(matthew): Should standardize on error codes, (probably based on click, 1 general failure, 2 invalid args, etc.)

    api.cred_set(cred_id, username=username, password=password)
    sys.exit(0)

@main_cred.command("unset")
@click.argument("cred_id")
@click.pass_obj
def cred_unset(api, cred_id):
    if api.cred_exists(cred_id):
        api.cred_unset(cred_id)
