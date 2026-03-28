# One-time local env bootstrap (PowerShell). Safe to re-run; does not overwrite existing files.
$root = Split-Path -Parent $PSScriptRoot
$be = Join-Path $root "backend\.env"
$fe = Join-Path $root "frontend\.env.local"
if (-not (Test-Path $be)) {
  Copy-Item (Join-Path $root "backend\.env.example") $be
  Write-Host "Created backend/.env from .env.example"
} else {
  Write-Host "backend/.env already exists — skipped"
}
if (-not (Test-Path $fe)) {
  Copy-Item (Join-Path $root "frontend\.env.example") $fe
  Write-Host "Created frontend/.env.local from .env.example"
} else {
  Write-Host "frontend/.env.local already exists — skipped"
}
Write-Host "Next: see docs/SETUP.md and README.md (Run locally)."
