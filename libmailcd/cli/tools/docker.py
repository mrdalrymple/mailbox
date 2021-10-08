import subprocess

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

def images_get():
    result = _run_cmd(["docker", "images"])
    #_print_result(result)
    return _images_from_output(result.stdout)

def build(dockerfile, label):
    _run_cmd([
        "docker", "build",
        "-f", f"{dockerfile}",
        "-t", f"{label}",
        "."
    ])

def start(image):
    if True:
        result = _run_cmd([
            "docker", "run",
            "-td",
            f"{image}",
        ])
        return result.stdout.strip()
    else:
        return "a777fd12"

def stop(handle):
    if True:
        _run_cmd([
            "docker", "stop",
            f"{handle}"
        ])

def exec(handle, cmd):
    return _run_cmd([
       "docker", "exec",
       f"{handle}",
       f"cmd", f"/c", f"{cmd}"
    ])
