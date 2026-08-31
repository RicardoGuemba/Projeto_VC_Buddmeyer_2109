#!/usr/bin/env bash
# Validação manual de recovery PLC (dev/lab com SimulatedPLC).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
python -m pytest tests/test_plc_recovery.py -q
echo "Recovery matrix OK — reinicie o serviço em campo para validação integrada."
