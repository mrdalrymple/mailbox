import os
import sys
import logging
from pathlib import Path

import click

import libmailcd.library
from libmailcd.cli.main import main


MAILCD_CONFIG_ROOT = str(Path(Path.home(), ".mailcd"))
MAILCD_LIBRARY_ROOT = Path(MAILCD_CONFIG_ROOT, "library")
MAILCD_LIBRARY_DEFAULT = 'default'


########################################

@main.group("lib")
def main_library():
    pass

@main_library.command("ls")
@click.argument("config", required=False)
@click.pass_obj
def main_library_ls(api, config):
    libraries = [ MAILCD_LIBRARY_DEFAULT ]
    library_root = Path(MAILCD_LIBRARY_ROOT)
    selected = None

    # Find installed libraries
    installed_libraries = libmailcd.library.get_installed_libraries(library_root)

    # If libraries are installed, find the selected one
    if installed_libraries:
        # Check if a library is already set/selected via the environment
        if 'MB_LIBRARY' in os.environ:
            library = os.environ['MB_LIBRARY']
            if 'MB_LIBRARY_NAME' in os.environ:
                library_name = os.environ['MB_LIBRARY_NAME']
            if not library_name:
                library_name = libmailcd.library.url_to_name(library)
            selected = library_name

        # If no library is set via the environment
        if not selected:
            selected = libmailcd.library.get_selected(library_root)

        libraries.extend(installed_libraries)

    # If no libraries installed, or none of them are selected, select the default
    if not selected:
        selected = MAILCD_LIBRARY_DEFAULT

    for lib in libraries:
        if lib == selected:
            print(f"* {lib}")
        else:
            print(f"  {lib}")

@main_library.command("rm")
@click.argument("library")
@click.pass_obj
def main_library_rm(api, library):
    library_name = library
    library_found = False

    if library_name == MAILCD_LIBRARY_DEFAULT:
        print(f"Invalid library: cannot remove the default library")
        sys.exit(1)

    installed_libraries = libmailcd.library.get_installed_libraries(MAILCD_LIBRARY_ROOT)
    if installed_libraries:
        if library in installed_libraries:
            library_found = True

    if not library_found:
        print(f"Unknown library: {library}")
        sys.exit(1)

    # Special Case: if library to remove is currently selected, select the default
    current_selected = libmailcd.library.get_selected(MAILCD_LIBRARY_ROOT)
    if current_selected and current_selected == library:
        libmailcd.library.set_selected(MAILCD_LIBRARY_ROOT, MAILCD_LIBRARY_DEFAULT)

    libmailcd.library.remove(MAILCD_LIBRARY_ROOT, library_name)

@main_library.command("add")
@click.argument("url")
@click.option("--name")
@click.option("--ref")
@click.pass_obj
def main_library_add(api, url, name, ref):
    library_name = name
    if not library_name:
        library_name = libmailcd.library.url_to_name(url)

    # NOTE(matthew): If library already exists, we could offer an overwrite feature/flag.
    #  We could also have interactive "already exists, overwrite (Y/n)" prompt.
    #   If we go this route, we should do more validation that library url is same.
    #  Until a real use-case shows up, don't go the overwrite approach; let the user
    #   remove it first.
    if libmailcd.library.exists(MAILCD_LIBRARY_ROOT, library_name):
        print(f"Library already exists: {library_name}")
        sys.exit(1)

    libmailcd.library.add(MAILCD_LIBRARY_ROOT, url, library_name)

@main_library.command("select")
@click.argument("library")
@click.pass_obj
def main_library_select(api, library):
    library_name = library
    all_libraries = [ MAILCD_LIBRARY_DEFAULT ]
    library_found = False

    # Handle case where MB_LIBRARY env. variable is set (should not be able to change selection)
    # NOTE(matthew): Or is this not the case?  What do we do when env. variable set and we init but it is not the current selected?
    #  Maybe the use case here isn't valid.
    if 'MB_LIBRARY' in os.environ:
        env_library = os.environ['MB_LIBRARY']
        if 'MB_LIBRARY_NAME' in os.environ:
            env_library_name = os.environ['MB_LIBRARY_NAME']
        if not env_library_name:
            env_library_name = libmailcd.library.url_to_name(env_library)
        print(f"Error: unable to change selection while 'MB_LIBRARY' is set")
        sys.exit(1)

    installed_libraries = libmailcd.library.get_installed_libraries(MAILCD_LIBRARY_ROOT)
    logging.debug(f"installed_libraries={installed_libraries}")

    all_libraries.extend(installed_libraries)
    if library_name in all_libraries:
        library_found = True

    if not library_found:
        print(f"Unknown library: {library_name}")
        sys.exit(1)

    libmailcd.library.set_selected(MAILCD_LIBRARY_ROOT, library_name)
    logging.info(f"Selected library: {library_name}")
