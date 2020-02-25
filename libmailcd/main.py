# -*- coding: utf-8 -*-

import sys
import os
import argparse
from pathlib import Path, PurePath
import pprint
import click

import libmailcd
import libmailcd.storage
import libmailcd.utils

########################################

INSOURCE_PIPELINE_FILENAME = 'pipeline.yml'

########################################

def app_init(settings):
    if settings['storage_root'] is not None:
        storage_root_path = Path(settings['storage_root'])
        if not storage_root_path.exists():
            print(f"creating storage: {storage_root_path}")
            storage_root_path.mkdir(parents=True)

def log_data_structure(data, display_name = None):
    if display_name is not None:
        print(f"{display_name}:")
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(data)

########################################

def pull_artifact_by_id(config, art_id):
    sr = config['settings']['storage_root']
    artifact_path = Path(sr, art_id).resolve()
    print(f"artifact path: {artifact_path}")
    pass

########################################

def exec_inbox(config, inbox):
    print(f"Executing Inbox")
    #log_data_structure(inbox, "inbox")
    for slot in inbox:
        label = slot['label']
        print(f"slot: {label}")
        pull_artifact_by_id(config, label)
    pass

def exec_outbox(config, outbox):
    print(f"Executing Outbox")
    log_data_structure(outbox, "outbox")
    pass

def exec_steps(config, steps):
    print(f"Executing Steps")
    log_data_structure(steps, "steps")

def exec_stage(config, stage_name, stage):
    print(f"Executing Stage: {stage_name}")

    if 'inbox' in stage:
        inbox = stage['inbox']
        exec_inbox(config, inbox)

    if 'steps' in stage:
        steps = stage['steps']
        exec_steps(config, steps)

    if 'outbox' in stage:
        outbox = stage['outbox']
        exec_outbox(config, outbox)
    pass

########################################


@click.group()
def cli():
    pass

@cli.group("storage", invoke_without_command=True)
@click.pass_context
def cli_storage(ctx):
    # If no subcommand specified, default to 'list'
    if ctx.invoked_subcommand is None:
        ctx.invoke(cli_storage_list)
    pass

@cli_storage.command("add")
@click.argument("sid")
@click.argument("package", type=click.Path(exists=True)) # can be zip or directory
def cli_storage_add(sid, package):
    print(f"add({sid}, {package})")
    libmailcd.storage.add(sid, package)
    pass

@cli_storage.command("list")
@click.argument("sid", default=None, required=False)
def cli_storage_list(sid):
    if sid:
        sid = sid.upper()
        versions = libmailcd.storage.get(sid)
        for version in versions:
            print(f"{version}")

        if not versions:
            print(f"{sid} - No entries")
    else:
        storage_ids = libmailcd.storage.get()

        for sid in storage_ids:
            print(f"{sid}")
        
        if not storage_ids:
            print(f"Nothing currently stored")

    pass


#mb storage label LUA/acdef
#mb storage label LUA acdef
# TODO(matthew): Look into auto completion (https://stackoverflow.com/questions/187621/how-to-make-a-python-command-line-program-autocomplete-arbitrary-things-not-int)
@cli_storage.command("label")
@click.argument("ref")
@click.argument("label", default=None, required=False)
def cli_storage_label(ref, label):
    storage_id, partial_package_hash = libmailcd.storage.split_ref(ref)
    #print(f"sid={storage_id}, pphash={partial_package_hash}")
    if storage_id and partial_package_hash:
        matches = libmailcd.storage.get_package_hash_matches(storage_id, partial_package_hash)
        if len(matches) == 1:
            package_hash = matches[0]

            if label:
                libmailcd.storage.label(storage_id, package_hash, label)
            else:
                print(f"{storage_id}/{package_hash}:")
                labels = libmailcd.storage.get_labels(storage_id, package_hash)
                for label in labels:
                    print(f"  {label}")
                else:
                    print("  No labels defined")
        else:
            print("Multiple matches found:")
            for m in matches:
                print(f"  {m}")
    elif storage_id:
        versions = libmailcd.storage.get(storage_id)
        for version in versions:
            print(f"{version}")

        if not versions:
            print(f"{storage_id} - No entries")
    pass


# NOTE(matthew): This can eventually be removed after completed ported to click.
#  Need to see where all this code fits in.
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--project_dir", dest='project_dir', default=".")
    parser.add_argument("--env_config", dest='env_config', default="enva.yml")

    args = parser.parse_args()

    #print(f"arg(project_dir)={args.project_dir}")
    #print(f"arg(env_config)={args.env_config}")

    settings = {}
    settings['storage_root'] = libmailcd.storage.get_artifact_storage_root()

    app_init(settings)

    arg_project_dir = Path(args.project_dir).resolve()
    arg_env_config = Path(args.env_config).resolve()
    
    #print(f"arg_project_dir={arg_project_dir}")
    #print(f"arg_env_config={arg_env_config}")

    env = libmailcd.utils.load_yaml(arg_env_config)

    config = {
        'settings': settings,
        'env': env
    }


    #print(f"env={env}")

    # TODO(Matthew): Make the pipeline filepath/filename configurable
    pipeline_filepath = Path(arg_project_dir, INSOURCE_PIPELINE_FILENAME).resolve()

    #print(f"pipeline_filepath={pipeline_filepath}")

    pipeline = libmailcd.utils.load_yaml(pipeline_filepath)

    #log_data_structure(pipeline)

    for stage_name in pipeline['stages'].keys():
        stage = pipeline['stages'][stage_name]
        exec_stage(config, stage_name, stage)


    return 0

########################################
