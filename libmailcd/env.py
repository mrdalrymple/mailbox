import os
from pathlib import Path

from libmailcd.constants import LOCAL_MB_ROOT, LOCAL_ENV_DIRNAME, LOCAL_ENV_SELECT_FILENAME, DEFAULT_ENV_CONFIG_NAME


########################################

def create_config(mb_env_path, config):
    if not mb_env_path.exists():
        mb_env_path.mkdir()

    Path(mb_env_path, config).touch()

def delete_config(mb_env_path, config):
    config_filepath = Path(mb_env_path, config).resolve()

    if config_filepath.exists():
        config_filepath.unlink()

def unset_variable(mb_env_path, variable_name, config):
    config_filepath = Path(mb_env_path, config).resolve()

    # nothing to unset if the config doesn't exist
    if not config_filepath.exists():
        return

    config_contents = load_env_config(config_filepath)

    if variable_name in config_contents:
        del config_contents[variable_name]

    save_env_config(config_filepath, config_contents)



def set_variable(mb_env_path, variable_name, variable_value, config):
    config_filepath = Path(mb_env_path, config).resolve()

    # if the config exists, load it in so we can overwrite if necessary
    config_contents = {}
    if config_filepath.exists():
        config_contents = load_env_config(config_filepath)

    if not mb_env_path.exists():
        os.makedirs(mb_env_path, exist_ok=True)

    config_contents[variable_name] = variable_value

    save_env_config(config_filepath, config_contents)

def get_selected_config(mb_env_path, default=None):
    selected_config = default

    selected_env_filepath = Path(mb_env_path, LOCAL_ENV_SELECT_FILENAME).resolve()
    if selected_env_filepath.exists():
        with open(selected_env_filepath, 'r') as select_file:
            selected_config = select_file.read().strip().lower()

    return selected_config

def set_selected_config(mb_env_path, config):
    if not mb_env_path.exists():
        mb_env_path.mkdir()
    selected_env_filepath = Path(mb_env_path, LOCAL_ENV_SELECT_FILENAME).resolve()
    with open(selected_env_filepath, 'w') as select_file:
        select_file.write(f"{config}\n")

def is_environment(mb_env_path, config):
    found = False
    environments = get_environments(mb_env_path)
    if config in environments:
        found = True
    return found

def get_environments(mb_env_path):
    environments = []
    if mb_env_path.exists():
        environments = os.listdir(mb_env_path)
        if LOCAL_ENV_SELECT_FILENAME in environments:
            environments.remove(LOCAL_ENV_SELECT_FILENAME)
    return environments

def valid_env_ref(ref):
    #TODO(matthew): implement this
    return True

def load_env_config(filepath):
    contents = {}

    with open(filepath, 'r') as config_file:
        for line in config_file.readlines():
            # Ignore any lines with errors
            try:
                env_var_name, env_var_value = line.split('=', 1)
            except ValueError:
                continue
            contents[env_var_name.strip()] = env_var_value.strip()

    return contents

def save_env_config(filepath, contents):
    with open(filepath, 'w') as config_file:
        for key, value in contents.items():
            config_file.write(f"{key}={value}\n")


def get_variables(mb_env_path, config=None):
    """Get the environment variables from the currently selected config
    """
    variables = {}

    if config:
        selected_config = config
    else:
        selected_config = get_selected_config(mb_env_path)

    if Path(mb_env_path).resolve().exists():
        config_filepath = Path(mb_env_path, selected_config).resolve()
        if config_filepath.exists():
            variables = load_env_config(config_filepath)

    return variables
