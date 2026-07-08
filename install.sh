#!/usr/bin/env bash
set -euo pipefail

TARGET="${HERMES_GROK_TARGET:-auto}"
RUN_AUTH=1
INSTALL_HERMES=1
CONFIGURE_HERMES=1
SERVER_NAME="${SERVER_NAME:-hermes-grok}"

usage() {
  cat <<'EOF'
Usage:
  ./install.sh [--target auto|codex|claude-code|cursor|antigravity|gemini] [options]

Options:
  --no-auth              Do not run `hermes auth add xai-oauth`
  --no-hermes-install    Do not install Hermes if the `hermes` command is missing
  --no-hermes-config     Do not set Hermes image/video providers to xAI
  --hermes-agent-path P  Optional Hermes Agent source checkout hint for manual/debug use
  --server-name NAME     MCP server name (default: hermes-grok)
  -h, --help             Show this help
EOF
}

HERMES_AGENT_PATH="${HERMES_AGENT_PATH:-}"

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
    --no-hermes-install)
      INSTALL_HERMES=0
      shift
      ;;
    --no-hermes-config)
      CONFIGURE_HERMES=0
      shift
      ;;
    --hermes-agent-path)
      HERMES_AGENT_PATH="${2:-}"
      shift 2
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
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"

if [[ -z "$PYTHON_BIN" ]]; then
  echo "python3 was not found on PATH" >&2
  exit 1
fi

if ! command -v hermes >/dev/null 2>&1; then
  if [[ "$INSTALL_HERMES" == "1" ]]; then
    echo "Hermes CLI not found. Installing Hermes Agent..."
    curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
  else
    echo "Hermes CLI not found. Install Hermes first or rerun without --no-hermes-install." >&2
    exit 1
  fi
fi

if [[ "$CONFIGURE_HERMES" == "1" ]]; then
  echo "Configuring Hermes xAI/Grok backends..."
  hermes plugins enable image_gen/xai --no-allow-tool-override >/dev/null 2>&1 || true
  hermes plugins enable video_gen/xai --no-allow-tool-override >/dev/null 2>&1 || true
  hermes config set image_gen.provider xai >/dev/null
  hermes config set video_gen.provider xai >/dev/null
  hermes config set video_gen.model grok-imagine-video >/dev/null || true
fi

if [[ "$RUN_AUTH" == "1" ]]; then
  echo "Starting Hermes xAI Grok OAuth. Browser/device login may require user action."
  hermes auth add xai-oauth || {
    echo "OAuth did not complete. You can rerun later: hermes auth add xai-oauth" >&2
  }
fi

if [[ -n "$HERMES_AGENT_PATH" ]]; then
  echo "Note: plugin manifests stay portable; export HERMES_AGENT_PATH in the host environment if this checkout hint is required."
fi

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "$1 was not found on PATH" >&2
    exit 1
  fi
}

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
    codex plugin marketplace remove hermes-grok-tools >/dev/null 2>&1 || true
    codex plugin marketplace add "$ROOT_DIR"
    codex plugin add hermes-grok-tools@hermes-grok-tools
    ;;
  claude-code)
    require_cmd claude
    claude mcp remove "$SERVER_NAME" >/dev/null 2>&1 || true
    claude plugin uninstall hermes-grok-tools >/dev/null 2>&1 || true
    claude plugin marketplace remove hermes-grok-tools >/dev/null 2>&1 || true
    claude plugin marketplace add "$ROOT_DIR"
    claude plugin install hermes-grok-tools@hermes-grok-tools --scope user
    ;;
  cursor)
    CURSOR_PLUGIN_DIR="${CURSOR_PLUGIN_DIR:-$HOME/.cursor/plugins/local/hermes-grok-tools}"
    mkdir -p "$(dirname "$CURSOR_PLUGIN_DIR")"
    copy_tree "$ROOT_DIR/plugins/hermes-grok-tools" "$CURSOR_PLUGIN_DIR"
    echo "Installed hermes-grok-tools as a local Cursor plugin at $CURSOR_PLUGIN_DIR."
    echo "For team distribution, import this GitHub repo in Cursor Dashboard > Settings > Plugins > Team Marketplaces."
    echo "Direct cursor --add-mcp fallback was intentionally not used."
    ;;
  antigravity)
    if command -v agy >/dev/null 2>&1; then
      AGY_PLUGIN_DIR="$HOME/.gemini/antigravity-cli/plugins/hermes-grok-tools"
      mkdir -p "$(dirname "$AGY_PLUGIN_DIR")"
      copy_tree "$ROOT_DIR" "$AGY_PLUGIN_DIR"
      echo "Installed hermes-grok-tools as an Antigravity CLI plugin at $AGY_PLUGIN_DIR."
    elif command -v gemini >/dev/null 2>&1; then
      gemini extensions uninstall hermes-grok-tools >/dev/null 2>&1 || true
      gemini extensions install "$ROOT_DIR" --consent
      echo "Installed hermes-grok-tools as a Gemini/Antigravity-compatible extension."
    else
      echo "Neither agy nor gemini was found on PATH. Install Antigravity CLI or Gemini CLI first." >&2
      exit 1
    fi
    ;;
  gemini)
    require_cmd gemini
    gemini extensions uninstall hermes-grok-tools >/dev/null 2>&1 || true
    gemini extensions install "$ROOT_DIR" --consent
    ;;
esac

if [[ "$TARGET" == "cursor" ]]; then
  echo "Target handled: cursor."
  echo "Restart Cursor, ensure local/team plugin imports are allowed, then call hermes_grok_status."
else
  echo "Target handled: $TARGET."
  echo "Restart $TARGET, then call hermes_grok_status from the plugin MCP tools."
fi
