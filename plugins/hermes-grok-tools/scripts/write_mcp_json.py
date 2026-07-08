#!/usr/bin/env python3
"""Add or update a stdio MCP server entry in a JSON config file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--name", default="hermes-grok")
    parser.add_argument("--python", required=True)
    parser.add_argument("--server", required=True)
    parser.add_argument("--hermes-agent-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.config).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SystemExit(f"{path} must contain a JSON object")
    else:
        data = {}

    servers = data.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise SystemExit(f"{path}: mcpServers must be a JSON object")

    env = {"PYTHONUNBUFFERED": "1"}
    if args.hermes_agent_path:
        env["HERMES_AGENT_PATH"] = args.hermes_agent_path

    servers[args.name] = {
        "command": args.python,
        "args": [args.server],
        "env": env,
    }

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
