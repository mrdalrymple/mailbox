import shutil
import subprocess
import logging

from pathlib import Path

import docker

def _print_result_(result):
    return result

def _print_result(result):
    logging.debug(f"CMD: " + " ".join(result.args))
    logging.debug(f"RC: {result.returncode}")
    if result.stdout:
        logging.debug(f"STDOUT:")
        logging.debug(result.stdout)
    if result.stderr:
        logging.debug(f"STDERR:")
        logging.debug(result.stderr)
    return result

def _run_cmd(args):
    result = subprocess.run(
        args,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    result.stdout = result.stdout.decode()
    result.stderr = result.stderr.decode()

    return result

def _images_from_output(output):
    images = []

    for line in output.splitlines():
        if line.startswith('REPOSITORY'):
            continue

        columns = line.split()
        column_repo = columns[0]
        images.append(column_repo)

    return images

##########################

import time

def os_windows():
    #logging.debug("DOCKER: OS WINDOWS SWITCH")
    docker_cli = docker_cli_path()
    res = _run_cmd([
        f"{docker_cli}",
        "-SwitchWindowsEngine"
    ])
    #_print_result(res)

    #logging.debug("DOCKER: OS WINDOWS SWITCH -- WAIT")
    docker_wait_until_up()
    #logging.debug("DOCKER: OS WINDOWS SWITCH -- OVER")


def os_linux():
    #logging.debug("DOCKER: OS LINUX SWITCH")
    docker_cli = docker_cli_path()
    res = _run_cmd([
        f"{docker_cli}",
        "-SwitchLinuxEngine"
    ])
    #_print_result(res)

    #logging.debug("DOCKER: OS LINUX SWITCH -- WAIT")
    docker_wait_until_up()
    #logging.debug("DOCKER: OS LINUX SWITCH -- OVER")

MAX_CHECK_FAILURES = 10  # TODO(Matthew): if this becomes an issue, move this up as a setting
def docker_wait_until_up():
    for _ in range(0, MAX_CHECK_FAILURES):
        res_version = version()
        if res_version.returncode == 0:
            break
        else:
            #logging.debug(f"VERSION-RC: {res_version.returncode}")
            pass
        time.sleep(1)

def is_installed():
    which_docker = shutil.which("docker")
    if which_docker is not None:
        return True
    return False

def is_running():
    try:
        client = docker.from_env()
        return client.ping()
    except docker.errors.DockerException:
        return False

docker_install_root_cache = None
def docker_install_location():
    global docker_install_root_cache
    if not docker_install_root_cache:
        # Determine install root based on relative path to docker executable
        docker_install_root_cache = Path(shutil.which("docker"))

        # Example Windows Install: C:\Program Files\Docker\Docker\resources\bin\docker.EXE
        docker_install_root_cache = docker_install_root_cache.parent.parent.parent
        #  Return: C:\Program Files\Docker\Docker\

    return docker_install_root_cache

docker_cli_path_cache = None
def docker_cli_path():
    global docker_cli_path_cache
    if not docker_cli_path_cache:
        docker_root = docker_install_location()
        docker_cli_path_cache = Path(docker_root, "dockercli.exe")
    return docker_cli_path_cache


##########################

def images_get():
    result = _run_cmd(["docker", "images"])
    #_print_result(result)
    return _images_from_output(result.stdout)

def build(dockerfile, label, os):
    res = _run_cmd([
        "docker", "build",
        "-f", f"{dockerfile}",
        "-t", f"{label}",
        "."
    ])
    _print_result(res)

def start(image, host_workspace, container_workspace, env):
    env_args = []

    if env:
        # Is this method sustainable? How many env variables can it take?
        # Might need to switch to an environment file instead
        for key, value in env.items():
            env_args.append('-e')
            env_args.append(f"{key}={value}")

    result = _print_result(_run_cmd(
        [
            "docker", "run",
            f"-v", f"{host_workspace}:{container_workspace}",
            "-w", container_workspace
        ] + env_args + [
            "-td",
            f"{image}",
        ]
    ))
    return result.stdout.strip()

def version():
    return _run_cmd([
        "docker", "version"
    ])

def stop(handle):
    _run_cmd([
        "docker", "stop",
        f"{handle}"
    ])

def windows_exec(handle, cmd):
    return _print_result(_run_cmd([
       "docker", "exec",
       f"{handle}",
       f"cmd", f"/c", f"{cmd}"
    ]))

def linux_exec(handle, cmd):
    return _print_result(_run_cmd([
       "docker", "exec",
       f"{handle}",
       f"sh", "-c", f"{cmd}"
    ]))
