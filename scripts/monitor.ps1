# WOCS RAG Bot - GitHub Traffic Monitor
# Usage:
#   powershell.exe -ExecutionPolicy Bypass -File scripts/monitor.ps1
#   (or from a PowerShell prompt: .\scripts\monitor.ps1)
#
# Shows last 14-day views and clones for the public WOCS RAG Bot repo.
# Flags any day whose "count" exceeds a threshold (default 100) as suspicious.

param(
    [string]$Repo      = "cryptowoosung/wocs-ragbot",
    [int]   $Threshold = 100
)

# --- Preconditions ------------------------------------------------------

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] gh (GitHub CLI) not found. Install: https://cli.github.com/" -ForegroundColor Red
    exit 1
}

gh auth status 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] gh not authenticated. Run: gh auth login" -ForegroundColor Red
    exit 1
}

# --- Header -------------------------------------------------------------

Write-Host "== WOCS RAG Bot traffic (last 14 days) ==" -ForegroundColor Cyan
Write-Host ("Repo      : {0}" -f $Repo)
Write-Host ("Threshold : {0} / day (HIGH flag)" -f $Threshold)
Write-Host ("-" * 64)

# --- Core fetch + render ------------------------------------------------

function Show-Traffic {
    param(
        [Parameter(Mandatory = $true)][string] $Kind,     # "views" or "clones"
        [Parameter(Mandatory = $true)][string] $DailyKey  # json array property name
    )

    $json = gh api "repos/$Repo/traffic/$Kind" 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $json) {
        Write-Host ("[ERROR] Failed to fetch {0} (need push access / repo scope)" -f $Kind) -ForegroundColor Red
        return
    }

    $data  = $json | ConvertFrom-Json
    $daily = $data.$DailyKey

    Write-Host ""
    Write-Host ("-- {0} --" -f $Kind) -ForegroundColor Yellow
    Write-Host ("  Total : {0,6}    Uniques : {1,6}" -f $data.count, $data.uniques)

    if (-not $daily -or $daily.Count -eq 0) {
        Write-Host "  (no daily data in the 14-day window)"
        return
    }

    Write-Host ""
    Write-Host ("  {0,-12} {1,8} {2,8}   {3}" -f "date", "count", "uniques", "flag")

    $maxCount   = 0
    $warnDay    = [Math]::Max(1, [Math]::Floor($Threshold / 2))
    $anyHigh    = $false

    foreach ($row in $daily) {
        $date = ($row.timestamp -split "T")[0]
        $flag = ""
        $clr  = "White"
        if ($row.count -ge $Threshold) {
            $flag    = "!! HIGH (>= $Threshold)"
            $clr     = "Red"
            $anyHigh = $true
        }
        elseif ($row.count -ge $warnDay) {
            $flag = ".. watch"
            $clr  = "Yellow"
        }
        if ($row.count -gt $maxCount) { $maxCount = $row.count }
        Write-Host ("  {0,-12} {1,8} {2,8}   {3}" -f $date, $row.count, $row.uniques, $flag) -ForegroundColor $clr
    }

    Write-Host ""
    Write-Host ("  peak-day count : {0}" -f $maxCount)
    if ($anyHigh) {
        Write-Host "  >>> at least one day exceeded threshold. Investigate referrer/clone source." -ForegroundColor Red
    }
}

Show-Traffic -Kind "views"  -DailyKey "views"
Show-Traffic -Kind "clones" -DailyKey "clones"

# --- Footer -------------------------------------------------------------

Write-Host ""
Write-Host ("-" * 64)
Write-Host ("done: {0:yyyy-MM-dd HH:mm}" -f (Get-Date)) -ForegroundColor Green
