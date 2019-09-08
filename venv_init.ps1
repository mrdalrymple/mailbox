# Construct path variables
$venv_dirname = "venv"
$path = Join-Path -Path "." -ChildPath "$venv_dirname"
$activate_path = Join-Path -Path "." -ChildPath "$path"
$activate_path = Join-Path -Path "$activate_path" -ChildPath "Scripts"
$activate_path = Join-Path -Path "$activate_path" -ChildPath "activate.ps1"

# Create the virtual env if it isn't already created
if(-not (Test-Path $path)) {
    py -3 -m virtualenv $path
    Invoke-Expression $activate_path
    pip install -r requirements.txt
    pip install -e .
}
#else {
#    Write-Output "Path Exists: $path"
#}

# Load in the virtual env if it isn't already loaded
if(-not (Test-Path env:VIRTUAL_ENV)) {
    #Write-Output "No virtual env"
    Invoke-Expression $activate_path
}

#Write-Output "Virtual Env: $env:VIRTUAL_ENV"
