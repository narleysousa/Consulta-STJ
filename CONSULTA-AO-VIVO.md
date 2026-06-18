# Consulta ao vivo — qual opção usar?

O **GitHub Pages** só serve arquivos estáticos. A API do Datajud **bloqueia** chamadas diretas do navegador (CORS). Por isso o botão no Pages **não consulta na hora** — ele dispara uma atualização via GitHub Actions.

## Opção A — Vercel (recomendado: consulta com 1 clique)

1. Abra: [Deploy na Vercel (1 clique)](https://vercel.com/new/clone?repository-url=https://github.com/narleysousa/Consulta-STJ&project-name=consulta-stj)
2. Faça login com GitHub → **Deploy** (sem mudar nada)
3. Use a URL gerada (ex.: `consulta-stj.vercel.app`) — consulta instantânea funciona

O repositório já inclui `vercel.json` e `api/datajud.js` (proxy gratuito).

## Opção B — GitHub Actions (já no Pages, ~1–2 min)

No site do GitHub Pages:

1. Configure os filtros na barra lateral
2. Clique **Atualizar dados (GitHub Actions)**
3. Na página que abrir, clique **Run workflow** com os valores indicados
4. O site aguarda e atualiza sozinho quando a Action terminar

A Action roda de segunda a sexta às 8h (horário de Brasília) automaticamente.

## Opção C — No seu computador (instantâneo, sem cadastro)

```bash
./iniciar-site.sh
```

Abre em http://127.0.0.1:8765 com a mesma interface e consulta ao vivo.

Alternativa com interface Streamlit:

```bash
./iniciar.sh
```

Abre em http://localhost:8501
