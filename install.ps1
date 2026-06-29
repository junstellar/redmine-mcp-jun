<#
.SYNOPSIS
    Windows 사용자용 redmine-mcp 설치 wrapper.
    내부적으로 pip install + redmine-mcp-setup 을 호출합니다.

.DESCRIPTION
    macOS/Linux 사용자는 그냥 터미널에서:
        pipx install git+https://github.com/junstellar/redmine-mcp-jun.git
        redmine-mcp-setup
    하면 됩니다. 이 스크립트는 Windows에서 같은 작업을 한 번에 해주는 편의용입니다.

.PARAMETER ApiKey
    Redmine API 키. 생략하면 redmine-mcp-setup이 콘솔에서 안전하게 입력받음.

.PARAMETER RedmineUrl
    Redmine 서버 주소 (예: https://redmine.example.com). 생략하면 설치 중 입력받음.

.PARAMETER Force
    이미 등록되어 있어도 덮어쓰기.

.PARAMETER FromLocal
    git 저장소 대신 현재 폴더(`pip install -e .`)에서 설치. 개발/오프라인 시 사용.

.EXAMPLE
    .\install.ps1

.EXAMPLE
    .\install.ps1 -RedmineUrl "https://redmine.example.com" -ApiKey "여기에_본인_키" -Force
#>

[CmdletBinding()]
param(
    [string]$ApiKey = "",
    [string]$RedmineUrl = "",
    [switch]$Force,
    [switch]$FromLocal
)

$ErrorActionPreference = "Stop"
$RepoUrl = "git+https://github.com/junstellar/redmine-mcp-jun.git"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "===== Redmine MCP 설치 (Windows wrapper) =====" -ForegroundColor Cyan
Write-Host ""

# 1. Python 확인
Write-Host "[1/3] Python 확인..." -ForegroundColor Yellow
try {
    $pyVersion = (& python --version 2>&1).ToString()
    if ($pyVersion -notmatch "Python 3\.(1[0-9]|[2-9][0-9])") {
        Write-Warning "Python 3.10 이상 권장. 현재: $pyVersion"
    } else {
        Write-Host "  $pyVersion" -ForegroundColor Green
    }
} catch {
    Write-Error "Python이 PATH에 없습니다. https://www.python.org 에서 설치 후 다시 실행하세요."
    exit 1
}

# 2. pip install
Write-Host ""
Write-Host "[2/3] pip install..." -ForegroundColor Yellow
if ($FromLocal) {
    Write-Host "  로컬 폴더에서 설치: $ScriptDir"
    & python -m pip install -e $ScriptDir
} else {
    Write-Host "  git 저장소에서 설치: $RepoUrl"
    & python -m pip install $RepoUrl
}
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install 실패"
    exit 1
}
Write-Host "  완료" -ForegroundColor Green

# 3. redmine-mcp-setup
Write-Host ""
Write-Host "[3/3] .claude.json 등록..." -ForegroundColor Yellow

# redmine-mcp-setup이 PATH에 없을 수 있어 python -m 으로 호출 (가장 안전)
$setupArgs = @("-m", "redmine_mcp.installer")
if ($RedmineUrl) { $setupArgs += @("--url", $RedmineUrl) }
if ($ApiKey) { $setupArgs += @("--api-key", $ApiKey) }
if ($Force) { $setupArgs += "--force" }

& python @setupArgs
$setupExit = $LASTEXITCODE

if ($setupExit -eq 0) {
    Write-Host ""
    Write-Host "===== 설치 완료 =====" -ForegroundColor Cyan
} elseif ($setupExit -eq 2) {
    Write-Host ""
    Write-Warning "이미 등록되어 있습니다. -Force 옵션으로 덮어쓰기 가능."
    exit 2
} else {
    Write-Error "설치 실패 (exit $setupExit)"
    exit $setupExit
}
