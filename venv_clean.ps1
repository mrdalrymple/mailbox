$venv_dirname = "venv"
$path = Join-Path -Path "." -ChildPath "$venv_dirname"

if((Test-Path $path)) {
    Write-Output "Cleaning $path..."
    Remove-Item -path $path -Recurse
} else {
    Write-Output "Nothing to clean..."
}
