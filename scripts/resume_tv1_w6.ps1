# Run from any directory. A published release is verified, never overwritten.
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot
$pythonExe = Join-Path $repoRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Create the project Python environment first.' }

function Invoke-TaskPython {
    param([string[]]$PythonArgs, [switch]$AllowDownloadFailure)
    & $pythonExe -X utf8 @PythonArgs
    if ($LASTEXITCODE -ne 0) {
        if ($AllowDownloadFailure) {
            Write-Warning 'Download had failures; the audit will require a decision for every image and complete holdout coverage.'
        } else {
            throw "Task stopped with Python exit code $LASTEXITCODE. Preserve logs/state and fix the reported cause."
        }
    }
}

if (Test-Path -LiteralPath 'data/processed/train_expansion_w6_v1/provenance.json') {
    Invoke-TaskPython -PythonArgs @('scripts/prepare_tv1_w6.py', 'verify')
    Write-Output 'Published snapshot verified. Do not download/scan over a frozen release. TV2 review is a separate handoff.'
    exit 0
}

# Refuse to launch another downloader/auditor using these task states.
foreach ($statePath in @('data/interim/download_w5_extension', 'data/interim/download_w6_holdout_audit', 'data/interim/train_expansion_w6_v1')) {
    $lockPath = Join-Path $statePath 'active.lock'
    if (Test-Path -LiteralPath $lockPath) {
        $lockText = Get-Content -Raw -LiteralPath $lockPath
        if ($lockText -match '^pid=(\d+) started=\S+\s*$') {
            $ownerId = [int]$Matches[1]
            if (Get-Process -Id $ownerId -ErrorAction SilentlyContinue) {
                throw "Task process $ownerId is still active. Read its log; do not start another writer."
            }
        } else {
            throw "Unreadable lock at $lockPath; inspect without deleting it."
        }
    }
}

Invoke-TaskPython -PythonArgs @('scripts/download_subset.py', '--source', 'data/processed/w5_candidates_v1/train_extension_candidates.jsonl', '--images', 'data/images/swg_w5_extension', '--state', 'data/interim/download_w5_extension', '--log', 'outputs/tv1_w6/train_download_events.jsonl', '--workers', '4') -AllowDownloadFailure
Invoke-TaskPython -PythonArgs @('scripts/download_subset.py', '--source', 'data/processed/w5_candidates_v1/holdout_candidates.jsonl', '--images', 'data/images/swg_w6_holdout_audit', '--state', 'data/interim/download_w6_holdout_audit', '--log', 'outputs/tv1_w6/holdout_download_events.jsonl', '--workers', '2') -AllowDownloadFailure
Invoke-TaskPython -PythonArgs @('scripts/prepare_tv1_w6.py', 'scan')
Invoke-TaskPython -PythonArgs @('scripts/prepare_tv1_w6.py', 'sheets')
if (-not (Test-Path -LiteralPath 'reports/tv1_w6/visual_review.json')) {
    Write-Output 'Download/audit complete. Inspect outputs/tv1_w6/visual_sheets and record the fixed review queue before release. No approval has been fabricated.'
    exit 0
}
Invoke-TaskPython -PythonArgs @('scripts/prepare_tv1_w6.py', 'release')
Invoke-TaskPython -PythonArgs @('scripts/prepare_tv1_w6.py', 'verify', '--check-images')
