#!/bin/bash
# Runner script — uses the venv Python to start the MCP server
# This is what Kiro calls via package.json

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Auto-setup if venv doesn't exist yet
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    bash "$SCRIPT_DIR/setup.sh"
fi

exec "$SCRIPT_DIR/.venv/bin/python3" "$SCRIPT_DIR/server.py"
