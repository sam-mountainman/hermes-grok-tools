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
    }


def test_initialize_response_shape():
    response = grok_cli_mcp._handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )
    assert response["id"] == 1
    assert response["result"]["serverInfo"]["name"] == "grok-cli"
    assert response["result"]["serverInfo"]["version"] == "1.0.0"
    assert "tools" in response["result"]["capabilities"]


def test_tools_list_response_is_json_serializable():
    response = grok_cli_mcp._handle_request(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    )
    encoded = json.dumps(response)
    assert "grok_ask" in encoded
    assert "grok_review" in encoded


def test_build_command_uses_grok_45_and_read_only_flags(tmp_path: Path):
    command = grok_cli_mcp._build_command("/tmp/grok", "Question", {}, tmp_path)
    assert command[:4] == ["/tmp/grok", "--no-auto-update", "-p", "Question"]
    assert command[command.index("--model") + 1] == "grok-4.5"
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
        {"model": "grok-custom", "effort": "max", "session_id": "session-123"},
        tmp_path,
    )
    assert command[command.index("--model") + 1] == "grok-custom"
    assert command[command.index("--effort") + 1] == "max"
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


def test_research_description_does_not_claim_dedicated_x_search():
    description = grok_cli_mcp.TOOLS["grok_research"]["description"]
    assert "not a guaranteed dedicated X Search API" in description
