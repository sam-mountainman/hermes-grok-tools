import json
import importlib.util
from pathlib import Path


SERVER_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "hermes-grok-tools"
    / "scripts"
    / "hermes_grok_mcp.py"
)
SPEC = importlib.util.spec_from_file_location("hermes_grok_mcp", SERVER_PATH)
hermes_grok_mcp = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(hermes_grok_mcp)


def test_tool_list_contains_expected_tools():
    names = {tool["name"] for tool in hermes_grok_mcp._mcp_tool_list()}
    assert "hermes_grok_status" in names
    assert "hermes_x_search" in names
    assert "hermes_grok_image" in names
    assert "hermes_grok_video" in names


def test_initialize_response_shape():
    response = hermes_grok_mcp._handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )
    assert response["id"] == 1
    assert response["result"]["serverInfo"]["name"] == "hermes-grok"
    assert "tools" in response["result"]["capabilities"]


def test_tools_list_response_is_json_serializable():
    response = hermes_grok_mcp._handle_request(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    )
    encoded = json.dumps(response)
    assert "hermes_x_search" in encoded
