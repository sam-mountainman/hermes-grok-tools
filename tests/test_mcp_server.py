import importlib.util
import json
import subprocess
from pathlib import Path


SERVER_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "grok-cli-tools"
    / "scripts"
    / "grok_cli_mcp.py"
)
SPEC = importlib.util.spec_from_file_location("grok_cli_mcp", SERVER_PATH)
grok_cli_mcp = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(grok_cli_mcp)


def test_tool_list_contains_expected_tools():
    names = {tool["name"] for tool in grok_cli_mcp._mcp_tool_list()}
    assert names == {
        "grok_status",
        "grok_ask",
        "grok_research",
        "grok_plan",
        "grok_review",
        "grok_generate_image",
        "grok_generate_video",
    }


def test_initialize_response_shape():
    response = grok_cli_mcp._handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )
    assert response["id"] == 1
    assert response["result"]["serverInfo"]["name"] == "grok-cli"
    assert response["result"]["serverInfo"]["version"] == "1.2.1"
    assert "tools" in response["result"]["capabilities"]


def test_tools_list_response_is_json_serializable():
    response = grok_cli_mcp._handle_request(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    )
    encoded = json.dumps(response)
    assert "grok_ask" in encoded
    assert "grok_review" in encoded


def test_tool_call_content_is_exact_answer_while_metadata_stays_structured(monkeypatch):
    exact = "  Exact Grok answer\n\n```python\nprint('same')\n```  "
    monkeypatch.setitem(
        grok_cli_mcp.TOOLS["grok_ask"],
        "handler",
        lambda _: {"ok": True, "answer": exact, "session_id": "session-1"},
    )
    response = grok_cli_mcp._handle_request(
        {
            "jsonrpc": "2.0",
            "id": 20,
            "method": "tools/call",
            "params": {"name": "grok_ask", "arguments": {"question": "Hello"}},
        }
    )

    assert response["result"]["content"][0]["text"] == exact
    assert response["result"]["structuredContent"]["session_id"] == "session-1"


def test_build_command_uses_grok_45_and_read_only_flags(tmp_path: Path):
    command = grok_cli_mcp._build_command("/tmp/grok", "Question", {}, tmp_path)
    assert command[:4] == ["/tmp/grok", "--no-auto-update", "-p", "Question"]
    assert command[command.index("--model") + 1] == "grok-4.5"
    assert command[command.index("--effort") + 1] == "high"
    assert command[command.index("--permission-mode") + 1] == "dontAsk"
    assert "Edit(*)" in command
    assert "MCPTool(*)" in command
    assert "--no-subagents" in command
    assert "--no-memory" in command
    assert "--always-approve" not in command


def test_build_command_supports_effort_and_resume(tmp_path: Path):
    command = grok_cli_mcp._build_command(
        "/tmp/grok",
        "Follow up",
        {"model": "grok-custom", "effort": "medium", "session_id": "session-123"},
        tmp_path,
    )
    assert command[command.index("--model") + 1] == "grok-custom"
    assert command[command.index("--effort") + 1] == "medium"
    assert command[command.index("--resume") + 1] == "session-123"


def test_parse_json_output_accepts_trailing_json_line():
    payload = grok_cli_mcp._parse_json_output(
        'non-json diagnostic\n{"result":"answer","session_id":"abc"}\n'
    )
    assert payload == {"result": "answer", "session_id": "abc"}


def test_extract_answer_and_session_from_nested_payload():
    payload = {
        "session": {"sessionId": "nested-session"},
        "response": {"content": [{"type": "text", "text": "Grok answer"}]},
    }
    assert grok_cli_mcp._extract_answer(payload) == "Grok answer"
    assert grok_cli_mcp._extract_session_id(payload) == "nested-session"


def test_extract_answer_preserves_exact_text_and_content_boundaries():
    payload = {
        "response": {
            "content": [
                {"type": "text", "text": "  First line\n"},
                {"type": "text", "text": "Second line  "},
            ]
        }
    }
    assert grok_cli_mcp._extract_answer(payload) == "  First line\nSecond line  "


def test_tool_descriptions_require_verbatim_relay():
    for name in ("grok_ask", "grok_research", "grok_plan", "grok_review"):
        description = grok_cli_mcp.TOOLS[name]["description"]
        assert "verbatim" in description
        assert "without summarizing" in description or "do not summarize" in description


def test_run_grok_returns_answer_without_real_cli(monkeypatch, tmp_path: Path):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {"result": "Mock Grok response", "session_id": "session-mock"}
            ),
            stderr="",
        )

    monkeypatch.setattr(grok_cli_mcp, "_require_grok_bin", lambda: "/mock/grok")
    monkeypatch.setattr(grok_cli_mcp.subprocess, "run", fake_run)

    result = grok_cli_mcp._run_grok(
        "A normal question",
        {"cwd": str(tmp_path), "effort": "medium", "timeout_seconds": 60},
    )

    assert result["ok"] is True
    assert result["answer"] == "Mock Grok response"
    assert result["session_id"] == "session-mock"
    assert result["model"] == "grok-4.5"
    assert result["effort"] == "medium"
    assert calls[0][1]["cwd"] == str(tmp_path)


def test_run_grok_creates_resumable_session_when_cli_omits_id(monkeypatch, tmp_path: Path):
    captured_command = []

    def fake_run(command, **kwargs):
        captured_command.extend(command)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps({"result": "Answer without metadata"}),
            stderr="",
        )

    monkeypatch.setattr(grok_cli_mcp, "_require_grok_bin", lambda: "/mock/grok")
    monkeypatch.setattr(grok_cli_mcp.subprocess, "run", fake_run)

    result = grok_cli_mcp._run_grok("Question", {"cwd": str(tmp_path)})

    assert result["session_id"]
    assert captured_command[captured_command.index("--session-id") + 1] == result["session_id"]


def test_cli_auth_error_is_returned_as_mcp_tool_error(monkeypatch):
    monkeypatch.setattr(
        grok_cli_mcp,
        "_require_grok_bin",
        lambda: (_ for _ in ()).throw(grok_cli_mcp.GrokCliError("Run `grok login`.")),
    )
    response = grok_cli_mcp._handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "grok_ask", "arguments": {"question": "Hello"}},
        }
    )
    assert response["result"]["isError"] is True
    assert "grok login" in response["result"]["content"][0]["text"]


def test_usage_limit_detection_matches_quota_errors_only():
    for detail in (
        "HTTP 429: Too Many Requests",
        '{"error":{"type":"rate_limit_error"}}',
        "Weekly limit reached",
        "Free-usage paywall",
        "Insufficient credits",
        '{"error":{"code":"insufficient_quota"}}',
        "RESOURCE_EXHAUSTED",
    ):
        assert grok_cli_mcp._is_usage_limit_error(detail)

    assert not grok_cli_mcp._is_usage_limit_error("Authentication failed with 401")
    assert not grok_cli_mcp._is_usage_limit_error("Context length limit exceeded")


def test_usage_limit_error_includes_all_recovery_links():
    error = grok_cli_mcp.GrokUsageLimitError("HTTP 429 rate limit exceeded")
    message = str(error)
    assert grok_cli_mcp.SUPERGROK_UPGRADE_URL in message
    assert grok_cli_mcp.X_PREMIUM_UPGRADE_URL in message
    assert "Settings → Account" in message
    assert "grok logout" in message
    assert "grok login" in message
    assert "別のプランを重ねて購入する必要はありません" in message
    assert "Extra Usage Credits" not in message
    assert "HTTP 429 rate limit exceeded" in message


def test_cli_usage_limit_returns_structured_upgrade_guidance(monkeypatch, tmp_path: Path):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            1,
            stdout="",
            stderr="HTTP 429: rate limit exceeded",
        )

    monkeypatch.setattr(grok_cli_mcp, "_require_grok_bin", lambda: "/mock/grok")
    monkeypatch.setattr(grok_cli_mcp.subprocess, "run", fake_run)

    response = grok_cli_mcp._handle_request(
        {
            "jsonrpc": "2.0",
            "id": 30,
            "method": "tools/call",
            "params": {
                "name": "grok_ask",
                "arguments": {"question": "Hello", "cwd": str(tmp_path)},
            },
        }
    )

    result = response["result"]
    assert result["isError"] is True
    assert grok_cli_mcp.SUPERGROK_UPGRADE_URL in result["content"][0]["text"]
    assert result["structuredContent"]["error_type"] == "usage_limit"
    assert result["structuredContent"]["upgrade_plan"] == "SuperGrok"
    assert (
        result["structuredContent"]["upgrade_url"]
        == grok_cli_mcp.SUPERGROK_UPGRADE_URL
    )
    options = result["structuredContent"]["upgrade_options"]
    assert [option["type"] for option in options] == [
        "supergrok",
        "x_premium",
    ]
    assert options[1]["url"] == grok_cli_mcp.X_PREMIUM_UPGRADE_URL
    reauthentication = result["structuredContent"]["reauthentication"]
    assert reauthentication["commands"] == ["grok logout", "grok login"]
    assert reauthentication["requires_browser_interaction"] is True
    assert reauthentication["retry_after_login"] is True
    assert (
        reauthentication["do_not_purchase_again_when_plan_is_active_and_usage_remains"]
        is True
    )
    assert result["structuredContent"]["original_error"] == "HTTP 429: rate limit exceeded"


def test_research_description_does_not_claim_dedicated_x_search():
    description = grok_cli_mcp.TOOLS["grok_research"]["description"]
    assert "not a guaranteed dedicated X Search API" in description


def test_grok_45_rejects_unsupported_effort(tmp_path: Path):
    try:
        grok_cli_mcp._build_command(
            "/tmp/grok", "Question", {"effort": "max"}, tmp_path
        )
    except grok_cli_mcp.GrokCliError as exc:
        assert "low, medium, or high" in str(exc)
    else:
        raise AssertionError("Expected GrokCliError")


def test_media_generation_requires_confirmation():
    try:
        grok_cli_mcp.tool_generate_image(
            {
                "prompt": "A mountain lake",
                "quality": "high",
                "resolution": "2k",
                "aspect_ratio": "16:9",
            }
        )
    except grok_cli_mcp.GrokCliError as exc:
        assert "AskUserQuestion/request_user_input" in str(exc)
    else:
        raise AssertionError("Expected GrokCliError")


def test_media_tool_schemas_require_confirmed_output_settings():
    image_required = set(
        grok_cli_mcp.TOOLS["grok_generate_image"]["inputSchema"]["required"]
    )
    video_required = set(
        grok_cli_mcp.TOOLS["grok_generate_video"]["inputSchema"]["required"]
    )
    assert {
        "confirmed_settings",
        "quality",
        "resolution",
        "aspect_ratio",
    } <= image_required
    assert {
        "confirmed_settings",
        "quality",
        "resolution",
        "duration",
        "aspect_ratio",
    } <= video_required
    video_properties = grok_cli_mcp.TOOLS["grok_generate_video"]["inputSchema"][
        "properties"
    ]
    assert video_properties["duration"]["enum"] == [6, 10]
    assert video_properties["resolution"]["enum"] == ["480p", "720p"]


def test_image_generation_passes_confirmed_settings(monkeypatch):
    captured = {}

    def fake_run(prompt, args):
        captured["prompt"] = prompt
        captured["args"] = args
        return {"ok": True, "answer": "/tmp/image.png"}

    monkeypatch.setattr(grok_cli_mcp, "_run_grok", fake_run)
    result = grok_cli_mcp.tool_generate_image(
        {
            "prompt": "A mountain lake",
            "confirmed_settings": True,
            "quality": "high",
            "resolution": "2k",
            "aspect_ratio": "16:9",
        }
    )

    assert "grok-imagine-image-quality" in captured["prompt"]
    assert "Resolution: 2k" in captured["prompt"]
    assert result["media"]["model"] == "grok-imagine-image-quality"


def test_video_generation_rejects_unsupported_cli_settings(monkeypatch):
    monkeypatch.setattr(
        grok_cli_mcp,
        "_run_grok",
        lambda prompt, args: {"ok": True, "answer": "/tmp/video.mp4"},
    )
    try:
        grok_cli_mcp.tool_generate_video(
            {
                "prompt": "A mountain flyover",
                "confirmed_settings": True,
                "quality": "standard",
                "resolution": "1080p",
                "duration": 10,
                "aspect_ratio": "16:9",
            }
        )
    except grok_cli_mcp.GrokCliError as exc:
        assert "480p or 720p" in str(exc)
    else:
        raise AssertionError("Expected GrokCliError")


def test_video_generation_uses_single_clip_workflow_with_source(monkeypatch):
    captured = {}

    def fake_run(prompt, args):
        captured["prompt"] = prompt
        captured["args"] = args
        return {"ok": True, "answer": "/tmp/video.mp4"}

    monkeypatch.setattr(grok_cli_mcp, "_run_grok", fake_run)
    result = grok_cli_mcp.tool_generate_video(
        {
            "prompt": "Animate the clouds",
            "confirmed_settings": True,
            "quality": "high",
            "resolution": "720p",
            "duration": 10,
            "aspect_ratio": "16:9",
            "source_image_path": "/tmp/source.png",
        }
    )

    assert "image_to_video at exactly 10 seconds" in captured["prompt"]
    assert "/tmp/source.png" in captured["prompt"]
    assert result["media"]["resolution"] == "720p"


def test_video_generation_rejects_old_15_second_duration(monkeypatch):
    monkeypatch.setattr(
        grok_cli_mcp,
        "_run_grok",
        lambda prompt, args: {"ok": True, "answer": "/tmp/video.mp4"},
    )
    try:
        grok_cli_mcp.tool_generate_video(
            {
                "prompt": "A mountain flyover",
                "confirmed_settings": True,
                "quality": "standard",
                "resolution": "720p",
                "duration": 15,
                "aspect_ratio": "16:9",
            }
        )
    except grok_cli_mcp.GrokCliError as exc:
        assert "6 or 10 seconds" in str(exc)
    else:
        raise AssertionError("Expected GrokCliError")
