#!/usr/bin/env python3
"""Expose Grok CLI as read-only MCP consultation tools.

The bridge has no third-party Python dependencies. Authentication and model
access stay inside the official Grok CLI (`grok login` or `XAI_API_KEY`).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import traceback
import uuid
from pathlib import Path
from typing import Any

SERVER_NAME = "grok-cli"
SERVER_VERSION = "1.0.0"
DEFAULT_MODEL = os.environ.get("GROK_CLI_MODEL", "grok-4.5")
DEFAULT_TIMEOUT_SECONDS = 900
MIN_TIMEOUT_SECONDS = 30
MAX_TIMEOUT_SECONDS = 3600
EFFORT_LEVELS = {"low", "medium", "high", "xhigh", "max"}


class GrokCliError(RuntimeError):
    pass


def _grok_home() -> Path:
    configured = os.environ.get("GROK_HOME", "").strip()
    return Path(configured).expanduser() if configured else Path.home() / ".grok"


def _candidate_grok_bins() -> list[Path]:
    candidates: list[Path] = []
    configured = os.environ.get("GROK_CLI_BIN", "").strip()
    if configured:
        candidates.append(Path(configured).expanduser())

    home_bin = _grok_home() / "bin"
    candidates.extend([home_bin / "grok", home_bin / "grok.exe"])

    appdata = os.environ.get("APPDATA", "").strip()
    if appdata:
        candidates.extend(
            [Path(appdata) / "npm" / "grok.cmd", Path(appdata) / "npm" / "grok.exe"]
        )
    return candidates


def _find_grok_bin() -> str | None:
    on_path = shutil.which("grok")
    if on_path:
        return on_path
    for candidate in _candidate_grok_bins():
        if candidate.is_file():
            return str(candidate)
    return None


def _require_grok_bin() -> str:
    grok_bin = _find_grok_bin()
    if grok_bin:
        return grok_bin
    raise GrokCliError(
        "Grok CLI was not found. Install it from https://x.ai/cli, then run `grok login`. "
        "Set GROK_CLI_BIN only when the executable is installed in a custom location."
    )


def _run_version(grok_bin: str) -> str | None:
    try:
        completed = subprocess.run(
            [grok_bin, "version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    raw = (completed.stdout or completed.stderr).strip()
    return raw or None


def _authentication_hint() -> dict[str, Any]:
    auth_file = _grok_home() / "auth.json"
    config_file = _grok_home() / "config.toml"
    environment_methods = [
        name
        for name in ("XAI_API_KEY", "GROK_DEPLOYMENT_KEY")
        if os.environ.get(name, "").strip()
    ]
    detected = bool(environment_methods) or (
        auth_file.is_file() and auth_file.stat().st_size > 2
    )
    return {
        "detected": detected,
        "method_hint": environment_methods
        or (["grok login cache"] if auth_file.is_file() else []),
        "auth_file": str(auth_file),
        "config_file_present": config_file.is_file(),
        "note": "Managed config or an external auth provider may work even when no local hint is detected.",
    }


def tool_status(_: dict[str, Any]) -> dict[str, Any]:
    grok_bin = _find_grok_bin()
    authentication = _authentication_hint()
    version = _run_version(grok_bin) if grok_bin else None
    cli_available = bool(grok_bin)
    return {
        "ok": cli_available,
        "grok_cli": grok_bin,
        "version": version,
        "default_model": DEFAULT_MODEL,
        "authentication": authentication,
        "next_steps": (
            []
            if cli_available and authentication["detected"]
            else [
                *(
                    []
                    if cli_available
                    else ["Install Grok CLI from https://x.ai/cli."]
                ),
                "Run `grok login` for browser OAuth, or configure XAI_API_KEY, if calls fail authentication.",
            ]
        ),
    }


def _working_directory(raw: Any) -> Path:
    if raw in (None, ""):
        return Path.cwd()
    path = Path(str(raw)).expanduser().resolve()
    if not path.is_dir():
        raise GrokCliError(f"Working directory does not exist or is not a directory: {path}")
    return path


def _timeout_seconds(raw: Any) -> int:
    if raw in (None, ""):
        return DEFAULT_TIMEOUT_SECONDS
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise GrokCliError("timeout_seconds must be an integer.") from exc
    if not MIN_TIMEOUT_SECONDS <= value <= MAX_TIMEOUT_SECONDS:
        raise GrokCliError(
            f"timeout_seconds must be between {MIN_TIMEOUT_SECONDS} and {MAX_TIMEOUT_SECONDS}."
        )
    return value


def _max_turns(raw: Any) -> int:
    if raw in (None, ""):
        return 24
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise GrokCliError("max_turns must be an integer.") from exc
    if not 1 <= value <= 100:
        raise GrokCliError("max_turns must be between 1 and 100.")
    return value


def _parse_json_output(raw: str) -> Any:
    stripped = raw.strip()
    if not stripped:
        raise GrokCliError("Grok CLI returned no output.")
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    for line in reversed(stripped.splitlines()):
        candidate = line.strip()
        if not candidate:
            continue
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return stripped


def _text_from_content(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                parts.append(item.strip())
            elif isinstance(item, dict):
                for key in ("text", "content", "message"):
                    text = _text_from_content(item.get(key))
                    if text:
                        parts.append(text)
                        break
        if parts:
            return "\n".join(parts)
    return None


def _extract_answer(payload: Any) -> str:
    direct = _text_from_content(payload)
    if direct:
        return direct
    if not isinstance(payload, dict):
        return json.dumps(payload, ensure_ascii=False)

    for key in (
        "answer",
        "result",
        "output_text",
        "response",
        "content",
        "text",
        "message",
        "assistant_message",
        "output",
    ):
        value = payload.get(key)
        direct = _text_from_content(value)
        if direct:
            return direct
        if isinstance(value, dict):
            nested = _extract_answer(value)
            if nested:
                return nested

    return json.dumps(payload, ensure_ascii=False)


def _extract_session_id(payload: Any) -> str | None:
    if isinstance(payload, dict):
        for key in ("session_id", "sessionId", "session"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for value in payload.values():
            found = _extract_session_id(value)
            if found:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = _extract_session_id(value)
            if found:
                return found
    return None


def _build_command(grok_bin: str, prompt: str, args: dict[str, Any], cwd: Path) -> list[str]:
    model = str(args.get("model") or DEFAULT_MODEL).strip()
    if not model:
        raise GrokCliError("model cannot be empty.")

    command = [
        grok_bin,
        "--no-auto-update",
        "-p",
        prompt,
        "--output-format",
        "json",
        "--cwd",
        str(cwd),
        "--model",
        model,
        "--permission-mode",
        "dontAsk",
        "--deny",
        "Edit(*)",
        "--deny",
        "MCPTool(*)",
        "--no-subagents",
        "--no-memory",
        "--max-turns",
        str(_max_turns(args.get("max_turns"))),
    ]

    effort = str(args.get("effort") or "").strip().lower()
    if effort:
        if effort not in EFFORT_LEVELS:
            raise GrokCliError("effort must be low, medium, high, xhigh, or max.")
        command.extend(["--effort", effort])

    session_id = str(args.get("session_id") or "").strip()
    if session_id:
        command.extend(["--resume", session_id])
    else:
        new_session_id = str(args.get("_new_session_id") or "").strip()
        if new_session_id:
            command.extend(["--session-id", new_session_id])
    return command


def _run_grok(prompt: str, args: dict[str, Any]) -> dict[str, Any]:
    if not prompt.strip():
        raise GrokCliError("A non-empty question or task is required.")

    grok_bin = _require_grok_bin()
    cwd = _working_directory(args.get("cwd"))
    timeout = _timeout_seconds(args.get("timeout_seconds"))
    command_args = dict(args)
    requested_session_id = str(command_args.get("session_id") or "").strip()
    new_session_id = None
    if not requested_session_id:
        new_session_id = str(uuid.uuid4())
        command_args["_new_session_id"] = new_session_id
    command = _build_command(grok_bin, prompt, command_args, cwd)
    env = os.environ.copy()
    env.setdefault("NO_COLOR", "1")

    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise GrokCliError(
            f"Grok CLI timed out after {timeout} seconds. Increase timeout_seconds and try again."
        ) from exc
    except OSError as exc:
        raise GrokCliError(f"Failed to start Grok CLI: {exc}") from exc

    stdout = completed.stdout or ""
    stderr = (completed.stderr or "").strip()
    if completed.returncode != 0:
        detail = stderr or stdout.strip() or f"exit code {completed.returncode}"
        auth_help = ""
        if any(token in detail.lower() for token in ("auth", "login", "credential", "401")):
            auth_help = " Run `grok login` in a terminal, then retry."
        raise GrokCliError(f"Grok CLI failed: {detail}.{auth_help}".strip())

    payload = _parse_json_output(stdout)
    return {
        "ok": True,
        "answer": _extract_answer(payload),
        "session_id": _extract_session_id(payload)
        or requested_session_id
        or new_session_id,
        "model": str(args.get("model") or DEFAULT_MODEL),
        "cwd": str(cwd),
        "result": payload,
        "stderr": stderr or None,
    }


def _with_context(prompt: str, args: dict[str, Any]) -> str:
    context = str(args.get("context") or "").strip()
    if not context:
        return prompt
    return f"{prompt}\n\nAdditional context from the host agent:\n{context}"


def tool_ask(args: dict[str, Any]) -> dict[str, Any]:
    question = str(args.get("question") or "").strip()
    prompt = _with_context(
        "You are an external expert consulted by another AI agent. Answer the question directly, "
        "state important uncertainty, and do not modify any files.\n\n"
        f"Question:\n{question}",
        args,
    )
    return _run_grok(prompt, args)


def tool_research(args: dict[str, Any]) -> dict[str, Any]:
    query = str(args.get("query") or "").strip()
    prompt = _with_context(
        "Research the following question using Grok CLI's web-search capability when useful. "
        "Prioritize current primary sources, include direct source links, distinguish facts from "
        "inference, and do not modify files.\n\n"
        f"Research question:\n{query}",
        args,
    )
    return _run_grok(prompt, args)


def tool_plan(args: dict[str, Any]) -> dict[str, Any]:
    task = str(args.get("task") or "").strip()
    prompt = _with_context(
        "Act as a read-only software architect. Inspect the repository in the current working "
        "directory when relevant and return a concrete implementation plan. Do not edit files. "
        "Call out risks, affected files, validation, and unresolved decisions.\n\n"
        f"Task:\n{task}",
        args,
    )
    return _run_grok(prompt, args)


def tool_review(args: dict[str, Any]) -> dict[str, Any]:
    instructions = str(args.get("instructions") or "Review the current working tree.").strip()
    prompt = _with_context(
        "Act as a read-only code reviewer. Inspect the repository and current git diff. Lead with "
        "actionable correctness, security, performance, and regression findings ordered by "
        "severity, with file and line references. Mention test gaps. Do not edit files.\n\n"
        f"Review request:\n{instructions}",
        args,
    )
    return _run_grok(prompt, args)


COMMON_PROPERTIES: dict[str, Any] = {
    "cwd": {
        "type": "string",
        "description": "Absolute project directory Grok may inspect read-only. Defaults to the MCP process cwd.",
    },
    "model": {
        "type": "string",
        "description": f"Grok CLI model. Defaults to {DEFAULT_MODEL}.",
    },
    "effort": {
        "type": "string",
        "enum": ["low", "medium", "high", "xhigh", "max"],
    },
    "session_id": {
        "type": "string",
        "description": "Session id from a previous response to continue the same Grok conversation.",
    },
    "context": {
        "type": "string",
        "description": "Optional host-agent context appended to the request.",
    },
    "timeout_seconds": {
        "type": "integer",
        "minimum": MIN_TIMEOUT_SECONDS,
        "maximum": MAX_TIMEOUT_SECONDS,
        "default": DEFAULT_TIMEOUT_SECONDS,
    },
    "max_turns": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 24,
    },
}


def _schema(required_name: str, description: str) -> dict[str, Any]:
    properties = dict(COMMON_PROPERTIES)
    properties[required_name] = {"type": "string", "description": description}
    return {"type": "object", "properties": properties, "required": [required_name]}


TOOLS: dict[str, dict[str, Any]] = {
    "grok_status": {
        "description": "Check locally whether the official Grok CLI and an OAuth/API-key authentication hint are available. This does not call a model or spend usage.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_status,
    },
    "grok_ask": {
        "description": "Ask Grok 4.5 a normal question or request a second opinion through the locally authenticated Grok CLI. Use when the user explicitly asks Grok/Grok 4.5, asks for a Grok second opinion, or requests an external Grok consultation. Read-only; supports session continuation.",
        "inputSchema": _schema("question", "The complete question to ask Grok."),
        "handler": tool_ask,
    },
    "grok_research": {
        "description": "Delegate current-information and web research to Grok 4.5 through Grok CLI, requesting primary-source links. Use when the user explicitly asks Grok to research or wants Grok's web-search perspective. This is not a guaranteed dedicated X Search API.",
        "inputSchema": _schema("query", "The research question."),
        "handler": tool_research,
    },
    "grok_plan": {
        "description": "Ask Grok 4.5 to inspect a project read-only and produce an implementation plan. Use when the user asks Grok to plan or architect a change.",
        "inputSchema": _schema("task", "The complete implementation or architecture task."),
        "handler": tool_plan,
    },
    "grok_review": {
        "description": "Ask Grok 4.5 to review a repository and current git diff read-only. Use when the user asks Grok for code review or a second review opinion.",
        "inputSchema": _schema("instructions", "Review scope or special concerns."),
        "handler": tool_review,
    },
}


def _mcp_tool_list() -> list[dict[str, Any]]:
    return [
        {"name": name, "description": spec["description"], "inputSchema": spec["inputSchema"]}
        for name, spec in TOOLS.items()
    ]


def _response(message_id: Any, result: Any = None, error: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"jsonrpc": "2.0", "id": message_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result
    return payload


def _handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    message_id = message.get("id")
    params = message.get("params") or {}

    if method == "initialize":
        return _response(
            message_id,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return _response(message_id, {})
    if method == "tools/list":
        return _response(message_id, {"tools": _mcp_tool_list()})
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name not in TOOLS:
            return _response(message_id, error={"code": -32602, "message": f"Unknown tool: {name}"})
        if not isinstance(arguments, dict):
            return _response(message_id, error={"code": -32602, "message": "arguments must be an object"})
        try:
            result = TOOLS[name]["handler"](arguments)
            return _response(
                message_id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2),
                        }
                    ],
                    "structuredContent": result,
                    "isError": False,
                },
            )
        except Exception as exc:
            return _response(
                message_id,
                {
                    "content": [{"type": "text", "text": str(exc)}],
                    "structuredContent": {"ok": False, "error": str(exc)},
                    "isError": True,
                },
            )
    return _response(message_id, error={"code": -32601, "message": f"Method not found: {method}"})


def main() -> int:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
            response = _handle_request(message)
            if response is not None:
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except Exception:
            traceback.print_exc(file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
