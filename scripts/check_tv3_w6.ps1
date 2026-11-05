param(
    [string]$Python = "python",
    [string]$Output = "outputs/tv3_w6/checks01",
    [switch]$FullSuite
)

# Invoked by the user. No smoke, feature extraction, official training or Test command.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$null = Get-Command $Python -ErrorAction Stop
foreach ($requiredFile in @('src/evaluation/w6_validation.py', 'tests/test_w6_validation.py', 'tests/test_dino_w6.py')) {
    if (-not (Test-Path -LiteralPath $requiredFile)) { throw "Missing $requiredFile. Merge TV2 W6 before checking." }
}
if (Test-Path -LiteralPath $Output) { throw "Output exists: $Output. Use a new attempt directory." }
$null = New-Item -ItemType Directory -Path $Output
$checks = @()
$commands = @(
    @{ Name = 'environment'; Args = @('scripts/check_environment.py') },
    @{ Name = 'contracts'; Args = @('scripts/validate_results.py') },
    @{ Name = 'w6_tv3'; Args = @('-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_dino_w6.py', '-v') },
    @{ Name = 'w6_tv2'; Args = @('-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_w6_validation.py', '-v') }
)
if ($FullSuite) {
    $commands += @{ Name = 'full_suite'; Args = @('-m', 'unittest', 'discover', '-s', 'tests', '-v') }
}
foreach ($item in $commands) {
    $started = Get-Date
    $log = Join-Path $Output ($item.Name + '.log')
    $argv = $item.Args
    # unittest writes normal progress to stderr. Capture both native streams
    # directly, so Windows PowerShell does not wrap passing tests as errors.
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = (Get-Command $Python -ErrorAction Stop).Source
    # Arguments here are fixed tokens above, with no user-supplied shell text.
    $startInfo.Arguments = (@('-X', 'utf8') + $argv) -join ' '
    $startInfo.WorkingDirectory = (Get-Location).Path
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $startInfo.StandardErrorEncoding = [System.Text.Encoding]::UTF8
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    try {
        $null = $process.Start()
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        $exitCode = $process.ExitCode
        $logText = $stdoutTask.GetAwaiter().GetResult() + $stderrTask.GetAwaiter().GetResult()
        [System.IO.File]::WriteAllText((Join-Path (Get-Location) $log), $logText, [System.Text.UTF8Encoding]::new($false))
    }
    finally { $process.Dispose() }
    $checks += @{
        name = $item.Name
        command = @($Python, '-X', 'utf8') + $argv
        exit_code = $exitCode
        seconds = ((Get-Date) - $started).TotalSeconds
        log = $log
        log_sha256 = (Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $checks | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Output 'checks.json') -Encoding UTF8
    Get-Content -LiteralPath $log -Encoding UTF8
    if ($exitCode -ne 0) { throw "Check failed: $($item.Name). Stop here; inspect $log." }
}
Write-Output "Requested checks passed. Evidence: $Output. GPU smoke and official training have NOT been run."
