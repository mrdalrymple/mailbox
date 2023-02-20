import os
import logging
from pathlib import Path
import shutil

import libmailcd.storage
import libmailcd.errors
from libmailcd.constants import PIPELINE_COPY_SEPARATOR
from libmailcd.constants import LOCAL_OUTBOX_DIRNAME # Note(matthew): The use of this variable should be refactored (should not include this here)

from libmailcd.cli.tools import agent
from libmailcd.cli.common.constants import LOG_FILE_EXTENSION
from libmailcd.cli.common.constants import ENV_LOG_FILE_EXTENSION

########################################

def get_outboxes(pipeline_outbox, mb_outbox_path):
    outboxes = {}

    for storage_id in pipeline_outbox:
        outboxes[storage_id] = Path(mb_outbox_path, storage_id)

    return outboxes


def pipeline_outbox_deploy(api, pipeline_outbox):
    packages_to_upload = [] # all packages that need to be uploaded

    mb_outbox_path = api.settings("outbox_root")
    outboxes = get_outboxes(pipeline_outbox, mb_outbox_path)

    # Calculate all packages that need to be uploaded
    # TODO(matthew): need to make sure an upload of an empty directory
    #   doesnt work
    #  i.e. we add this storage id to upload, but we are not sure that any
    #   file will actually be copied into it.
    for outbox in outboxes:
        storage_id = outbox
        target_path = outboxes[outbox]
        packages_to_upload.append(
            libmailcd.workflow.PackageUpload(storage_id, target_path)
        )

    for ptu in packages_to_upload:
        print(f"Upload {ptu.storage_id}")
        if os.path.exists(ptu.package_path):
            package_hash = api.store_add(ptu.storage_id, ptu.package_path)
            print(f" as: {package_hash}")
        else:
            print(f" nothing to store for: {ptu.storage_id} (empty)")

    return packages_to_upload

# TODO(Matthew): this should be reused between stage and pipeline outboxes
def pipeline_outbox_run(workspace, layout_outbox, pipeline_outbox):
    if not pipeline_outbox:
        raise ValueError("No outbox set")

    mb_outbox_path = layout_outbox.root
    #mb_local_root = api.settings("local_root_relative")
    mb_local_root = layout_outbox.root

    outboxes = get_outboxes(pipeline_outbox, mb_outbox_path)

    _exec_outbox_rules(
        mb_local_root=mb_local_root,
        workspace=workspace,
        outbox=pipeline_outbox,
        outboxes=outboxes
    )


def pipeline_inbox_run(inbox_layout, pipeline_inbox):
    if not pipeline_inbox:
        raise ValueError("No inbox set")

    env_vars = {}
    inbox_packages = [] # all packages
    packages_to_download = [] # all packages that need to be downloaded

    # Find required packages
    for slot in pipeline_inbox:
        logging.debug(f"{slot}")

        tag = pipeline_inbox[slot]['tag']
        logging.debug(f"tag={tag}")

        labels = tag
        storage_id = slot

        matches = libmailcd.storage.find(storage_id, labels)
        if len(matches) > 1:
            raise libmailcd.errors.StorageMultipleFound(storage_id, matches, f"multiple found in store '{storage_id}' with labels: {labels}")
        if not matches:
            raise ValueError(f"No matches found for '{storage_id}' with labels: {labels}")
        package_hash = matches[0]

        pkg = {
            "id": storage_id,
            "hash": package_hash
        }

        packages_to_download.append(pkg)
        inbox_packages.append(pkg)

    # Download all required packages
    if packages_to_download:

        # TODO(matthew): Do we need to optimize this to only actually download ones we don't already have
        for package in packages_to_download:
            storage_id = package['id']
            package_hash = package['hash']
            print(f"Downloading package: {storage_id}/{package_hash}")

            # calculate target directory
            target_path = inbox_layout.get_package_path(storage_id, package_hash)

            # download to the target directory
            libmailcd.storage.download(storage_id, package_hash, target_path)
            print(f" --> '{target_path}'")

    # Set env variables that point to the inbox packages
    for package in inbox_packages:
        env_var_name = f"MB_{storage_id}_ROOT"
        env_var_value = str(target_path)
        env_vars[env_var_name] = env_var_value

    return env_vars

def pipeline_set_env(mb_inbox_env_vars, mb_env_path):
    # Note: Order matters here! Should inbox overwrite loaded env? Or vice versa?
    # For now, we prefer loaded env over inbox env vars.  This should give users
    #  the ability to load envs that overwrite the normal behavior.  However, this
    #  case really shouldn't happen, but we should still make a decision here.
    # I haven't thought this through enough, and could be persuaded either way.

    loaded_env = libmailcd.env.get_variables(mb_env_path)

    # Merge environment dicts
    env_vars = {**mb_inbox_env_vars, **loaded_env}

    # Set all variables into the environment
    for key, value in env_vars.items():
        logging.debug(f"SET {key}={value}")
        os.environ[key] = value

    return env_vars

def _expand_variables_from_env(string_to_expand, env): #for stage

    for e in env:
        print("e={e}")

    return string_to_expand

def _pipeline_process_stage(api, workspace, stage, stage_name, logpath, envlogpath, env):
    print(f"> Starting Stage: {stage_name}")

    if 'node' not in stage:
        raise ValueError(f"No 'node' block in stage: {stage_name}")

    node = agent.factory(stage['node'], workspace, env)

    logpath = logpath.resolve()
    envlogpath = envlogpath.resolve()
    stage_steps = None
    stage_outboxes = None
    with open(logpath, 'w') as logfp:
        if 'steps' in stage:
            stage_steps = stage['steps']

        if 'outbox' in stage:
            stage_outboxes = stage['outbox']

        # Allocate a node if we have steps to run and/or outbox to make
        if stage_steps or stage_outboxes:

            with node:

                if stage_steps:
                    env_result = node.get_env()
                    with open(envlogpath, 'w') as envfp:
                        env_output = env_result.stdout.strip().replace("\r\n", "\n")
                        if env_output:
                            envfp.write(env_output + "\n")
                        pass
                    #print(f"{env_result.stdout}")

                    # Process
                    for step in stage_steps:
                        step = _expand_variables_from_env(step.strip(), env).strip()
                        print(f"{stage_name}> {step}")
                        result = node.run_step(step)

                        result_output = result.stdout.strip().replace("\r\n", "\n")
                        if result_output:
                            logfp.write(result_output + "\n")
                            print(result_output)
                        print(f"{stage_name}?> {result.returncode}")

                if stage_outboxes:
                    _stage_outbox_run(api, stage_name, stage_outboxes)

#def _stage_inbox_run(api, stage, stage_inbox):
#    pass

# TODO(matthew): this function should go into the API / some get path api
def _get_stage_outbox_root(api, stage):
    mb_stage_relpath = api.settings("stage_root_relative")

    return Path(mb_stage_relpath, stage, LOCAL_OUTBOX_DIRNAME)

def _stage_outbox_run(api, stage, stage_outbox):
    stage_outbox_root = _get_stage_outbox_root(api, stage)
    mb_local_root = api.settings("local_root_relative")
    root_path = api.settings("workspace")
    
    # Copy files into outbox
    logging.debug(f"outbox root={stage_outbox_root}")

    outboxes = get_outboxes(stage_outbox, stage_outbox_root)

    _exec_outbox_rules(
        mb_local_root=mb_local_root,
        workspace=root_path,
        outbox=stage_outbox,
        outboxes=outboxes
    )

# todo(matthew): maybe instead of passing in mb_local_root, we pass in directories to ignore and add that to the list
def _exec_outbox_rules(mb_local_root, workspace, outbox, outboxes):
    files_to_copy = {} # all the file copy rules

    for storage_id in outboxes:
        logging.debug(f"{storage_id}")
        rules = outbox[storage_id]
        logging.debug(f"rules={rules}")

        target_path = outboxes[storage_id]

        files_to_copy[storage_id] = {}

        for rule in rules:
            files_to_copy[storage_id][rule] = []

            source, destination = rule.split(PIPELINE_COPY_SEPARATOR)
            source = source.strip()
            destination = destination.strip()

            # Support destinations starting with "/" (in Windows)
            #  and not have it think it's the root of the drive
            #  but instead the root of the output path
            # TODO(matthew): What about linux?
            if os.name == 'nt':
                destination = destination.lstrip('/\\')

            logging.debug(f"src='{source}'")
            logging.debug(f"dst='{destination}'")
            logging.debug(f"target='{target_path}'")

            # TODO(matthew): What about the case where we may want to grab
            #  something from a pulled in package?  Shouldn't always assume
            #  searching from the workspace, but how to implement this?
            # Maybe do this format:
            #   "WORKSPACE: *.txt -> /docs/"
            #   "LUA: *.dll -> /external/lua/"
            found_files = workspace.glob("**/" + source)
            mb_local_root_str = str(mb_local_root)

            for ffile in found_files:
                # Ignore files that are in the local mailbox root (that's our stuff)
                if str(ffile).startswith(mb_local_root_str):
                    logging.debug(f"Ignoring -- {mb_local_root_str}")
                    continue

                ffile_source_path = ffile

                # get filename
                ffilename = ffile.name

                # generate output path
                ffile_destination_path = Path.joinpath(target_path, destination, ffilename)

                # copy file (or save it to a list to be copied later)
                files_to_copy[storage_id][rule].append(
                    libmailcd.workflow.FileCopy(ffile_source_path, ffile_destination_path, rule=rule)
                )

    if files_to_copy:
        #print(f"ftc={files_to_copy}")
        for sid in files_to_copy:
            logging.info(f"{sid}:")
            if files_to_copy[sid]:
                for rule in rules:
                    logging.info(f"- {rule}")
                    files = files_to_copy[sid][rule]
                    if files:
                        for ftc in files:
                            # TODO(Matthew): Make this ftc.dst_relative output be a debug output, instead
                            #  print how to access it via the generated root variable (example: MB_LIB_ROOT/lib/mylib.lib).
                            logging.info(f"-- Copy {ftc.src_relative} => {ftc.dst_relative}")
                            os.makedirs(ftc.dst_root, exist_ok=True)
                            shutil.copy(ftc.src, ftc.dst)
                    else:
                        logging.info("-- No matching files to copy")
                        pass
            else:
                logging.info("- No rules found")

class StageTreeNode:
    def __init__(self, name):
        self.dependencies = None
        self.name = name

    def add_dependency(self, dependency):
        if self.dependencies is None:
            self.dependencies = []
        self.dependencies.append(dependency)

from collections import defaultdict

class Graph:
    def __init__(self, nodes):
        self._edges = defaultdict(list)
        self._nodes = nodes

    def edge(self, origin, target):
        #print(f"EDGE: {origin} -> {target}")
        self._edges[origin].append(target)

    def _topo_sort_util(self, origin_node, visited, stack):
        visited.append(origin_node)

        #print(f"EDGES({origin_node})={self._edges[origin_node]}")
        for target_node in self._edges[origin_node]:
            if target_node not in visited:
                self._topo_sort_util(target_node, visited, stack)

        stack.append(origin_node)

    def topological_sort(self):
        visited_nodes = []
        sorted_nodes = [] # this will be a stack

        #print(f"topo_nodes: {self._nodes}")
        for node in self._nodes:
            if node not in visited_nodes:
                self._topo_sort_util(node, visited_nodes, sorted_nodes)

        #print(f"visited_nodes={visited_nodes}")

        return sorted_nodes


def _get_stage_dependencies(stages, stage):
    dependent_stages = []

    # Go through inbox and find all the packages that need to be pulled in
    required_packages = []
    if 'inbox' in stages[stage]:
        for node in stages[stage]['inbox']:
            required_packages.append(node)

    # Go through all other stages and see if they have the packages in their outbox
    for other_stage in stages:
        if 'outbox' in stages[other_stage]:
            for node in stages[other_stage]['outbox']:
                if node in required_packages:
                    dependent_stages.append(other_stage)

    return dependent_stages


def _get_stage_order_sequential(stages):
    ordered_stages = []
    #print(f"!!stages={stages}")

    deps = {}
    for stage in stages:
        d = _get_stage_dependencies(stages, stage)
        deps[stage] = d
        print(f"{stage}.deps={d}")

    # TODO(Matthew): maybe re-do with some zip() usage?
    stage_graph = Graph(stages)

    for stage in stages:
        # stage_graph.addEdges(stage, stage.deps) # this way I can add a bunch of edges at once.
        for dstage in deps[stage]:
            stage_graph.edge(stage, dstage)

    sorted_graph = stage_graph.topological_sort()
    #print(f"sorted_graph={sorted_graph}")
    ordered_stages = sorted_graph
    #print(f"ordered_stages={ordered_stages}")

    return ordered_stages

def pipeline_stages_run(api, workspace, pipeline_stages, logpath, env):
    # TODO(Matthew): Should do a schema validation here (or up a level) first,
    #  so we can give line numbers for issues to the end user.

    # Build dependency tree
    ordered_stages = _get_stage_order_sequential(pipeline_stages)
    logging.debug(f"Stage Order: {ordered_stages}")

    # TODO(Matthew): Should not just loop through and execute, need to build dependency tree
    stage_no = 0
    for stage_name in ordered_stages:
        stage = pipeline_stages[stage_name]
        stage_no = stage_no + 1
        #print(f"STAGE#{stage_no}: {stage_name}")

        logfilepath = Path(logpath, f"{stage_name}{LOG_FILE_EXTENSION}")
        envlogfilepath = Path(logpath, f"{stage_name}{ENV_LOG_FILE_EXTENSION}")
        _pipeline_process_stage(
            api,
            workspace,
            stage,
            stage_name,
            logpath=logfilepath,
            envlogpath=envlogfilepath,
            env=env
        )
