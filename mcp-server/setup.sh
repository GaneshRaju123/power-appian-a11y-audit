#!/bin/bash
# Auto-setup script for the A11y Audit MCP server
# Kiro runs this when the power is installed

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🔧 Setting up Appian A11y Audit MCP server..."

# Create virtual environment if it doesn't exist
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/.venv"
fi

# Activate and install dependencies
echo "📥 Installing dependencies..."
"$SCRIPT_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$SCRIPT_DIR/.venv/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"

echo "✅ Setup complete!"
