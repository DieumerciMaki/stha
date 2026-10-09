$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv/Scripts/python.exe')) { py -3.11 -m venv .venv }
& .venv/Scripts/python.exe -m pip install -r backend/requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Installation Python incomplète.' }
Push-Location frontend
try { npm.cmd ci; if ($LASTEXITCODE -ne 0) { throw 'Installation frontend incomplète.' }; npm.cmd run build; if ($LASTEXITCODE -ne 0) { throw 'Compilation frontend échouée.' } } finally { Pop-Location }
& .venv/Scripts/python.exe scripts/download_model.py
if ($LASTEXITCODE -ne 0) { throw 'Installation du modèle échouée.' }
Write-Host 'Installation terminée. Lancez LANCER.cmd.'
