#!/bin/bash
# Abre o Streamlit Community Cloud para deploy deste app.
# Deploy via API (opcional): export STREAMLIT_TOKEN="seu-token" && ./deploy_streamlit.sh --api

set -euo pipefail

REPO="narleysousa/Consulta-STJ"
BRANCH="main"
MAIN_FILE="app.py"
APP_NAME="consulta-stj"
GITHUB_APP_URL="https://github.com/${REPO}/blob/${BRANCH}/${MAIN_FILE}"

if [[ "${1:-}" == "--api" ]]; then
  if [[ -z "${STREAMLIT_TOKEN:-}" ]]; then
    echo "Defina STREAMLIT_TOKEN (Settings → API tokens em share.streamlit.io)"
    exit 1
  fi
  echo "Iniciando deploy via API..."
  curl -fsS -X POST "https://api.streamlit.io/v1/apps" \
    -H "Authorization: Bearer ${STREAMLIT_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"repo\":\"${REPO}\",\"branch\":\"${BRANCH}\",\"mainFile\":\"${MAIN_FILE}\",\"appName\":\"${APP_NAME}\"}"
  echo ""
  echo "Deploy solicitado. Acompanhe em https://share.streamlit.io"
  exit 0
fi

echo "════════════════════════════════════════════════════════"
echo "  Deploy no Streamlit Community Cloud"
echo "════════════════════════════════════════════════════════"
echo ""
echo "  Repositório : ${REPO}"
echo "  Branch      : ${BRANCH}"
echo "  Arquivo     : ${MAIN_FILE}"
echo "  Python      : 3.11 (runtime.txt)"
echo ""
echo "  URL sugerida: https://${APP_NAME}.streamlit.app"
echo ""
echo "  Passos:"
echo "  1. Faça login com GitHub em share.streamlit.io"
echo "  2. Clique em 'Create app' → 'Yup, I have an app'"
echo "  3. Cole a URL do GitHub ou preencha os campos acima"
echo "  4. Advanced settings → Python 3.11 → Deploy"
echo ""
echo "  URL do app no GitHub:"
echo "  ${GITHUB_APP_URL}"
echo "════════════════════════════════════════════════════════"

if command -v open >/dev/null 2>&1; then
  open "https://share.streamlit.io/deploy"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "https://share.streamlit.io/deploy"
else
  echo "Abra manualmente: https://share.streamlit.io/deploy"
fi
