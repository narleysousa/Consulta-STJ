#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

echo "Site local com consulta ao vivo em http://127.0.0.1:8765"
echo "Pressione Ctrl+C para encerrar."
exec python3 servidor_local.py
