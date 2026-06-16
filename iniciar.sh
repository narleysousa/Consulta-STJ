#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if ! python3 -c "import streamlit" 2>/dev/null; then
  echo "Instalando dependências..."
  pip3 install -r requirements-web.txt
fi

echo "Iniciando STJ Paraná em http://localhost:8501"
exec python3 -m streamlit run app.py --server.port 8501
