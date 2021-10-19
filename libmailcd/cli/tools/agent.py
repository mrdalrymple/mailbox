import os
import subprocess
import logging

from libmailcd.cli.tools import docker
from libmailcd.utils import hash_file

from libmailcd.constants import PIPELINE_CONTAINERFILE_SEPARATOR
from libmailcd.constants import PIPELINE_CONTAINERFILE_OS_WINDOWS
from libmailcd.constants import PIPELINE_CONTAINERFILE_OS_LINUX
from libmailcd.constants import AGENT_CONTAINER_WORKSPACE

##########################

def _print_result(result):
    print(f"CMD: " + " ".join(result.args))
    print(f"RC: {result.returncode}")
    if result.stdout:
        print(f"STDOUT:")
        print(result.stdout)
    if result.stderr:
        print(f"STDERR:")
        print(result.stderr)

def _run_cmd(args):
    result = subprocess.run(
        args,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    result.stdout = result.stdout.decode()
    result.stderr = result.stderr.decode()

    return result

##########################

from abc import ABC, abstractmethod

class NodeInterface(ABC):
    @abstractmethod
    def run_step(self, step):
        pass

    @abstractmethod
    def get_env(self):
        pass

class LocalNode(NodeInterface):
    def __init__(self, workspace):
        self.workspace = workspace

    def __enter__(self):
        self._previous_cwd = os.getcwd()
        os.chdir(self.workspace)

    def __exit__(self):
        os.chdir(self._previous_cwd)
        self._previous_cwd = None

    def run_step(self, step):
        return _run_cmd([
            "cmd", "/c",
            f"{step}"
        ])

    def get_env(self):
        return _run_cmd([
            "cmd", "/c",
            f"SET"
        ])

class LocalDockerNode(LocalNode):
    def __init__(self, image, host_workspace, env):
        self._handle = None
        self.image = image
        self.host_workspace = host_workspace
        self.container_workspace = AGENT_CONTAINER_WORKSPACE
        self.env = env

    def __enter__(self):
        self._handle = docker.start(
            self.image,
            self.host_workspace,
            self.container_workspace,
            env=self.env
        )

    def __exit__(self, exc_type, exc_value, tb):
        if self._handle:
            docker.stop(self._handle)
        self._handle = None


class LocalDockerLinuxNode(LocalDockerNode):
    def run_step(self, step):
        return docker.linux_exec(self._handle, step)

    def get_env(self):
        return docker.linux_exec(self._handle, "set")

class LocalDockerWindowsNode(LocalDockerNode):
    def __init__(self, image, host_workspace, env):
        super().__init__(image, host_workspace, env)
        self.container_workspace = f"C:{self.container_workspace}"

    def run_step(self, step):
        return docker.windows_exec(self._handle, step)

    def get_env(self):
        return docker.windows_exec(self._handle, "SET")

##########################

def factory(node_dict, workspace, env):
    host_workspace = workspace
    if node_dict:
        # This is getting gross, how to handle the docker cache system? Should not go into the library for sure.  Should be implemented at the cli / default API.  The whole node factory should be implemented by the cli.

        containerfile_ref = str(node_dict['containerfile'])

        containerfile = containerfile_ref
        containerfile_os = PIPELINE_CONTAINERFILE_OS_LINUX # set default to windows .. for now -- also should come in via settings

        # If the user specified the OS, use it instead of the default
        if PIPELINE_CONTAINERFILE_SEPARATOR in containerfile_ref:
            containerfile_os, containerfile = containerfile_ref.split(PIPELINE_CONTAINERFILE_SEPARATOR)

        # Should build container?
        container_hash = hash_file(containerfile)
        logging.debug(f"container_hash={container_hash}")

        # TODO(Matthew): I think if you use the default dockerfile OS, but point to a wrong dockerfile, the error the user is not clear (and nothing actually fails).

        if os.name == "nt":
            # Windows supports Linux and Windows containers, but the Docker Desktop needs to switch modes before you can launch containers for that OS-type.
            if containerfile_os == PIPELINE_CONTAINERFILE_OS_WINDOWS:
                docker.os_windows()
            else:
                docker.os_linux()
        else:
            if containerfile_os == PIPELINE_CONTAINERFILE_OS_WINDOWS:
                raise ValueError(f"Windows containers are not supported for this OS ({os.name}).")

        found_images = docker.images_get()
        if container_hash not in found_images:
            print(f"Container not found, building '{containerfile_os}{PIPELINE_CONTAINERFILE_SEPARATOR}{containerfile}' ({container_hash})")
            docker.build(containerfile, container_hash, os=containerfile_os)
            pass

        if containerfile_os == "windows":
            node = LocalDockerWindowsNode(container_hash, host_workspace, env)
        else:
            node = LocalDockerLinuxNode(container_hash, host_workspace, env)
    else:
        node = LocalNode(host_workspace)

    return node

##########################
