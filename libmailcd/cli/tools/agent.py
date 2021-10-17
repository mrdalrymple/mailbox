import os
import subprocess
import logging

from libmailcd.cli.tools import docker
from libmailcd.utils import hash_file

from libmailcd.constants import PIPELINE_CONTAINERFILE_SEPARATOR
from libmailcd.constants import PIPELINE_CONTAINERFILE_OS_WINDOWS
from libmailcd.constants import PIPELINE_CONTAINERFILE_OS_LINUX

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

class LocalNode(NodeInterface):
    def __init__(self):
        pass

    def run_step(self, step):
        return _run_cmd([
            "cmd", "/c",
            f"{step}"
        ])

class LocalDockerNode(LocalNode):
    def __init__(self, image):
        self._handle = None
        self.image = image

    def __enter__(self):
        self._handle = docker.start(self.image)

    def __exit__(self, exc_type, exc_value, tb):
        if self._handle:
            docker.stop(self._handle)
        self._handle = None

    def run_step(self, step):
        return docker.exec(self._handle, step)

class LocalDockerLinuxNode(LocalDockerNode):
    def run_step(self, step):
        return docker.linux_exec(self._handle, step)

class LocalDockerWindowsNode(LocalDockerNode):
    def run_step(self, step):
        return docker.windows_exec(self._handle, step)

##########################

def factory(node_dict):
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
            node = LocalDockerWindowsNode(container_hash)
        else:
            node = LocalDockerLinuxNode(container_hash)
    else:
        node = LocalNode()

    return node

##########################