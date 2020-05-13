import os
import logging
from pathlib import Path
import shutil

from pygit2 import Repository, clone_repository, GIT_MERGE_ANALYSIS_NORMAL, GIT_MERGE_ANALYSIS_FASTFORWARD, GIT_MERGE_ANALYSIS_UP_TO_DATE
from yapsy.PluginManager import PluginManager
from yapsy.PluginFileLocator import PluginFileAnalyzerWithInfoFile

from libmailcd.constants import LOCAL_LIB_SELECT_FILENAME

def url_to_name(url):
    # get library name from URL
    return url[url.rfind('/')+1:].replace('.git', '')  # is this really the right way to get this name?

def exists(library_root, library_name):
    library_exists = False

    library_target = Path(library_root, library_name)

    if library_target.exists():
        library_exists = True

    return library_exists

def get_installed_libraries(library_root):
    installed_libraries = None
    if library_root.exists():
        installed_libraries = os.listdir(library_root)
        installed_libraries.remove(LOCAL_LIB_SELECT_FILENAME)
    return installed_libraries

def get_selected(library_root, default=None):
    selected_library = default

    selected_library_filepath = Path(library_root, LOCAL_LIB_SELECT_FILENAME).resolve()
    if selected_library_filepath.exists():
        with open(selected_library_filepath, 'r') as select_file:
            selected_library = select_file.read().strip().lower()

    return selected_library

def set_selected(library_root, library):
    """Set the selected library (doesn't validate existence)

    Arguments:
        library_root {Path} -- Path to where libraries are stored
        library {String} -- Library name to set as selected
    """
    if not library_root.exists():
        library_root.mkdir()
    selected_env_filepath = Path(library_root, LOCAL_LIB_SELECT_FILENAME).resolve()
    with open(selected_env_filepath, 'w') as select_file:
        select_file.write(f"{library}\n")

def add(library_root, library_url, library_name = None):
    if not library_root.exists():
        library_root.mkdir()

    library_target = Path(library_root, library_name)

    # TODO(matthew): detect if we already have the library download
    if library_target.exists():
        repo = Repository(Path(library_target, '.git'))
    else:
        # clone library if we don't have it already
        print(f"Loading Library: {library_url} => {library_target}")
        repo = clone_repository(library_url, library_target)

    return library_target, repo

def remove(library_root, library_name):
    """Remove the specified library (doesn't validate existence)

    Arguments:
        library_root {Path} -- Path to where libraries are stored
        library_name {String} -- Name of the library to remove
    """
    library_target = Path(library_root, library_name)
    if library_target.exists():
        # Use an onerror callback, as there are intermittent issues deleting git repos (permissions)
        shutil.rmtree(library_target, onerror=_onerror)


def load_library(library_root, library, library_name = None, library_head = None):
    loaded_api = None

    loaded_library_path = load_library_source(
        library_root,
        library,
        library_name,
        library_head
    )

    if loaded_library_path:
        logging.debug(f"Loaded Library: {loaded_library_path}")
        loaded_api = load_library_module(loaded_library_path)

    return loaded_api

def load_library_module(library_path):
    loaded_library_plugins = Path(library_path, "")

    pm = PluginManager()
    pm.setPluginPlaces([loaded_library_plugins])
    pm.collectPlugins()

    # Grab the first found plugin
    # Note: Currently only supporting up to 1 plugin to keep this simple.
    #  I have not heard a strong enough argument for supporting more than 1...
    #  Also vague on: if more than 1... Would they be ordered? How do you determine order?
    #  If they aren't ordered, how does that work as an end-user? How would we maximize feature
    #   understanding/intuitiveness and minimize complexity?
    for pi in pm.getAllPlugins():
        logging.debug(f"Activated: {pi.name}")
        pm.activatePluginByName(pi.name)
        break

    return pi.plugin_object


def load_library_source(library_root, library_url, library_name = None, library_head = None):
    if not library_url:
        return None

    # get library name from URL (if not specified)
    if not library_name:
        library_name = url_to_name(library_url)

    # NOTE(matthew): Should we be checking if already exists here? Probably (need 'exists' method then)
    library_target, repo = add(library_root, library_url, library_name)

    if library_head:
        repo.checkout(library_head)
        pull(repo, branch=library_head)
        print(f"{library_name} - Selected Ref: {library_head}")
    else:
        pull(repo)

    return library_target

# https://github.com/MichaelBoselowitz/pygit2-examples
def pull(repo, remote_name='origin', branch='master'):
    for remote in repo.remotes:
        if remote.name == remote_name:
            remote.fetch()
            remote_master_id = repo.lookup_reference('refs/remotes/origin/%s' % (branch)).target
            merge_result, _ = repo.merge_analysis(remote_master_id)
            # Up to date, do nothing
            if merge_result & GIT_MERGE_ANALYSIS_UP_TO_DATE:
                return
            # We can just fastforward
            elif merge_result & GIT_MERGE_ANALYSIS_FASTFORWARD:
                repo.checkout_tree(repo.get(remote_master_id))
                try:
                    master_ref = repo.lookup_reference('refs/heads/%s' % (branch))
                    master_ref.set_target(remote_master_id)
                except KeyError:
                    repo.create_branch(branch, repo.get(remote_master_id))
                repo.head.set_target(remote_master_id)
            elif merge_result & GIT_MERGE_ANALYSIS_NORMAL:
                repo.merge(remote_master_id)

                if repo.index.conflicts is not None:
                    for conflict in repo.index.conflicts:
                        print('Conflicts found in:', conflict[0].path)
                    raise AssertionError('Conflicts, ahhhhh!!')

                user = repo.default_signature
                tree = repo.index.write_tree()
                commit = repo.create_commit('HEAD',
                                            user,
                                            user,
                                            'Merge!',
                                            tree,
                                            [repo.head.target, remote_master_id])
                # We need to do this or git CLI will think we are still merging.
                repo.state_cleanup()
            else:
                raise AssertionError('Unknown merge analysis result')

########################################

def _onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=_onerror)``
    """
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise
