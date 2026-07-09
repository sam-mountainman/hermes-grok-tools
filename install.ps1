[CmdletBinding()]
param(
    [ValidateSet("auto", "codex", "claude-code", "cursor", "antigravity", "gemini")]
    [string]$Target = $(if ($env:HERMES_GROK_TARGET) { $env:HERMES_GROK_TARGET } else { "auto" }),
    [switch]$NoAuth,
    [switch]$NoHermesInstall,
    [switch]$NoHermesConfig,
    [switch]$NoPythonInstall,
    [string]$HermesAgentPath = $env:HERMES_AGENT_PATH,
    [string]$ServerName = $(if ($env:SERVER_NAME) { $env:SERVER_NAME } else { "hermes-grok" })
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RootDir) {
    $RootDir = (Get-Location).Path
}

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message"
}

function Get-CommandPath {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }
    return $null
}

function Invoke-Tool {
    param(
        [string]$File,
        [string[]]$Arguments = @(),
        [switch]$IgnoreErrors
    )
    & $File @Arguments
    $code = $LASTEXITCODE
    if ($null -eq $code) {
        $code = 0
    }
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
    $parts = @()
    if ($userPath) {
        $parts = $userPath -split ";"
    }
    $alreadyPresent = $false
    foreach ($part in $parts) {
        if ($part.TrimEnd("\") -ieq $PathToAdd.TrimEnd("\")) {
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

function Add-HermesPaths {
    $paths = @(
        (Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\venv\Scripts"),
        (Join-Path $env:LOCALAPPDATA "hermes\bin"),
        (Join-Path $env:LOCALAPPDATA "hermes")
    )
    foreach ($path in $paths) {
        if (Test-Path $path) {
            Add-UserPath $path
        }
    }
}

function Get-HermesCommand {
    $cmd = Get-CommandPath "hermes"
    if ($cmd) {
        return $cmd
    }
    $candidate = Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\venv\Scripts\hermes.exe"
    if (Test-Path $candidate) {
        return $candidate
    }
    return $null
}

function Ensure-Hermes {
    Add-HermesPaths
    $hermes = Get-HermesCommand
    if ($hermes) {
        return $hermes
    }

    if ($NoHermesInstall) {
        throw "Hermes CLI was not found. Install Hermes Agent first, or rerun without -NoHermesInstall."
    }

    Write-Step "Hermes CLI not found. Installing Hermes Agent for native Windows..."
    $script = Invoke-RestMethod "https://hermes-agent.nousresearch.com/install.ps1"
    & ([ScriptBlock]::Create($script))
    Add-HermesPaths
    $hermes = Get-HermesCommand
    if (-not $hermes) {
        throw "Hermes installer completed, but hermes.exe was not found. Open a new PowerShell window and rerun .\install.ps1."
    }
    return $hermes
}

function Test-PythonInvocation {
    param(
        [string]$File,
        [string[]]$Arguments
    )
    try {
        & $File @Arguments *> $null
        $code = $LASTEXITCODE
        return ($code -eq 0)
    } catch {
        return $false
    }
}

function Ensure-Python3Shim {
    $binDir = Join-Path $env:LOCALAPPDATA "hermes-grok-tools\bin"
    New-Item -ItemType Directory -Force -Path $binDir | Out-Null
    $shim = Join-Path $binDir "python3.cmd"

    $hasHermesPython = Test-Path (Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\venv\Scripts\python.exe")
    $hasPyLauncher = (Get-CommandPath "py") -and (Test-PythonInvocation "py" @("-3", "-c", "import sys; raise SystemExit(0 if sys.version_info[0] == 3 else 1)"))
    $hasPython = (Get-CommandPath "python") -and (Test-PythonInvocation "python" @("-c", "import sys; raise SystemExit(0 if sys.version_info[0] == 3 else 1)"))

    if ((-not $hasHermesPython) -and (-not $hasPyLauncher) -and (-not $hasPython)) {
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
set "HERMES_PY=%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts\python.exe"
if exist "%HERMES_PY%" (
  "%HERMES_PY%" %*
  exit /b %ERRORLEVEL%
)
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
echo Python 3 was not found. Re-run install.ps1 or install Hermes Agent.
exit /b 1
'@
    Set-Content -Path $shim -Value $cmd -Encoding ASCII
    Add-UserPath $binDir
    return $shim
}

function Copy-Tree {
    param([string]$Source, [string]$Destination)
    if (Test-Path $Destination) {
        Remove-Item -Recurse -Force $Destination
    }
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
            if (-not $proc) {
                break
            }
            $line = [string]$proc.CommandLine
            if ($line -match "(?i)codex") { return "codex" }
            if ($line -match "(?i)claude") { return "claude-code" }
            if ($line -match "(?i)cursor") { return "cursor" }
            if ($line -match "(?i)antigravity|agy") { return "antigravity" }
            if ($line -match "(?i)gemini") { return "gemini" }
            $pidToCheck = $proc.ParentProcessId
            if ($pidToCheck -eq 1) {
                break
            }
        }
    } catch {
        return $null
    }
    return $null
}

function Resolve-Target {
    if ($Target -ne "auto") {
        return $Target
    }
    if ($env:CODEX_SHELL -or $env:CODEX_THREAD_ID -or $env:CODEX_HOME) { return "codex" }
    if ($env:CLAUDECODE -or $env:CLAUDE_CODE -or $env:CLAUDE_CONFIG_DIR) { return "claude-code" }
    if ($env:CURSOR_TRACE_ID -or $env:CURSOR_AGENT -or ($env:TERM_PROGRAM -eq "Cursor")) { return "cursor" }
    if ($env:ANTIGRAVITY_HOME -or $env:AGY_HOME) { return "antigravity" }
    if ($env:GEMINI_API_KEY -or $env:GEMINI_CLI) { return "gemini" }

    $fromProcess = Get-ParentCommandLineTarget
    if ($fromProcess) {
        return $fromProcess
    }

    $available = @()
    if (Get-CommandPath "codex") { $available += "codex" }
    if (Get-CommandPath "claude") { $available += "claude-code" }
    if (Get-CommandPath "cursor") { $available += "cursor" }
    if (Get-CommandPath "agy") { $available += "antigravity" }
    if (Get-CommandPath "gemini") { $available += "gemini" }
    if ($available.Count -eq 1) {
        return $available[0]
    }
    throw "Could not auto-detect target. Rerun with -Target codex, claude-code, cursor, antigravity, or gemini."
}

$hermes = Ensure-Hermes
$pythonShim = Ensure-Python3Shim

if (-not $NoHermesConfig) {
    Write-Step "Configuring Hermes xAI/Grok backends..."
    Invoke-Tool $hermes @("plugins", "enable", "image_gen/xai", "--no-allow-tool-override") -IgnoreErrors
    Invoke-Tool $hermes @("plugins", "enable", "video_gen/xai", "--no-allow-tool-override") -IgnoreErrors
    Invoke-Tool $hermes @("config", "set", "image_gen.provider", "xai")
    Invoke-Tool $hermes @("config", "set", "video_gen.provider", "xai")
    Invoke-Tool $hermes @("config", "set", "image_gen.model", "grok-imagine-image") -IgnoreErrors
    Invoke-Tool $hermes @("config", "set", "video_gen.model", "grok-imagine-video") -IgnoreErrors
}

if (-not $NoAuth) {
    Write-Step "Starting Hermes xAI Grok OAuth. Browser/device login may require user action."
    Invoke-Tool $hermes @("auth", "add", "xai-oauth") -IgnoreErrors
}

if ($HermesAgentPath) {
    Write-Host "Note: plugin manifests stay portable; set HERMES_AGENT_PATH in the host environment if this checkout hint is required."
}

$resolvedTarget = Resolve-Target
Write-Host "Detected setup target: $resolvedTarget"

switch ($resolvedTarget) {
    "codex" {
        $codex = Get-CommandPath "codex"
        if (-not $codex) { throw "codex was not found on PATH." }
        Invoke-Tool $codex @("mcp", "remove", $ServerName) -IgnoreErrors
        Invoke-Tool $codex @("plugin", "marketplace", "remove", "hermes-grok-tools") -IgnoreErrors
        Invoke-Tool $codex @("plugin", "marketplace", "add", $RootDir)
        Invoke-Tool $codex @("plugin", "add", "hermes-grok-tools@hermes-grok-tools")
    }
    "claude-code" {
        $claude = Get-CommandPath "claude"
        if (-not $claude) { throw "claude was not found on PATH." }
        Invoke-Tool $claude @("mcp", "remove", $ServerName) -IgnoreErrors
        Invoke-Tool $claude @("plugin", "uninstall", "hermes-grok-tools") -IgnoreErrors
        Invoke-Tool $claude @("plugin", "marketplace", "remove", "hermes-grok-tools") -IgnoreErrors
        Invoke-Tool $claude @("plugin", "marketplace", "add", $RootDir)
        Invoke-Tool $claude @("plugin", "install", "hermes-grok-tools@hermes-grok-tools", "--scope", "user")
    }
    "cursor" {
        $cursorPluginDir = if ($env:CURSOR_PLUGIN_DIR) {
            $env:CURSOR_PLUGIN_DIR
        } else {
            Join-Path $env:USERPROFILE ".cursor\plugins\local\hermes-grok-tools"
        }
        Copy-Tree (Join-Path $RootDir "plugins\hermes-grok-tools") $cursorPluginDir
        Write-Host "Installed hermes-grok-tools as a local Cursor plugin at $cursorPluginDir."
        Write-Host "For team distribution, import this GitHub repo in Cursor Dashboard > Settings > Plugins > Team Marketplaces."
        Write-Host "Direct cursor --add-mcp fallback was intentionally not used."
    }
    "antigravity" {
        $agy = Get-CommandPath "agy"
        if ($agy) {
            $agyPluginDir = Join-Path $env:USERPROFILE ".gemini\antigravity-cli\plugins\hermes-grok-tools"
            Copy-Tree $RootDir $agyPluginDir
            Write-Host "Installed hermes-grok-tools as an Antigravity CLI plugin at $agyPluginDir."
        } else {
            $gemini = Get-CommandPath "gemini"
            if (-not $gemini) { throw "Neither agy nor gemini was found on PATH. Install Antigravity CLI or Gemini CLI first." }
            Invoke-Tool $gemini @("extensions", "uninstall", "hermes-grok-tools") -IgnoreErrors
            Invoke-Tool $gemini @("extensions", "install", $RootDir, "--consent")
            Write-Host "Installed hermes-grok-tools as a Gemini/Antigravity-compatible extension."
        }
    }
    "gemini" {
        $gemini = Get-CommandPath "gemini"
        if (-not $gemini) { throw "gemini was not found on PATH." }
        Invoke-Tool $gemini @("extensions", "uninstall", "hermes-grok-tools") -IgnoreErrors
        Invoke-Tool $gemini @("extensions", "install", $RootDir, "--consent")
    }
}

Write-Host "Target handled: $resolvedTarget."
Write-Host "Restart $resolvedTarget so it picks up User PATH changes, then call hermes_grok_status from the plugin MCP tools."
Write-Host "Python shim for MCP hosts: $pythonShim"
