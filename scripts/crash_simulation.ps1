# Crash Simulation Script for Demo 5 (PowerShell)
# Simulates a crash during backup by killing the process after a delay

param(
    [string]$DatasetPath = "dataset/",
    [string]$StorePath = "store/",
    [double]$DelaySeconds = 2.0
)

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "  CRASH SIMULATION - Demo 5" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Validate dataset path
if (-not (Test-Path $DatasetPath)) {
    Write-Host "❌ Error: Dataset path not found: $DatasetPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Usage: .\scripts\crash_simulation.ps1 [-DatasetPath <path>] [-StorePath <path>] [-DelaySeconds <seconds>]"
    Write-Host "Example: .\scripts\crash_simulation.ps1 -DatasetPath dataset/ -StorePath store/ -DelaySeconds 2.0"
    exit 1
}

Write-Host "📦 Starting backup process..." -ForegroundColor Yellow
Write-Host "   Dataset: $DatasetPath"
Write-Host "   Store: $StorePath"
Write-Host "   Will crash after: ${DelaySeconds}s"
Write-Host ""

# Build command
$pythonCmd = "python"
$args = @(
    "-m", "src.cli.main",
    "backup", $DatasetPath,
    "--label", "Incomplete - Crashed",
    "--store", $StorePath
)

Write-Host "Command: $pythonCmd $($args -join ' ')"
Write-Host ""

# Start backup process in background
Write-Host "⏳ Backup starting..." -ForegroundColor Yellow

$job = Start-Job -ScriptBlock {
    param($cmd, $arguments)
    & $cmd $arguments
} -ArgumentList $pythonCmd, $args

Write-Host "   Job ID: $($job.Id)"
Write-Host "   Job Name: $($job.Name)"
Write-Host ""

# Wait for specified delay
Write-Host "⏱️  Waiting $DelaySeconds seconds before crash..." -ForegroundColor Yellow

# Show progress while waiting
$elapsed = 0
$interval = 0.5
while ($elapsed -lt $DelaySeconds) {
    Start-Sleep -Milliseconds ($interval * 1000)
    $elapsed += $interval
    
    # Show progress bar
    $percent = [math]::Min(100, ($elapsed / $DelaySeconds) * 100)
    Write-Progress -Activity "Waiting to crash" -Status "$([math]::Round($elapsed, 1))s / ${DelaySeconds}s" -PercentComplete $percent
}

Write-Progress -Activity "Waiting to crash" -Completed

# Kill the process
Write-Host ""
Write-Host "💥 SIMULATING CRASH - Killing backup process..." -ForegroundColor Red

try {
    # Stop the job
    Stop-Job -Job $job -ErrorAction SilentlyContinue
    
    # Get job output before removing
    $output = Receive-Job -Job $job -ErrorAction SilentlyContinue
    
    # Remove the job
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    
    Write-Host "✓ Process killed successfully" -ForegroundColor Green
    Write-Host ""
    
    # Show any output from the process
    if ($output) {
        Write-Host "📄 Process output (before crash):" -ForegroundColor Cyan
        $outputStr = $output | Out-String
        if ($outputStr.Length -gt 500) {
            Write-Host $outputStr.Substring(0, 500)
            Write-Host "... (truncated)"
        } else {
            Write-Host $outputStr
        }
        Write-Host ""
    }
    
} catch {
    Write-Host "⚠️  Error killing process: $_" -ForegroundColor Yellow
}

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "  CRASH SIMULATION COMPLETE" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Green
Write-Host "  1. Check snapshots:" -ForegroundColor Yellow
Write-Host "     python -m src.cli.main list-snapshots --store $StorePath" -ForegroundColor White
Write-Host ""
Write-Host "  2. Retry backup:" -ForegroundColor Yellow
Write-Host "     python -m src.cli.main backup $DatasetPath --store $StorePath" -ForegroundColor White
Write-Host ""
