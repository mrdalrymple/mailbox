import subprocess

#import libmailcd.cli.tools.docker as docker
from libmailcd.cli.tools import docker
from libmailcd.utils import hash_file

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

class LocalNode():
    def __init__(self):
        pass

    def run_step(self, step):
        return _run_cmd([
            "cmd", "/c",
            f"{step}"
        ])

class LocalDockerNode():
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

##########################

def factory(node_dict):
    if not node_dict:
        node = LocalNode()
    else:
        # This is getting gross, how to handle the docker cache system? Should not go into the library for sure.  Should be implemented at the cli / default API.  The whole node factory should be implemented by the cli.

        stage_node_container_file = node_dict['container']

        # Should build container?
        container_hash = hash_file(stage_node_container_file)
        #print(f"container_hash={container_hash}")

        found_images = docker.images_get()
        if container_hash not in found_images:
            print("Container not found, building...")
            docker.build(stage_node_container_file, container_hash)
            pass

        node = LocalDockerNode(container_hash)

    return node

##########################
