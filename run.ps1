(get-item $scriptPath ).parent

Invoke-Expression ".\venv_init.ps1"

python .\bin\mailcd.py
$ret = $LASTEXITCODE

Write-Host "Exit Code: $ret"
