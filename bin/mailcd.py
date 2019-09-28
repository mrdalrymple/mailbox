# -*- coding: utf-8 -*-

import sys
import os
import argparse
from pathlib import Path, PurePath
import pprint

import yaml


import libmailcd

INSOURCE_PIPELINE_FILENAME = 'pipeline.yml'

def load_yaml(yaml_file):
    contents = {}

    with open(yaml_file, 'r') as stream:
        try:
            contents = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    return contents


def get_artifact_storage_root():
    return str(Path(Path.home(), ".mailcd", "storage"))


def app_init(settings):
    if settings['storage_root'] is not None:
        storage_root_path = Path(settings['storage_root'])
        if not storage_root_path.exists():
            print(f"creating storage: {storage_root_path}")
            storage_root_path.mkdir(parents=True)


def main():
    #print("Hello World")
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("env_config")
    args = parser.parse_args()

    #print(f"arg(project_dir)={args.project_dir}")
    #print(f"arg(env_config)={args.env_config}")

    settings = {}
    settings['storage_root'] = get_artifact_storage_root()

    app_init(settings)

    arg_project_dir = Path(args.project_dir).resolve()
    arg_env_config = Path(args.env_config).resolve()
    
    #print(f"arg_project_dir={arg_project_dir}")
    #print(f"arg_env_config={arg_env_config}")

    env = load_yaml(arg_env_config)

    #print(f"env={env}")

    # TODO(Matthew): Make the pipeline filepath/filename configurable
    pipeline_filepath = Path(arg_project_dir, INSOURCE_PIPELINE_FILENAME).resolve()

    #print(f"pipeline_filepath={pipeline_filepath}")

    pipeline = load_yaml(pipeline_filepath)

    #print(f"pipeline={pipeline}")
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(pipeline)

    for stage_name in pipeline['stages'].keys():
        #stage_name = stage[0]
        print(f"STAGE: {stage_name}")
        #pp.pprint(stage)
        stage = pipeline['stages'][stage_name]
        inbox = stage['inbox']
        outbox = stage['outbox']
        print(f"inbox:")
        pp.pprint(inbox)
        print(f"outbox:")
        pp.pprint(outbox)

    return 0


if __name__ == "__main__":
    sys.exit(main())


