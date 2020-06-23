import os
import sys
import logging
from pathlib import Path

import click

import libmailcd.library
from libmailcd.cli.main import main

from libmailcd.constants import DEFAULT_LIBRARY_NAME


########################################

@main.group("lib")
def main_library():
    pass

@main_library.command("ls")
@click.argument("config", required=False)
@click.pass_obj
def main_library_ls(api, config):
    libraries = [ DEFAULT_LIBRARY_NAME ]
    library_root = Path(api.settings("library_root"))
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
        selected = DEFAULT_LIBRARY_NAME

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
    library_root = Path(api.settings("library_root"))

    if library_name == DEFAULT_LIBRARY_NAME:
        print(f"Invalid library: cannot remove the default library")
        sys.exit(1)

    installed_libraries = libmailcd.library.get_installed_libraries(library_root)
    if installed_libraries:
        if library in installed_libraries:
            library_found = True

    if not library_found:
        print(f"Unknown library: {library}")
        sys.exit(1)

    # Special Case: if library to remove is currently selected, select the default
    current_selected = libmailcd.library.get_selected(library_root)
    if current_selected and current_selected == library:
        libmailcd.library.set_selected(library_root, DEFAULT_LIBRARY_NAME)

    libmailcd.library.remove(library_root, library_name)

@main_library.command("add")
@click.argument("url")
@click.option("--name")
@click.option("--ref")
@click.pass_obj
def main_library_add(api, url, name, ref):
    library_name = name
    if not library_name:
        library_name = libmailcd.library.url_to_name(url)

    library_root = Path(api.settings("library_root"))

    # NOTE(matthew): If library already exists, we could offer an overwrite feature/flag.
    #  We could also have interactive "already exists, overwrite (Y/n)" prompt.
    #   If we go this route, we should do more validation that library url is same.
    #  Until a real use-case shows up, don't go the overwrite approach; let the user
    #   remove it first.
    if libmailcd.library.exists(library_root, library_name):
        print(f"Library already exists: {library_name}")
        sys.exit(1)

    libmailcd.library.add(library_root, url, library_name)

@main_library.command("select")
@click.argument("library")
@click.pass_obj
def main_library_select(api, library):
    library_name = library
    all_libraries = [ DEFAULT_LIBRARY_NAME ]
    library_found = False
    library_root = Path(api.settings("library_root"))

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

    installed_libraries = libmailcd.library.get_installed_libraries(library_root)
    logging.debug(f"installed_libraries={installed_libraries}")

    all_libraries.extend(installed_libraries)
    if library_name in all_libraries:
        library_found = True

    if not library_found:
        print(f"Unknown library: {library_name}")
        sys.exit(1)

    libmailcd.library.set_selected(library_root, library_name)
    logging.info(f"Selected library: {library_name}")
