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


def test_image_quality_maps_to_expected_models():
    assert hermes_grok_mcp._normalize_image_args({"prompt": "a cat"})["model"] == "grok-imagine-image"
    assert (
        hermes_grok_mcp._normalize_image_args({"prompt": "a cat", "quality": "high"})["model"]
        == "grok-imagine-image-quality"
    )
    assert (
        hermes_grok_mcp._normalize_image_args(
            {"prompt": "a cat", "quality": "high", "model": "custom-image-model"}
        )["model"]
        == "custom-image-model"
    )
    assert "quality" not in hermes_grok_mcp._normalize_image_args({"prompt": "a cat", "quality": "high"})


def test_video_quality_maps_to_expected_models():
    assert hermes_grok_mcp._normalize_video_args({"prompt": "a scene"})["model"] == "grok-imagine-video"
    assert (
        hermes_grok_mcp._normalize_video_args(
            {"prompt": "animate this", "image_url": "https://example.com/image.png", "quality": "quality"}
        )["model"]
        == "grok-imagine-video-1.5"
    )


def test_video_quality_model_rejects_text_only_generation():
    try:
        hermes_grok_mcp._normalize_video_args({"prompt": "a text only video", "quality": "high"})
    except hermes_grok_mcp.HermesBridgeError as exc:
        assert "does not support text-to-video" in str(exc)
    else:
        raise AssertionError("Expected HermesBridgeError")


def test_video_quality_alias_rejects_text_only_generation():
    try:
        hermes_grok_mcp._normalize_video_args(
            {"prompt": "a text only video", "model": "grok-imagine-video-1.5-preview"}
        )
    except hermes_grok_mcp.HermesBridgeError as exc:
        assert "does not support text-to-video" in str(exc)
    else:
        raise AssertionError("Expected HermesBridgeError")
