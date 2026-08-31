#!/usr/bin/env bash
# Realtec Vision Buddmeyer - Launcher Linux/macOS
# Uso: ./Iniciar_Realtec_Vision.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/realtec_vision_buddmeyer"

if [ -d "../venv/bin" ] && [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
elif [ -d ".venv/bin" ] && [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

exec python main.py
