import json
import subprocess
import sys
from pathlib import Path


def test_write_mcp_json_adds_server(tmp_path: Path):
    config = tmp_path / "mcp.json"
    script = (
        Path(__file__).resolve().parents[1]
        / "plugins"
        / "grok-cli-tools"
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
            "grok-cli",
            "--python",
            sys.executable,
            "--server",
            "/tmp/grok_cli_mcp.py",
            "--grok-cli-bin",
            "/tmp/grok",
        ]
    )
    data = json.loads(config.read_text(encoding="utf-8"))
    server = data["mcpServers"]["grok-cli"]
    assert server["command"] == sys.executable
    assert server["args"] == ["/tmp/grok_cli_mcp.py"]
    assert server["env"]["GROK_CLI_BIN"] == "/tmp/grok"
