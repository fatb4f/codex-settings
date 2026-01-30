#!/usr/bin/env bash
set -euo pipefail

CONTRACT_PATH="${1:-}"
if [[ -z "$CONTRACT_PATH" ]]; then
  echo "Usage: run_packet.sh <contract_path>" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLANT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

python "${PLANT_ROOT}/tools/run_packet.py" "$CONTRACT_PATH"
