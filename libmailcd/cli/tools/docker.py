import subprocess
import logging

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
    res = _run_cmd([
        "C:\Program Files\Docker\Docker\dockercli.exe", # TODO(Matthew): need to detect where this is? or ask user to put it in path?
        "-SwitchWindowsEngine"
    ])

    time.sleep(5) # TODO(Matthew): Need to find a way to query so we don't have to sleep
    #_print_result(res)

def os_linux():
    res = _run_cmd([
        "C:\Program Files\Docker\Docker\dockercli.exe",
        "-SwitchLinuxEngine"
    ])

    time.sleep(5) # TODO(Matthew): Need to find a way to query so we don't have to sleep
    #_print_result(res)

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

def start(image):
    result = _run_cmd([
        "docker", "run",
        "-td",
        f"{image}",
    ])
    return result.stdout.strip()

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
