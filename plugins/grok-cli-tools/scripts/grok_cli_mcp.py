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
SERVER_VERSION = "1.1.4"
DEFAULT_MODEL = os.environ.get("GROK_CLI_MODEL", "grok-4.5")
DEFAULT_EFFORT = os.environ.get("GROK_CLI_EFFORT", "high").strip().lower() or "high"
SUPERGROK_UPGRADE_URL = "https://grok.com/supergrok?referrer=pricing&target=supergrok"
X_PREMIUM_UPGRADE_URL = "https://x.com/i/premium_sign_up"
DEFAULT_TIMEOUT_SECONDS = 900
MIN_TIMEOUT_SECONDS = 30
MAX_TIMEOUT_SECONDS = 3600
EFFORT_LEVELS = {"low", "medium", "high"}
IMAGE_MODELS = {
    "standard": "grok-imagine-image",
    "high": "grok-imagine-image-quality",
}
VIDEO_MODELS = {
    "standard": "grok-imagine-video",
    "high": "grok-imagine-video-1.5",
}
IMAGE_RESOLUTIONS = {"1k", "2k"}
VIDEO_RESOLUTIONS = {"480p", "720p", "1080p"}
ASPECT_RATIOS = {"1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"}


class GrokCliError(RuntimeError):
    pass


class GrokUsageLimitError(GrokCliError):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        self.upgrade_url = SUPERGROK_UPGRADE_URL
        self.upgrade_options = [
            {
                "type": "supergrok",
                "label": "SuperGrokプランを確認・アップグレード",
                "url": SUPERGROK_UPGRADE_URL,
            },
            {
                "type": "x_premium",
                "label": "X PremiumまたはPremium+へ加入",
                "url": X_PREMIUM_UPGRADE_URL,
            },
        ]
        super().__init__(
            "Grokの利用上限またはレート制限に達しました。\n\n"
            "利用を続ける方法:\n\n"
            f"1. [SuperGrokプランを確認・アップグレード]({SUPERGROK_UPGRADE_URL})\n"
            f"2. [X PremiumまたはPremium+へ加入]({X_PREMIUM_UPGRADE_URL})\n"
            "   加入後、grok.comのSettings → AccountでXアカウントを連携してください。\n"
            "3. 利用枠のリセットを待ってから再試行する\n\n"
            "Grok CLIの元エラー:\n"
            f"{detail}"
        )


USAGE_LIMIT_MARKERS = (
    "rate limit",
    "rate_limit",
    "rate-limit",
    "usage limit",
    "usage_limit",
    "usage-limit",
    "weekly limit",
    "weekly_limit",
    "daily limit",
    "daily_limit",
    "free tier limit",
    "free_tier_limit",
    "credit limit",
    "credit_limit",
    "quota exceeded",
    "quota_exceeded",
    "insufficient quota",
    "insufficient_quota",
    "insufficient credit",
    "out of credit",
    "credits exhausted",
    "resource exhausted",
    "resource_exhausted",
    "free-usage paywall",
    "free usage paywall",
    "too many requests",
)


def _is_usage_limit_error(detail: str) -> bool:
    normalized = detail.lower()
    if any(marker in normalized for marker in USAGE_LIMIT_MARKERS):
        return True
    return any(
        marker in normalized
        for marker in ('"status":429', '"status": 429', "http 429", "status code 429")
    )


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
        "default_effort": DEFAULT_EFFORT,
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
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                parts.append(item)
            elif isinstance(item, dict):
                for key in ("text", "content", "message"):
                    text = _text_from_content(item.get(key))
                    if text:
                        parts.append(text)
                        break
        if parts:
            return "".join(parts)
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

    effort = str(args.get("effort") or DEFAULT_EFFORT).strip().lower()
    if effort not in EFFORT_LEVELS:
        raise GrokCliError("effort must be low, medium, or high for grok-4.5.")
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
        if _is_usage_limit_error(detail):
            raise GrokUsageLimitError(detail)
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
        "effort": str(args.get("effort") or DEFAULT_EFFORT),
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


def _required_media_settings(
    args: dict[str, Any], *, tool_name: str, fields: list[str]
) -> dict[str, Any]:
    cleaned = dict(args)
    confirmed = cleaned.pop("confirmed_settings", False) is True
    if not confirmed:
        raise GrokCliError(
            f"{tool_name} requires user-confirmed settings before generation. "
            "Use the host's structured AskUserQuestion/request_user_input UI to ask for the "
            "missing model/quality and output settings. If the user already supplied or delegated "
            "all settings, call again with confirmed_settings=true."
        )

    missing = [field for field in fields if cleaned.get(field) in (None, "")]
    if missing:
        raise GrokCliError(
            f"{tool_name} is missing confirmed settings: {', '.join(missing)}. "
            "Ask the user for them before retrying."
        )
    return cleaned


def _normalized_quality(args: dict[str, Any]) -> str:
    quality = str(args.get("quality") or "").strip().lower().replace("-", "_")
    aliases = {
        "default": "standard",
        "fast": "standard",
        "quality": "high",
        "high_quality": "high",
        "best": "high",
    }
    quality = aliases.get(quality, quality)
    if quality not in IMAGE_MODELS:
        raise GrokCliError("quality must be standard or high.")
    return quality


def _media_model(args: dict[str, Any], models: dict[str, str]) -> tuple[str, str]:
    quality = _normalized_quality(args)
    explicit_model = str(args.get("media_model") or "").strip()
    model = explicit_model or models[quality]
    if model not in set(models.values()):
        raise GrokCliError(f"Unsupported media_model: {model}")
    if explicit_model:
        quality = next(key for key, value in models.items() if value == model)
    return quality, model


def _validated_aspect_ratio(args: dict[str, Any]) -> str:
    aspect_ratio = str(args.get("aspect_ratio") or "").strip()
    if aspect_ratio not in ASPECT_RATIOS:
        raise GrokCliError(
            "aspect_ratio must be 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, or 2:3."
        )
    return aspect_ratio


def tool_generate_image(args: dict[str, Any]) -> dict[str, Any]:
    settings = _required_media_settings(
        args,
        tool_name="grok_generate_image",
        fields=["quality", "resolution", "aspect_ratio"],
    )
    quality, media_model = _media_model(settings, IMAGE_MODELS)
    resolution = str(settings["resolution"]).strip().lower()
    if resolution not in IMAGE_RESOLUTIONS:
        raise GrokCliError("resolution must be 1k or 2k for image generation.")
    aspect_ratio = _validated_aspect_ratio(settings)
    request = str(settings.get("prompt") or "").strip()
    if not request:
        raise GrokCliError("prompt must not be empty for image generation.")
    source_path = str(settings.get("source_image_path") or "").strip()
    source_instruction = (
        f"Edit the source image at this absolute local path: {source_path}\n"
        if source_path
        else "Generate a new image from text.\n"
    )
    prompt = (
        "Use Grok Build's bundled Imagine image-generation tool now. Do not merely describe an "
        "image. Generate exactly one image, save it through the built-in media tool, and return "
        "the saved absolute file path. Do not edit repository source files.\n\n"
        f"{source_instruction}"
        f"Media model: {media_model}\n"
        f"Quality: {quality}\n"
        f"Resolution: {resolution}\n"
        f"Aspect ratio: {aspect_ratio}\n"
        f"Generation request:\n{request}"
    )
    result = _run_grok(prompt, settings)
    result["media"] = {
        "type": "image",
        "model": media_model,
        "quality": quality,
        "resolution": resolution,
        "aspect_ratio": aspect_ratio,
    }
    return result


def tool_generate_video(args: dict[str, Any]) -> dict[str, Any]:
    settings = _required_media_settings(
        args,
        tool_name="grok_generate_video",
        fields=["quality", "resolution", "duration", "aspect_ratio"],
    )
    quality, media_model = _media_model(settings, VIDEO_MODELS)
    resolution = str(settings["resolution"]).strip().lower()
    if resolution not in VIDEO_RESOLUTIONS:
        raise GrokCliError("resolution must be 480p, 720p, or 1080p for video generation.")
    try:
        duration = int(settings["duration"])
    except (TypeError, ValueError) as exc:
        raise GrokCliError("duration must be an integer from 1 to 15 seconds.") from exc
    if not 1 <= duration <= 15:
        raise GrokCliError("duration must be from 1 to 15 seconds.")
    aspect_ratio = _validated_aspect_ratio(settings)
    request = str(settings.get("prompt") or "").strip()
    if not request:
        raise GrokCliError("prompt must not be empty for video generation.")
    source_path = str(settings.get("source_image_path") or "").strip()
    if media_model == "grok-imagine-video-1.5" and not source_path:
        raise GrokCliError(
            "grok-imagine-video-1.5 requires source_image_path. For text-to-video, use "
            "quality=standard and grok-imagine-video."
        )
    if resolution == "1080p" and media_model != "grok-imagine-video-1.5":
        raise GrokCliError(
            "1080p requires grok-imagine-video-1.5 with source_image_path. "
            "Use 720p or 480p for text-to-video."
        )
    source_instruction = (
        f"Animate the source image at this absolute local path: {source_path}\n"
        if source_path
        else "Generate a new video from text.\n"
    )
    prompt = (
        "Use Grok Build's bundled Imagine video-generation tool now. Do not merely describe a "
        "video. Generate exactly one video, save it through the built-in media tool, and return "
        "the saved absolute file path. Do not edit repository source files.\n\n"
        f"{source_instruction}"
        f"Media model: {media_model}\n"
        f"Quality: {quality}\n"
        f"Resolution: {resolution}\n"
        f"Duration: {duration} seconds\n"
        f"Aspect ratio: {aspect_ratio}\n"
        f"Generation request:\n{request}"
    )
    result = _run_grok(prompt, settings)
    result["media"] = {
        "type": "video",
        "model": media_model,
        "quality": quality,
        "resolution": resolution,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
    }
    return result


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
        "enum": ["low", "medium", "high"],
        "default": DEFAULT_EFFORT,
        "description": "Grok 4.5 reasoning effort. Defaults to high.",
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
        "description": "Ask Grok 4.5 a normal question or request a second opinion through the locally authenticated Grok CLI. The answer field preserves Grok's wording for verbatim relay: do not summarize, paraphrase, translate, or truncate it. Read-only; supports session continuation.",
        "inputSchema": _schema("question", "The complete question to ask Grok."),
        "handler": tool_ask,
    },
    "grok_research": {
        "description": "Delegate current-information and web research to Grok 4.5 through Grok CLI, requesting primary-source links. Relay the answer field verbatim without summarizing, paraphrasing, translating, or truncating it. This is not a guaranteed dedicated X Search API.",
        "inputSchema": _schema("query", "The research question."),
        "handler": tool_research,
    },
    "grok_plan": {
        "description": "Ask Grok 4.5 to inspect a project read-only and produce an implementation plan. Relay the answer field verbatim without summarizing, paraphrasing, translating, or truncating it.",
        "inputSchema": _schema("task", "The complete implementation or architecture task."),
        "handler": tool_plan,
    },
    "grok_review": {
        "description": "Ask Grok 4.5 to review a repository and current git diff read-only. Relay the answer field verbatim without summarizing, paraphrasing, translating, or truncating it.",
        "inputSchema": _schema("instructions", "Review scope or special concerns."),
        "handler": tool_review,
    },
    "grok_generate_image": {
        "description": "Generate or edit one image with Grok Imagine through the OAuth-authenticated Grok CLI. Before calling, use structured AskUserQuestion/request_user_input to confirm quality/model, resolution, and aspect ratio; then set confirmed_settings=true. Do not choose settings silently unless the user explicitly delegates them.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "confirmed_settings": {
                    "type": "boolean",
                    "description": "True only after the user supplied, approved, or delegated all generation settings.",
                },
                "quality": {"type": "string", "enum": ["standard", "high"]},
                "media_model": {
                    "type": "string",
                    "enum": ["grok-imagine-image", "grok-imagine-image-quality"],
                },
                "resolution": {"type": "string", "enum": ["1k", "2k"]},
                "aspect_ratio": {
                    "type": "string",
                    "enum": ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"],
                },
                "source_image_path": {
                    "type": "string",
                    "description": "Optional absolute local path for image editing.",
                },
                **COMMON_PROPERTIES,
            },
            "required": [
                "prompt",
                "confirmed_settings",
                "quality",
                "resolution",
                "aspect_ratio",
            ],
        },
        "handler": tool_generate_image,
    },
    "grok_generate_video": {
        "description": "Generate one text-to-video or image-to-video result with Grok Imagine through the OAuth-authenticated Grok CLI. Before calling, use structured AskUserQuestion/request_user_input to confirm model/quality, resolution, duration, and aspect ratio; then set confirmed_settings=true. grok-imagine-video-1.5 and 1080p require source_image_path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "confirmed_settings": {
                    "type": "boolean",
                    "description": "True only after the user supplied, approved, or delegated all generation settings.",
                },
                "quality": {"type": "string", "enum": ["standard", "high"]},
                "media_model": {
                    "type": "string",
                    "enum": ["grok-imagine-video", "grok-imagine-video-1.5"],
                },
                "resolution": {
                    "type": "string",
                    "enum": ["480p", "720p", "1080p"],
                },
                "duration": {"type": "integer", "minimum": 1, "maximum": 15},
                "aspect_ratio": {
                    "type": "string",
                    "enum": ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"],
                },
                "source_image_path": {
                    "type": "string",
                    "description": "Optional absolute local path for image-to-video generation.",
                },
                **COMMON_PROPERTIES,
            },
            "required": [
                "prompt",
                "confirmed_settings",
                "quality",
                "resolution",
                "duration",
                "aspect_ratio",
            ],
        },
        "handler": tool_generate_video,
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


def _tool_content_text(result: Any) -> str:
    if isinstance(result, dict) and isinstance(result.get("answer"), str):
        return result["answer"]
    return json.dumps(result, ensure_ascii=False, indent=2)


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
                            "text": _tool_content_text(result),
                        }
                    ],
                    "structuredContent": result,
                    "isError": False,
                },
            )
        except Exception as exc:
            structured_error: dict[str, Any] = {"ok": False, "error": str(exc)}
            if isinstance(exc, GrokUsageLimitError):
                structured_error.update(
                    {
                        "error_type": "usage_limit",
                        "upgrade_plan": "SuperGrok",
                        "upgrade_url": exc.upgrade_url,
                        "upgrade_options": exc.upgrade_options,
                        "original_error": exc.detail,
                    }
                )
            return _response(
                message_id,
                {
                    "content": [{"type": "text", "text": str(exc)}],
                    "structuredContent": structured_error,
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
