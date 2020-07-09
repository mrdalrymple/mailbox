from pathlib import Path
import yaml

import keyring
from cryptography.fernet import Fernet

from libmailcd.utils import load_yaml
from libmailcd.utils import save_yaml

CRED_STORE_FILENAME = "cred_store.yml"

def exists(mb_config_path, cred_id):
    exists = False

    cred_store_path = Path(mb_config_path, CRED_STORE_FILENAME)

    if cred_store_path.exists():
        cred_store = load_yaml(cred_store_path)
        if cred_id in cred_store:
            exists = True

    return exists

def get_ids(mb_config_path):
    ids = []

    cred_store_path = Path(mb_config_path, CRED_STORE_FILENAME)

    if cred_store_path.exists():
        cred_store = load_yaml(cred_store_path)
        ids = cred_store.keys()

    return ids

def set_cred(mb_config_path, cred_id, **kwargs):
    cred_store = {}
    cred_store_path = Path(mb_config_path, CRED_STORE_FILENAME)

    if cred_store_path.exists():
        cred_store = load_yaml(cred_store_path)

    master_key = __get_mb_master_key()
    f = Fernet(master_key.encode())

    cred_store[cred_id] = {}

    # Add credential based on key/value supplied (i.e.: username=exampleuser, password=examplepassword)
    for key, value in kwargs.items():
        cred_store[cred_id][key] = f.encrypt(value.encode()).decode()

    save_yaml(cred_store_path, cred_store, indent=2)


def unset_cred(mb_config_path, cred_id):
    cred_store_path = Path(mb_config_path, CRED_STORE_FILENAME)

    if cred_store_path.exists():
        cred_store = load_yaml(cred_store_path)
        if cred_id in cred_store:
            del cred_store[cred_id]
            save_yaml(cred_store_path, cred_store, indent=2)

########################################

def __get_mb_master_key():
    master_key = None
    
    master_key = keyring.get_password("system", "mailbox_masterkey")
    if master_key is None:
        # Generate a key
        master_key = Fernet.generate_key().decode()
        keyring.set_password("system", "mailbox_masterkey", master_key)

    return master_key

def __rm_mb_master_key():
    keyring.delete_password("system", "mailbox_masterkey")
