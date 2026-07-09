#!/usr/bin/env python3
"""MCP bridge for Hermes Agent xAI/Grok tools.

The server intentionally has no third-party dependency. It speaks the stdio
MCP framing directly, then imports Hermes Agent lazily when a tool is called.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import traceback
from pathlib import Path
from typing import Any, Callable

SERVER_NAME = "hermes-grok"
SERVER_VERSION = "0.1.0"
IMAGE_STANDARD_MODEL = "grok-imagine-image"
IMAGE_QUALITY_MODEL = "grok-imagine-image-quality"
VIDEO_STANDARD_MODEL = "grok-imagine-video"
VIDEO_QUALITY_MODEL = "grok-imagine-video-1.5"
VIDEO_IMAGE_OR_VIDEO_INPUT_MODELS = {
    VIDEO_QUALITY_MODEL,
    "grok-imagine-video-1.5-preview",
    "grok-imagine-video-1.5-2026-05-30",
}
STANDARD_QUALITY_VALUES = {"", "standard", "default", "fast", "economy"}
HIGH_QUALITY_VALUES = {"quality", "high", "high_quality", "high-quality", "best", "pro"}


class HermesBridgeError(RuntimeError):
    pass


def _candidate_hermes_paths() -> list[Path]:
    paths: list[Path] = []
    env_path = os.environ.get("HERMES_AGENT_PATH", "").strip()
    if env_path:
        paths.append(Path(env_path).expanduser())

    home = Path.home()
    local_appdata = os.environ.get("LOCALAPPDATA", "").strip()
    if local_appdata:
        paths.extend(
            [
                Path(local_appdata) / "hermes" / "hermes-agent",
                Path(local_appdata) / "hermes-grok-tools" / "hermes-agent",
            ]
        )

    paths.extend(
        [
            home / ".hermes" / "hermes-agent",
            home / ".hermes" / "agent",
            home / ".hermes-grok-tools" / "hermes-agent",
            home / "hermes-agent",
            home / "Documents" / "hermes-agent",
        ]
    )
    return paths


def _path_looks_like_hermes(path: Path) -> bool:
    return (path / "tools" / "x_search_tool.py").is_file() and (
        path / "hermes_cli"
    ).is_dir()


def _ensure_hermes_importable() -> Path | None:
    try:
        import tools.x_search_tool  # noqa: F401

        return None
    except Exception:
        pass

    for path in _candidate_hermes_paths():
        if _path_looks_like_hermes(path):
            sys.path.insert(0, str(path))
            try:
                import tools.x_search_tool  # noqa: F401

                return path
            except Exception:
                sys.path.pop(0)

    searched = ", ".join(str(p) for p in _candidate_hermes_paths())
    raise HermesBridgeError(
        "Hermes Agent Python modules were not importable. Run `hermes setup`, "
        "or set HERMES_AGENT_PATH to a hermes-agent source checkout. "
        f"Searched: {searched}"
    )


def _json_or_text(raw: Any) -> Any:
    if isinstance(raw, (dict, list)):
        return raw
    if not isinstance(raw, str):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return raw


def _successish(payload: Any) -> bool:
    if isinstance(payload, dict) and payload.get("success") is False:
        return False
    if isinstance(payload, dict) and payload.get("error"):
        return False
    return True


def _call_hermes_handler(handler: Callable[[dict[str, Any]], str], args: dict[str, Any]) -> dict[str, Any]:
    _ensure_hermes_importable()
    raw = handler(args)
    parsed = _json_or_text(raw)
    return {
        "ok": _successish(parsed),
        "result": parsed,
        "raw": raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False),
    }


def _normalize_quality_model_args(
    args: dict[str, Any],
    *,
    standard_model: str,
    quality_model: str,
) -> dict[str, Any]:
    normalized = dict(args)
    raw_quality = normalized.pop("quality", "standard")
    explicit_model = str(normalized.get("model") or "").strip()
    if explicit_model:
        normalized["model"] = explicit_model
        return normalized

    quality = str(raw_quality or "standard").strip().lower().replace(" ", "_")
    if quality in STANDARD_QUALITY_VALUES:
        normalized["model"] = standard_model
        return normalized
    if quality in HIGH_QUALITY_VALUES:
        normalized["model"] = quality_model
        return normalized

    raise HermesBridgeError(
        "Unsupported quality value. Use standard, quality, high, or pass an explicit model."
    )


def _normalize_image_args(args: dict[str, Any]) -> dict[str, Any]:
    return _normalize_quality_model_args(
        args,
        standard_model=IMAGE_STANDARD_MODEL,
        quality_model=IMAGE_QUALITY_MODEL,
    )


def _normalize_video_args(args: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_quality_model_args(
        args,
        standard_model=VIDEO_STANDARD_MODEL,
        quality_model=VIDEO_QUALITY_MODEL,
    )
    model = str(normalized.get("model") or "").strip()
    reference_images = normalized.get("reference_image_urls") or []
    has_image_input = bool(str(normalized.get("image_url") or "").strip()) or bool(reference_images)
    if model in VIDEO_IMAGE_OR_VIDEO_INPUT_MODELS and not has_image_input:
        raise HermesBridgeError(
            "grok-imagine-video-1.5 does not support text-to-video. "
            "Provide image_url/reference_image_urls, or use quality=standard/model=grok-imagine-video."
        )
    return normalized


def _normalize_video_with_input_args(args: dict[str, Any]) -> dict[str, Any]:
    return _normalize_quality_model_args(
        args,
        standard_model=VIDEO_STANDARD_MODEL,
        quality_model=VIDEO_QUALITY_MODEL,
    )


def tool_status(_: dict[str, Any]) -> dict[str, Any]:
    hermes_cli = shutil.which("hermes")
    import_error = None
    source_path = None
    credentials: dict[str, Any] = {"available": False}
    config: dict[str, Any] = {}

    try:
        source = _ensure_hermes_importable()
        source_path = str(source) if source is not None else "python-import-path"
        try:
            from tools.xai_http import resolve_xai_http_credentials

            creds = resolve_xai_http_credentials() or {}
            credentials = {
                "available": bool(str(creds.get("api_key") or "").strip()),
                "provider": str(creds.get("provider") or ""),
                "base_url": str(creds.get("base_url") or ""),
            }
        except Exception as exc:
            credentials = {"available": False, "error": str(exc)}
        try:
            from hermes_cli.config import load_config

            loaded = load_config()
            image_gen = loaded.get("image_gen") if isinstance(loaded, dict) else {}
            video_gen = loaded.get("video_gen") if isinstance(loaded, dict) else {}
            config = {
                "image_gen": image_gen if isinstance(image_gen, dict) else {},
                "video_gen": video_gen if isinstance(video_gen, dict) else {},
            }
        except Exception as exc:
            config = {"error": str(exc)}
    except Exception as exc:
        import_error = str(exc)

    return {
        "ok": import_error is None,
        "hermes_cli": hermes_cli,
        "hermes_source": source_path,
        "credentials": credentials,
        "config": config,
        "import_error": import_error,
        "next_steps": [
            "Run `hermes auth add xai-oauth` for Grok OAuth login.",
            "Run `hermes config set image_gen.provider xai`.",
            "Run `hermes config set video_gen.provider xai`.",
            "Run `hermes plugins enable image_gen/xai --no-allow-tool-override` and `hermes plugins enable video_gen/xai --no-allow-tool-override` if the xAI backends are disabled.",
        ],
    }


def tool_x_search(args: dict[str, Any]) -> dict[str, Any]:
    _ensure_hermes_importable()
    from tools.x_search_tool import _handle_x_search

    return _call_hermes_handler(_handle_x_search, args)


def tool_grok_image(args: dict[str, Any]) -> dict[str, Any]:
    _ensure_hermes_importable()
    try:
        import plugins.image_gen.xai  # noqa: F401
    except Exception:
        pass
    from tools.image_generation_tool import _handle_image_generate

    return _call_hermes_handler(_handle_image_generate, _normalize_image_args(args))


def tool_grok_video(args: dict[str, Any]) -> dict[str, Any]:
    _ensure_hermes_importable()
    try:
        import plugins.video_gen.xai  # noqa: F401
    except Exception:
        pass
    from tools.video_generation_tool import _handle_video_generate

    return _call_hermes_handler(_handle_video_generate, _normalize_video_args(args))


def tool_grok_video_edit(args: dict[str, Any]) -> dict[str, Any]:
    _ensure_hermes_importable()
    try:
        import plugins.video_gen.xai  # noqa: F401
    except Exception:
        pass
    from tools.xai_video_tools import _handle_xai_video_edit

    return _call_hermes_handler(_handle_xai_video_edit, _normalize_video_with_input_args(args))


def tool_grok_video_extend(args: dict[str, Any]) -> dict[str, Any]:
    _ensure_hermes_importable()
    try:
        import plugins.video_gen.xai  # noqa: F401
    except Exception:
        pass
    from tools.xai_video_tools import _handle_xai_video_extend

    return _call_hermes_handler(_handle_xai_video_extend, _normalize_video_with_input_args(args))


TOOLS: dict[str, dict[str, Any]] = {
    "hermes_grok_status": {
        "description": "Check whether Hermes Agent, xAI Grok OAuth credentials, and xAI image/video provider config are visible.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_status,
    },
    "hermes_x_search": {
        "description": "Search X posts through Hermes Agent's xAI Responses API x_search tool. Requires Grok OAuth or XAI_API_KEY.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "allowed_x_handles": {"type": "array", "items": {"type": "string"}},
                "excluded_x_handles": {"type": "array", "items": {"type": "string"}},
                "from_date": {"type": "string", "description": "YYYY-MM-DD"},
                "to_date": {"type": "string", "description": "YYYY-MM-DD"},
                "enable_image_understanding": {"type": "boolean"},
                "enable_video_understanding": {"type": "boolean"},
            },
            "required": ["query"],
        },
        "handler": tool_x_search,
    },
    "hermes_grok_image": {
        "description": "Generate or edit images with Hermes Agent image_generate configured for xAI Grok Imagine. quality=standard uses grok-imagine-image; quality=high/quality uses grok-imagine-image-quality. Explicit model overrides quality.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "quality": {
                    "type": "string",
                    "enum": ["standard", "quality", "high", "high_quality"],
                    "description": "standard is the default lower-cost model; quality/high selects grok-imagine-image-quality.",
                },
                "model": {"type": "string", "description": "Advanced override for the xAI image model."},
                "aspect_ratio": {
                    "type": "string",
                    "enum": ["landscape", "portrait", "square", "16:9", "9:16", "1:1", "4:3", "3:4", "3:2", "2:3"],
                },
                "image_url": {"type": "string"},
                "reference_image_urls": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["prompt"],
        },
        "handler": tool_grok_image,
    },
    "hermes_grok_video": {
        "description": "Generate text-to-video, image-to-video, or reference-to-video with Hermes Agent video_generate configured for xAI Grok Imagine. quality=standard uses grok-imagine-video; quality=high/quality uses grok-imagine-video-1.5, which needs image input. Explicit model overrides quality.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "quality": {
                    "type": "string",
                    "enum": ["standard", "quality", "high", "high_quality"],
                    "description": "standard is the default text/image/video model; quality/high selects grok-imagine-video-1.5 for image-to-video/reference-to-video.",
                },
                "image_url": {"type": "string"},
                "reference_image_urls": {"type": "array", "items": {"type": "string"}},
                "duration": {"type": "integer"},
                "aspect_ratio": {"type": "string"},
                "resolution": {"type": "string"},
                "negative_prompt": {"type": "string"},
                "audio": {"type": "boolean"},
                "seed": {"type": "integer"},
                "model": {"type": "string"},
            },
            "required": ["prompt"],
        },
        "handler": tool_grok_video,
    },
    "hermes_grok_video_edit": {
        "description": "Edit an existing public HTTPS MP4 with xAI Imagine through Hermes Agent. quality=standard uses grok-imagine-video; quality=high/quality uses grok-imagine-video-1.5. Explicit model overrides quality.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "video_url": {"type": "string"},
                "quality": {
                    "type": "string",
                    "enum": ["standard", "quality", "high", "high_quality"],
                },
                "model": {"type": "string"},
            },
            "required": ["prompt", "video_url"],
        },
        "handler": tool_grok_video_edit,
    },
    "hermes_grok_video_extend": {
        "description": "Extend an existing public HTTPS MP4 with xAI Imagine through Hermes Agent. quality=standard uses grok-imagine-video; quality=high/quality uses grok-imagine-video-1.5. Explicit model overrides quality.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "video_url": {"type": "string"},
                "duration": {"type": "integer"},
                "quality": {
                    "type": "string",
                    "enum": ["standard", "quality", "high", "high_quality"],
                },
                "model": {"type": "string"},
            },
            "required": ["prompt", "video_url"],
        },
        "handler": tool_grok_video_extend,
    },
}


def _mcp_tool_list() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["inputSchema"],
        }
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
        args = params.get("arguments") or {}
        if name not in TOOLS:
            return _response(
                message_id,
                error={"code": -32602, "message": f"Unknown tool: {name}"},
            )
        try:
            result = TOOLS[name]["handler"](args)
            text = json.dumps(result, ensure_ascii=False, indent=2)
            return _response(
                message_id,
                {
                    "content": [{"type": "text", "text": text}],
                    "isError": not bool(result.get("ok", True)) if isinstance(result, dict) else False,
                },
            )
        except Exception as exc:
            return _response(
                message_id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "ok": False,
                                    "error": str(exc),
                                    "traceback": traceback.format_exc(),
                                },
                                ensure_ascii=False,
                                indent=2,
                            ),
                        }
                    ],
                    "isError": True,
                },
            )
    return _response(
        message_id,
        error={"code": -32601, "message": f"Method not found: {method}"},
    )


def _read_message() -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            break
        key, _, value = line.decode("ascii", errors="replace").partition(":")
        headers[key.lower()] = value.strip()

    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    body = sys.stdin.buffer.read(length)
    return json.loads(body.decode("utf-8"))


def _write_message(message: dict[str, Any]) -> None:
    body = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def main() -> int:
    while True:
        message = _read_message()
        if message is None:
            return 0
        response = _handle_request(message)
        if response is not None:
            _write_message(response)


if __name__ == "__main__":
    raise SystemExit(main())
