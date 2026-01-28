#!/bin/bash
# WSL launcher: runs run_app.ps1. Use: ./run_app.sh (from project dir)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIN_PATH="$(wslpath -w "$SCRIPT_DIR")/run_app.ps1"
exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$WIN_PATH"
