#!/bin/bash
set -e

# Resolve absolute path of this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOK_SCRIPT="$PROJECT_ROOT/scripts/codex_enforce_hook.py"
CONFIG_DIR="$HOME/.gemini/config"
HOOKS_JSON="$CONFIG_DIR/hooks.json"

echo "=== Codex Enforcer Hook Installer ==="

# 1. Check if the hook script exists
if [ ! -f "$HOOK_SCRIPT" ]; then
    echo "Error: Hook script not found at $HOOK_SCRIPT"
    exit 1
fi

# 2. Make hook script executable
echo "Making hook script executable..."
chmod +x "$HOOK_SCRIPT"

# 3. Ensure target config directory exists
echo "Ensuring config directory exists at $CONFIG_DIR..."
mkdir -p "$CONFIG_DIR"

# 4. Generate hooks.json pointing to the absolute path
echo "Writing hooks.json configuration..."
cat << EOF > "$HOOKS_JSON"
{
  "codex-enforcer": {
    "enabled": true,
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "$HOOK_SCRIPT",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
EOF

echo "Hooks registered successfully at $HOOKS_JSON"
echo "Setup complete!"
