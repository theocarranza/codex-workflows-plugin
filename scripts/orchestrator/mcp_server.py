from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from .engine import OrchestratorEngine


def default_skills_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "skills"


def handle_list_tools(engine: OrchestratorEngine) -> dict[str, Any]:
    return {"tools": engine.list_tools()}


def process_message(line: str, engine: OrchestratorEngine) -> str:
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return ""

    if "id" not in msg or "method" not in msg:
        return ""

    msg_id = msg["id"]
    method = msg["method"]
    response: dict[str, Any] = {"jsonrpc": "2.0", "id": msg_id}

    try:
        if method == "initialize":
            response["result"] = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "agentic-orchestrator", "version": "1.0.0"},
            }
        elif method == "tools/list":
            response["result"] = handle_list_tools(engine)
        elif method == "tools/call":
            params = msg.get("params", {})
            name = params.get("name")
            args = params.get("arguments") or {}
            result = engine.run_tool_call(name, args)
            if result.ok:
                response["result"] = {"content": result.to_mcp_content()}
            else:
                response["result"] = {
                    "content": result.to_mcp_content(),
                    "isError": True,
                }
        elif method == "notifications/initialized":
            return ""
        else:
            response["error"] = {"code": -32601, "message": f"Method not found: {method}"}
    except Exception as exc:
        response["error"] = {"code": -32603, "message": str(exc)}

    return json.dumps(response)


def main() -> None:
    skills_dir = Path(os.environ.get("ORCHESTRATOR_SKILLS_DIR", default_skills_dir()))
    engine = OrchestratorEngine(skills_dir)
    for line in sys.stdin:
        if line.strip():
            res = process_message(line, engine)
            if res:
                print(res, flush=True)


if __name__ == "__main__":
    main()
