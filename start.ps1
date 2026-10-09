$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
Set-Location $PSScriptRoot
$pythonExe = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Lancez install.ps1 avant de démarrer.' }
& $pythonExe scripts/prepare_database.py
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL ne peut pas démarrer. Consultez runtime/postgres.log.' }
& $pythonExe -m alembic -c backend/alembic.ini upgrade head
if ($LASTEXITCODE -ne 0) { throw 'La migration de la base a échoué.' }
if (-not (Test-Path frontend/dist/index.html)) { throw 'Interface absente. Lancez install.ps1.' }
Write-Host 'Déchets urbains : http://127.0.0.1:8001'
& $pythonExe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
