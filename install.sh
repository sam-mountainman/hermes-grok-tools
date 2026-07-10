#!/usr/bin/env bash
set -euo pipefail

TARGET="${GROK_CLI_TOOLS_TARGET:-auto}"
RUN_AUTH=1
INSTALL_GROK=1
SERVER_NAME="${SERVER_NAME:-grok-cli}"

usage() {
  cat <<'EOF'
Usage: ./install.sh [options]

Options:
  --target TARGET        codex|claude-code|cursor|antigravity|gemini
  --no-auth              Do not run `grok login`
  --no-grok-install      Do not install Grok CLI when `grok` is missing
  --server-name NAME     Legacy direct-MCP name to remove (default: grok-cli)
  -h, --help             Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --no-auth)
      RUN_AUTH=0
      shift
      ;;
    --no-grok-install)
      INSTALL_GROK=0
      shift
      ;;
    --server-name)
      SERVER_NAME="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "$1 was not found on PATH" >&2
    exit 1
  fi
}

refresh_grok_path() {
  case ":$PATH:" in
    *":$HOME/.grok/bin:"*) ;;
    *) export PATH="$HOME/.grok/bin:$PATH" ;;
  esac
}

refresh_grok_path
if ! command -v grok >/dev/null 2>&1; then
  if [[ "$INSTALL_GROK" == "1" ]]; then
    require_cmd curl
    echo "Grok CLI not found. Installing the official Grok CLI..."
    curl -fsSL https://x.ai/cli/install.sh | bash
    refresh_grok_path
  else
    echo "Grok CLI was not found. Install it from https://x.ai/cli or rerun without --no-grok-install." >&2
    exit 1
  fi
fi

if ! command -v grok >/dev/null 2>&1; then
  echo "The Grok installer completed, but the grok command was not found in $HOME/.grok/bin." >&2
  exit 1
fi

if [[ "$RUN_AUTH" == "1" ]]; then
  echo "Starting Grok browser login. Complete the browser or device-code flow if prompted."
  grok login || {
    echo "Grok login did not complete. Run `grok login` later, then call grok_status." >&2
  }
fi

PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || true)}"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "python3 was not found on PATH. Install Python 3, then rerun this installer." >&2
  exit 1
fi

copy_tree() {
  local src="$1"
  local dst="$2"
  "$PYTHON_BIN" - "$src" "$dst" <<'PY'
from __future__ import annotations

import shutil
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
if dst.exists():
    shutil.rmtree(dst)
ignore = shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", "*.pyc")
shutil.copytree(src, dst, ignore=ignore)
PY
}

detect_target_from_process_tree() {
  local pid="${PPID:-}"
  while [[ -n "$pid" && "$pid" != "0" && "$pid" != "1" ]]; do
    local args
    args="$(ps -o args= -p "$pid" 2>/dev/null || true)"
    case "$args" in
      *Codex*|*codex*) echo codex; return 0 ;;
      *Claude*|*claude*) echo claude-code; return 0 ;;
      *Cursor*|*cursor*) echo cursor; return 0 ;;
      *Antigravity*|*antigravity*|*agy*) echo antigravity; return 0 ;;
      *Gemini*|*gemini*) echo gemini; return 0 ;;
    esac
    pid="$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ' || true)"
  done
  return 1
}

detect_target() {
  if [[ "$TARGET" != "auto" ]]; then
    echo "$TARGET"
    return 0
  fi
  if [[ -n "${CODEX_SHELL:-}" || -n "${CODEX_THREAD_ID:-}" || -n "${CODEX_HOME:-}" ]]; then
    echo codex
    return 0
  fi
  if [[ -n "${CLAUDECODE:-}" || -n "${CLAUDE_CODE:-}" || -n "${CLAUDE_CONFIG_DIR:-}" ]]; then
    echo claude-code
    return 0
  fi
  if [[ -n "${CURSOR_TRACE_ID:-}" || -n "${CURSOR_AGENT:-}" || "${TERM_PROGRAM:-}" == "Cursor" ]]; then
    echo cursor
    return 0
  fi
  if [[ -n "${ANTIGRAVITY_HOME:-}" || -n "${AGY_HOME:-}" ]]; then
    echo antigravity
    return 0
  fi
  if [[ -n "${GEMINI_API_KEY:-}" || -n "${GEMINI_CLI:-}" ]]; then
    echo gemini
    return 0
  fi
  if detected="$(detect_target_from_process_tree)"; then
    echo "$detected"
    return 0
  fi

  local available=()
  command -v codex >/dev/null 2>&1 && available+=(codex)
  command -v claude >/dev/null 2>&1 && available+=(claude-code)
  command -v cursor >/dev/null 2>&1 && available+=(cursor)
  command -v agy >/dev/null 2>&1 && available+=(antigravity)
  command -v gemini >/dev/null 2>&1 && available+=(gemini)
  if [[ "${#available[@]}" == "1" ]]; then
    echo "${available[0]}"
    return 0
  fi

  echo "Could not auto-detect target. Rerun with --target codex|claude-code|cursor|antigravity|gemini." >&2
  exit 2
}

TARGET="$(detect_target)"
case "$TARGET" in
  codex|claude-code|cursor|antigravity|gemini) ;;
  *)
    echo "Unsupported target: $TARGET" >&2
    exit 2
    ;;
esac
echo "Detected setup target: $TARGET"

case "$TARGET" in
  codex)
    require_cmd codex
    codex mcp remove "$SERVER_NAME" >/dev/null 2>&1 || true
    codex mcp remove hermes-grok >/dev/null 2>&1 || true
    codex plugin remove hermes-grok-tools >/dev/null 2>&1 || true
    codex plugin marketplace remove hermes-grok-tools >/dev/null 2>&1 || true
    codex plugin marketplace remove grok-cli-tools >/dev/null 2>&1 || true
    codex plugin marketplace add "$ROOT_DIR"
    codex plugin add grok-cli-tools@grok-cli-tools
    ;;
  claude-code)
    require_cmd claude
    claude mcp remove "$SERVER_NAME" >/dev/null 2>&1 || true
    claude mcp remove hermes-grok >/dev/null 2>&1 || true
    claude plugin uninstall hermes-grok-tools >/dev/null 2>&1 || true
    claude plugin uninstall grok-cli-tools >/dev/null 2>&1 || true
    claude plugin marketplace remove hermes-grok-tools >/dev/null 2>&1 || true
    claude plugin marketplace remove grok-cli-tools >/dev/null 2>&1 || true
    claude plugin marketplace add "$ROOT_DIR"
    claude plugin install grok-cli-tools@grok-cli-tools --scope user
    ;;
  cursor)
    OLD_CURSOR_PLUGIN_DIR="$HOME/.cursor/plugins/local/hermes-grok-tools"
    [[ ! -d "$OLD_CURSOR_PLUGIN_DIR" ]] || rm -rf "$OLD_CURSOR_PLUGIN_DIR"
    CURSOR_PLUGIN_DIR="${CURSOR_PLUGIN_DIR:-$HOME/.cursor/plugins/local/grok-cli-tools}"
    mkdir -p "$(dirname "$CURSOR_PLUGIN_DIR")"
    copy_tree "$ROOT_DIR/plugins/grok-cli-tools" "$CURSOR_PLUGIN_DIR"
    echo "Installed grok-cli-tools as a local Cursor plugin at $CURSOR_PLUGIN_DIR."
    echo "For team distribution, import this GitHub repo in Cursor Dashboard > Settings > Plugins > Team Marketplaces."
    ;;
  antigravity)
    if command -v agy >/dev/null 2>&1; then
      OLD_AGY_PLUGIN_DIR="$HOME/.gemini/antigravity-cli/plugins/hermes-grok-tools"
      [[ ! -d "$OLD_AGY_PLUGIN_DIR" ]] || rm -rf "$OLD_AGY_PLUGIN_DIR"
      AGY_PLUGIN_DIR="$HOME/.gemini/antigravity-cli/plugins/grok-cli-tools"
      mkdir -p "$(dirname "$AGY_PLUGIN_DIR")"
      copy_tree "$ROOT_DIR" "$AGY_PLUGIN_DIR"
      echo "Installed grok-cli-tools as an Antigravity CLI plugin at $AGY_PLUGIN_DIR."
    elif command -v gemini >/dev/null 2>&1; then
      gemini extensions uninstall hermes-grok-tools >/dev/null 2>&1 || true
      gemini extensions uninstall grok-cli-tools >/dev/null 2>&1 || true
      gemini extensions install "$ROOT_DIR" --consent
    else
      echo "Neither agy nor gemini was found on PATH. Install Antigravity CLI or Gemini CLI first." >&2
      exit 1
    fi
    ;;
  gemini)
    require_cmd gemini
    gemini extensions uninstall hermes-grok-tools >/dev/null 2>&1 || true
    gemini extensions uninstall grok-cli-tools >/dev/null 2>&1 || true
    gemini extensions install "$ROOT_DIR" --consent
    ;;
esac

echo "Target handled: $TARGET."
echo "Restart $TARGET, then call grok_status from the plugin MCP tools."
