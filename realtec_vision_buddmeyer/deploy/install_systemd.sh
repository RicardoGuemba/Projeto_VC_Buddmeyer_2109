#!/usr/bin/env bash
# Instala unit systemd para Realtec Vision Buddmeyer (Ubuntu box PC).
# Uso: sudo ./install_systemd.sh [/caminho/para/clone]

set -euo pipefail

INSTALL_ROOT="${1:-$(cd "$(dirname "$0")/../.." && pwd)}"
PKG_DIR="${INSTALL_ROOT}/realtec_vision_buddmeyer"
UNIT_NAME="realtec-vision.service"
UNIT_SRC="${PKG_DIR}/deploy/${UNIT_NAME}"
UNIT_DST="/etc/systemd/system/${UNIT_NAME}"

if [[ ! -f "${UNIT_SRC}" ]]; then
  echo "Erro: unit não encontrada em ${UNIT_SRC}" >&2
  exit 1
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Execute com sudo: sudo $0 [INSTALL_ROOT]" >&2
  exit 1
fi

sed "s|%i|${INSTALL_ROOT}|g" "${UNIT_SRC}" > "${UNIT_DST}"
systemctl daemon-reload
systemctl enable "${UNIT_NAME}"
echo "Instalado ${UNIT_DST}"
echo "Arranque: sudo systemctl start ${UNIT_NAME}"
echo "Estado:  systemctl status ${UNIT_NAME}"
