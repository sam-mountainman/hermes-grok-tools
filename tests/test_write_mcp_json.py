import json
import subprocess
import sys
from pathlib import Path


def test_write_mcp_json_adds_server(tmp_path: Path):
    config = tmp_path / "mcp.json"
    script = (
        Path(__file__).resolve().parents[1]
        / "plugins"
        / "hermes-grok-tools"
        / "scripts"
        / "write_mcp_json.py"
    )
    subprocess.check_call(
        [
            sys.executable,
            str(script),
            "--config",
            str(config),
            "--name",
            "hermes-grok",
            "--python",
            sys.executable,
            "--server",
            "/tmp/hermes_grok_mcp.py",
            "--hermes-agent-path",
            "/tmp/hermes-agent",
        ]
    )
    data = json.loads(config.read_text(encoding="utf-8"))
    server = data["mcpServers"]["hermes-grok"]
    assert server["command"] == sys.executable
    assert server["args"] == ["/tmp/hermes_grok_mcp.py"]
    assert server["env"]["HERMES_AGENT_PATH"] == "/tmp/hermes-agent"
