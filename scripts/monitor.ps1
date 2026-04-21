# WOCS RAG Bot - GitHub 트래픽 모니터링 (PowerShell)
#
# 사용법:
#   powershell.exe -ExecutionPolicy Bypass -File scripts/monitor.ps1
#   (또는 PowerShell 프롬프트에서 .\scripts\monitor.ps1)
#
# 기능:
#   - 최근 14일 views / clones 일별 카운트
#   - popular paths (인기 경로) 상위 10
#   - referrers (리퍼러) 상위 10
#   - 일 임계치 초과 시 빨간색 "HIGH" 플래그
#   - 전일 대비 5배 이상 급증 시 "SPIKE" 플래그
#   - 실행 결과를 logs/monitor_history.json 에 누적 저장 (비교용)
#
# 사전 조건: gh CLI 설치 + gh auth login 완료

param(
    [string]$Repo       = "cryptowoosung/wocs-ragbot",
    [int]   $Threshold  = 100,
    [double]$SpikeRatio = 5.0
)

$ErrorActionPreference = "Continue"
$histFile = Join-Path (Get-Location) "logs/monitor_history.json"

# --- 전제 조건 확인 ---------------------------------------------------

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "[오류] gh (GitHub CLI) 설치되지 않음." -ForegroundColor Red
    Write-Host "       https://cli.github.com/ 에서 설치 후 재시도." -ForegroundColor Red
    exit 1
}

gh auth status 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[오류] gh 인증되지 않음. 아래 명령 실행:" -ForegroundColor Red
    Write-Host "       gh auth login" -ForegroundColor Red
    exit 1
}

# --- 헤더 -----------------------------------------------------------

Write-Host "== WOCS RAG Bot GitHub 트래픽 모니터 ==" -ForegroundColor Cyan
Write-Host ("Repo      : {0}" -f $Repo)
Write-Host ("임계치    : 일 {0}회 이상 → HIGH  |  전일 대비 x{1} 이상 → SPIKE" -f $Threshold, $SpikeRatio)
Write-Host ("시작 시각 : {0:yyyy-MM-dd HH:mm}" -f (Get-Date))
Write-Host ("-" * 68)

# --- fetch 헬퍼 -----------------------------------------------------

function Get-GhJson {
    param([string]$Path)
    $raw = gh api "repos/$Repo/$Path" 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $raw) { return $null }
    try { return $raw | ConvertFrom-Json } catch { return $null }
}

# --- daily 카운트 출력 + 급증 체크 -----------------------------------

function Show-Daily {
    param(
        [string]$Kind,      # "views" or "clones"
        [string]$DailyKey   # JSON array property name
    )

    $data = Get-GhJson -Path "traffic/$Kind"
    if ($null -eq $data) {
        Write-Host ("[오류] {0} 조회 실패 (push access / repo scope 필요)" -f $Kind) -ForegroundColor Red
        return $null
    }

    Write-Host ""
    Write-Host ("-- {0} --" -f $Kind) -ForegroundColor Yellow
    Write-Host ("  총계 : {0,6}    고유 : {1,6}" -f $data.count, $data.uniques)

    $daily = $data.$DailyKey
    if (-not $daily -or $daily.Count -eq 0) {
        Write-Host "  (14일 창 내 일별 데이터 없음)"
        return $data
    }

    Write-Host ""
    Write-Host ("  {0,-12} {1,8} {2,8}   {3}" -f "날짜", "count", "uniques", "플래그")

    $warnDay = [Math]::Max(1, [Math]::Floor($Threshold / 2))

    for ($i = 0; $i -lt $daily.Count; $i++) {
        $row  = $daily[$i]
        $date = ($row.timestamp -split "T")[0]
        $flag = ""
        $clr  = "White"

        if ($row.count -ge $Threshold) {
            $flag = "!! HIGH (>= $Threshold)"
            $clr  = "Red"
        }
        elseif ($row.count -ge $warnDay) {
            $flag = ".. watch"
            $clr  = "Yellow"
        }

        # 전일 대비 x N배 이상 급증
        if ($i -gt 0) {
            $prev = $daily[$i - 1].count
            if ($prev -ge 1 -and $row.count -ge ($prev * $SpikeRatio)) {
                $ratio = [double]$row.count / [double]$prev
                $flag  = ("!! SPIKE ({0} -> {1}, x{2:N1})" -f $prev, $row.count, $ratio)
                $clr   = "Red"
            }
        }

        Write-Host ("  {0,-12} {1,8} {2,8}   {3}" -f $date, $row.count, $row.uniques, $flag) -ForegroundColor $clr
    }

    return $data
}

# --- popular 리스트 출력 --------------------------------------------

function Show-Top {
    param(
        [string]$Path,
        [string]$Title
    )

    $data = Get-GhJson -Path "traffic/$Path"
    if ($null -eq $data) {
        Write-Host ("[오류] {0} 조회 실패" -f $Title) -ForegroundColor Red
        return $null
    }

    Write-Host ""
    Write-Host ("-- {0} --" -f $Title) -ForegroundColor Yellow

    if ($data.Count -eq 0) {
        Write-Host "  (데이터 없음 — 아직 방문이 적습니다)"
        return $data
    }

    Write-Host ("  {0,6} {1,6}  {2}" -f "count", "uniq", "이름")
    foreach ($row in ($data | Select-Object -First 10)) {
        $name = if ($row.path) { $row.path } else { $row.referrer }
        Write-Host ("  {0,6} {1,6}  {2}" -f $row.count, $row.uniques, $name)
    }

    return $data
}

# --- 실행 -----------------------------------------------------------

$views  = Show-Daily -Kind "views"  -DailyKey "views"
$clones = Show-Daily -Kind "clones" -DailyKey "clones"
$paths  = Show-Top   -Path "popular/paths"     -Title "인기 경로 (paths)"
$refs   = Show-Top   -Path "popular/referrers" -Title "리퍼러 (referrers)"

# --- 히스토리 누적 저장 ---------------------------------------------

if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" | Out-Null }

$entry = [PSCustomObject]@{
    timestamp = (Get-Date).ToString("s")
    views     = $views
    clones    = $clones
    referrers = $refs
    paths     = $paths
}

$all = @()
if (Test-Path $histFile) {
    try {
        $prevRaw = Get-Content $histFile -Raw -Encoding UTF8
        if ($prevRaw) {
            $prev = $prevRaw | ConvertFrom-Json
            if ($prev -isnot [System.Array]) { $prev = @($prev) }
            $all = $prev + $entry
        } else {
            $all = @($entry)
        }
    } catch {
        Write-Host "[경고] 기존 히스토리 파싱 실패, 새 파일로 시작합니다." -ForegroundColor Yellow
        $all = @($entry)
    }
} else {
    $all = @($entry)
}

($all | ConvertTo-Json -Depth 12) | Set-Content -Path $histFile -Encoding UTF8

Write-Host ""
Write-Host ("-" * 68)
Write-Host ("완료 : {0:yyyy-MM-dd HH:mm}  |  히스토리 엔트리 {1}개 저장 -> {2}" -f (Get-Date), $all.Count, "logs/monitor_history.json") -ForegroundColor Green
