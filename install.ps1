[CmdletBinding()]
param(
    [ValidateSet("auto", "codex", "claude-code", "cursor", "antigravity", "gemini")]
    [string]$Target = $(if ($env:GROK_CLI_TOOLS_TARGET) { $env:GROK_CLI_TOOLS_TARGET } else { "auto" }),
    [switch]$NoAuth,
    [switch]$NoGrokInstall,
    [switch]$NoPythonInstall,
    [string]$ServerName = $(if ($env:SERVER_NAME) { $env:SERVER_NAME } else { "grok-cli" })
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RootDir) { $RootDir = (Get-Location).Path }

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message"
}

function Get-CommandPath {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Invoke-Tool {
    param(
        [string]$File,
        [string[]]$Arguments = @(),
        [switch]$IgnoreErrors
    )
    & $File @Arguments
    $code = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
    if (($code -ne 0) -and (-not $IgnoreErrors)) {
        throw "$File failed with exit code $code"
    }
}

function Add-UserPath {
    param([string]$PathToAdd)
    if (-not (Test-Path $PathToAdd)) {
        New-Item -ItemType Directory -Force -Path $PathToAdd | Out-Null
    }
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $parts = if ($userPath) { $userPath -split ";" } else { @() }
    $trimChars = [char[]]@('\', '/')
    $alreadyPresent = $false
    foreach ($part in $parts) {
        if ($part.TrimEnd($trimChars) -ieq $PathToAdd.TrimEnd($trimChars)) {
            $alreadyPresent = $true
            break
        }
    }
    if (-not $alreadyPresent) {
        $newUserPath = if ($userPath) { "$PathToAdd;$userPath" } else { $PathToAdd }
        [Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
    }
    if (($env:Path -split ";") -notcontains $PathToAdd) {
        $env:Path = "$PathToAdd;$env:Path"
    }
}

function Ensure-Grok {
    $grokBinDir = Join-Path $env:USERPROFILE ".grok\bin"
    Add-UserPath $grokBinDir
    $grok = Get-CommandPath "grok"
    if (-not $grok) {
        $candidate = Join-Path $grokBinDir "grok.exe"
        if (Test-Path $candidate) { $grok = $candidate }
    }
    if ($grok) { return $grok }
    if ($NoGrokInstall) {
        throw "Grok CLI was not found. Install it from https://x.ai/cli or rerun without -NoGrokInstall."
    }

    Write-Step "Grok CLI not found. Installing the official native Windows Grok CLI..."
    $script = Invoke-RestMethod "https://x.ai/cli/install.ps1"
    & ([ScriptBlock]::Create($script))
    Add-UserPath $grokBinDir
    $grok = Get-CommandPath "grok"
    if (-not $grok) {
        $candidate = Join-Path $grokBinDir "grok.exe"
        if (Test-Path $candidate) { $grok = $candidate }
    }
    if (-not $grok) {
        throw "The Grok installer completed, but grok.exe was not found. Open a new PowerShell window and rerun .\install.ps1."
    }
    return $grok
}

function Test-PythonInvocation {
    param([string]$File, [string[]]$Arguments)
    try {
        & $File @Arguments *> $null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Ensure-Python3Shim {
    $binDir = Join-Path $env:LOCALAPPDATA "grok-cli-tools\bin"
    New-Item -ItemType Directory -Force -Path $binDir | Out-Null
    $shim = Join-Path $binDir "python3.cmd"
    $hasPyLauncher = (Get-CommandPath "py") -and (Test-PythonInvocation "py" @("-3", "-c", "import sys; raise SystemExit(0 if sys.version_info[0] == 3 else 1)"))
    $hasPython = (Get-CommandPath "python") -and (Test-PythonInvocation "python" @("-c", "import sys; raise SystemExit(0 if sys.version_info[0] == 3 else 1)"))

    if ((-not $hasPyLauncher) -and (-not $hasPython)) {
        if ($NoPythonInstall) {
            throw "Python 3 was not found. Install Python 3 or rerun without -NoPythonInstall."
        }
        $winget = Get-CommandPath "winget"
        if (-not $winget) {
            throw "Python 3 was not found and winget is unavailable. Install Python 3 from python.org, then rerun .\install.ps1."
        }
        Write-Step "Python 3 not found. Installing Python 3.12 with winget..."
        Invoke-Tool $winget @("install", "--id", "Python.Python.3.12", "-e", "--source", "winget", "--accept-package-agreements", "--accept-source-agreements")
    }

    $cmd = @'
@echo off
setlocal
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 %*
  exit /b %ERRORLEVEL%
)
where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python %*
  exit /b %ERRORLEVEL%
)
echo Python 3 was not found. Re-run install.ps1 or install Python 3.
exit /b 1
'@
    Set-Content -Path $shim -Value $cmd -Encoding ASCII
    Add-UserPath $binDir
    return $shim
}

function Copy-Tree {
    param([string]$Source, [string]$Destination)
    if (Test-Path $Destination) { Remove-Item -Recurse -Force $Destination }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $Destination -Recurse -Force
    }
    Get-ChildItem -Path $Destination -Recurse -Force -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $Destination -Recurse -Force -File -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
}

function Get-ParentCommandLineTarget {
    try {
        $pidToCheck = $PID
        while ($pidToCheck -and ($pidToCheck -ne 0)) {
            $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$pidToCheck" -ErrorAction SilentlyContinue
            if (-not $proc) { break }
            $line = [string]$proc.CommandLine
            if ($line -match "(?i)codex") { return "codex" }
            if ($line -match "(?i)claude") { return "claude-code" }
            if ($line -match "(?i)cursor") { return "cursor" }
            if ($line -match "(?i)antigravity|agy") { return "antigravity" }
            if ($line -match "(?i)gemini") { return "gemini" }
            $pidToCheck = $proc.ParentProcessId
        }
    } catch { return $null }
    return $null
}

function Resolve-Target {
    if ($Target -ne "auto") { return $Target }
    if ($env:CODEX_SHELL -or $env:CODEX_THREAD_ID -or $env:CODEX_HOME) { return "codex" }
    if ($env:CLAUDECODE -or $env:CLAUDE_CODE -or $env:CLAUDE_CONFIG_DIR) { return "claude-code" }
    if ($env:CURSOR_TRACE_ID -or $env:CURSOR_AGENT -or ($env:TERM_PROGRAM -eq "Cursor")) { return "cursor" }
    if ($env:ANTIGRAVITY_HOME -or $env:AGY_HOME) { return "antigravity" }
    if ($env:GEMINI_API_KEY -or $env:GEMINI_CLI) { return "gemini" }
    $fromProcess = Get-ParentCommandLineTarget
    if ($fromProcess) { return $fromProcess }

    $available = @()
    if (Get-CommandPath "codex") { $available += "codex" }
    if (Get-CommandPath "claude") { $available += "claude-code" }
    if (Get-CommandPath "cursor") { $available += "cursor" }
    if (Get-CommandPath "agy") { $available += "antigravity" }
    if (Get-CommandPath "gemini") { $available += "gemini" }
    if ($available.Count -eq 1) { return $available[0] }
    throw "Could not auto-detect target. Rerun with -Target codex, claude-code, cursor, antigravity, or gemini."
}

$grok = Ensure-Grok
$pythonShim = Ensure-Python3Shim

if (-not $NoAuth) {
    Write-Step "Starting Grok browser login. Complete the browser or device-code flow if prompted."
    Invoke-Tool $grok @("login") -IgnoreErrors
}

$resolvedTarget = Resolve-Target
Write-Host "Detected setup target: $resolvedTarget"

switch ($resolvedTarget) {
    "codex" {
        $codex = Get-CommandPath "codex"
        if (-not $codex) { throw "codex was not found on PATH." }
        Invoke-Tool $codex @("mcp", "remove", $ServerName) -IgnoreErrors
        Invoke-Tool $codex @("mcp", "remove", "hermes-grok") -IgnoreErrors
        Invoke-Tool $codex @("plugin", "remove", "hermes-grok-tools") -IgnoreErrors
        Invoke-Tool $codex @("plugin", "marketplace", "remove", "hermes-grok-tools") -IgnoreErrors
        Invoke-Tool $codex @("plugin", "marketplace", "remove", "grok-cli-tools") -IgnoreErrors
        Invoke-Tool $codex @("plugin", "marketplace", "add", $RootDir)
        Invoke-Tool $codex @("plugin", "add", "grok-cli-tools@grok-cli-tools")
    }
    "claude-code" {
        $claude = Get-CommandPath "claude"
        if (-not $claude) { throw "claude was not found on PATH." }
        Invoke-Tool $claude @("mcp", "remove", $ServerName) -IgnoreErrors
        Invoke-Tool $claude @("mcp", "remove", "hermes-grok") -IgnoreErrors
        Invoke-Tool $claude @("plugin", "uninstall", "hermes-grok-tools") -IgnoreErrors
        Invoke-Tool $claude @("plugin", "uninstall", "grok-cli-tools") -IgnoreErrors
        Invoke-Tool $claude @("plugin", "marketplace", "remove", "hermes-grok-tools") -IgnoreErrors
        Invoke-Tool $claude @("plugin", "marketplace", "remove", "grok-cli-tools") -IgnoreErrors
        Invoke-Tool $claude @("plugin", "marketplace", "add", $RootDir)
        Invoke-Tool $claude @("plugin", "install", "grok-cli-tools@grok-cli-tools", "--scope", "user")
    }
    "cursor" {
        $oldDir = Join-Path $env:USERPROFILE ".cursor\plugins\local\hermes-grok-tools"
        if (Test-Path $oldDir) { Remove-Item -Recurse -Force $oldDir }
        $cursorPluginDir = if ($env:CURSOR_PLUGIN_DIR) { $env:CURSOR_PLUGIN_DIR } else { Join-Path $env:USERPROFILE ".cursor\plugins\local\grok-cli-tools" }
        Copy-Tree (Join-Path $RootDir "plugins\grok-cli-tools") $cursorPluginDir
        Write-Host "Installed grok-cli-tools as a local Cursor plugin at $cursorPluginDir."
    }
    "antigravity" {
        $agy = Get-CommandPath "agy"
        if ($agy) {
            $oldDir = Join-Path $env:USERPROFILE ".gemini\antigravity-cli\plugins\hermes-grok-tools"
            if (Test-Path $oldDir) { Remove-Item -Recurse -Force $oldDir }
            $agyPluginDir = Join-Path $env:USERPROFILE ".gemini\antigravity-cli\plugins\grok-cli-tools"
            Copy-Tree $RootDir $agyPluginDir
        } else {
            $gemini = Get-CommandPath "gemini"
            if (-not $gemini) { throw "Neither agy nor gemini was found on PATH." }
            Invoke-Tool $gemini @("extensions", "uninstall", "hermes-grok-tools") -IgnoreErrors
            Invoke-Tool $gemini @("extensions", "uninstall", "grok-cli-tools") -IgnoreErrors
            Invoke-Tool $gemini @("extensions", "install", $RootDir, "--consent")
        }
    }
    "gemini" {
        $gemini = Get-CommandPath "gemini"
        if (-not $gemini) { throw "gemini was not found on PATH." }
        Invoke-Tool $gemini @("extensions", "uninstall", "hermes-grok-tools") -IgnoreErrors
        Invoke-Tool $gemini @("extensions", "uninstall", "grok-cli-tools") -IgnoreErrors
        Invoke-Tool $gemini @("extensions", "install", $RootDir, "--consent")
    }
}

Write-Host "Target handled: $resolvedTarget."
Write-Host "Restart $resolvedTarget, then call grok_status from the plugin MCP tools."
Write-Host "Python shim for MCP hosts: $pythonShim"
