#!/usr/bin/env bash

# Deploy script wrapper for setup.sh
# This script is an alias to setup.sh for consistency with naming conventions

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETUP_SCRIPT="$PROJECT_DIR/setup.sh"

if [ ! -f "$SETUP_SCRIPT" ]; then
  echo "Error: setup.sh not found in project root"
  exit 1
fi

# Call setup.sh with all arguments
chmod +x "$SETUP_SCRIPT"
exec "$SETUP_SCRIPT" "$@"
