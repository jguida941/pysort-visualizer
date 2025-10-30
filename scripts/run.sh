#!/usr/bin/env bash

set -Eeuo pipefail

# Resolve repository root no matter where the script is invoked from
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
VENV_PATH="$PROJECT_ROOT/.venv"
ACTIVATE_SCRIPT="$VENV_PATH/bin/activate"
INSTALL_STAMP="$VENV_PATH/.deps-installed"

# Create the virtual environment if it does not exist yet
if [[ ! -d "$VENV_PATH" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_PATH"
fi

# shellcheck disable=SC1090
source "$ACTIVATE_SCRIPT"

# Install dependencies once, or again if requirements.txt changed
if [[ ! -f "$INSTALL_STAMP" || "$PROJECT_ROOT/requirements.txt" -nt "$INSTALL_STAMP" ]]; then
  pip install --disable-pip-version-check -r "$PROJECT_ROOT/requirements.txt"
  touch "$INSTALL_STAMP"
fi

# Launch the PyQt6 app
python "$PROJECT_ROOT/main.py"
