# STJ Paraná — Consulta Processual

Automatiza a busca de processos no **STJ com origem no Paraná (TJPR)** com:

- **Trânsito em julgado** (TPU 848)
- **Baixa definitiva** (TPU 22)

Usa a [API pública do Datajud/CNJ](https://datajud-wiki.cnj.jus.br/api-publica/).

## Rodar no GitHub

O site fica em **`docs/`** na branch **`main`**. O GitHub Pages publica essa pasta automaticamente.

### ⚠️ Ativar o site (obrigatório — só uma vez)

👉 **[ATIVAR-SITE.md](ATIVAR-SITE.md)** — passo a passo com prints

Resumo rápido:

1. **Settings** → **Pages** → [link direto](https://github.com/narleysousa/Consulta-STJ/settings/pages)
2. Source: **Deploy from a branch**
3. Branch: **`main`** | Folder: **`/docs`**
4. **Save**

Site: **https://narleysousa.github.io/Consulta-STJ/**

### Executar consulta

1. Aba **Actions** → workflow **Consulta STJ**
2. **Run workflow**
3. Informe período, modo e limite → **Run workflow**

A Action consulta a API, gera CSV/Excel/JSON e publica o site.

### 3. Ver resultados

- **Site:** https://narleysousa.github.io/Consulta-STJ/
- **Downloads:** CSV e Excel na própria página
- **Artefatos:** na execução da Action (aba Artifacts)

### Agendamento automático

O workflow roda **de segunda a sexta às 08h (Brasília)** com os últimos 30 dias.

## Executar localmente

```bash
git clone https://github.com/narleysousa/Consulta-STJ.git
cd Consulta-STJ
pip install -r requirements.txt
```

### Gerar site (igual ao GitHub Actions)

```bash
python3 gerar_site.py \
  --modo ambos \
  --data-inicio 2026-06-01 \
  --data-fim 2026-06-16 \
  --limite 200
```

Arquivos em `docs/` — abra `docs/index.html` no navegador.

### Linha de comando (só exportar)

```bash
python3 consulta_stj_parana.py \
  --modo ambos \
  --data-inicio 2026-06-01 \
  --data-fim 2026-06-16 \
  --tipo-data movimentacao \
  --limite 200 \
  --excel resultado.xlsx
```

### Interface web local (opcional)

```bash
pip install -r requirements-web.txt
./iniciar.sh
```

### Site estático com consulta ao vivo local

Para testar a página de `docs/` com busca funcionando no navegador, use o servidor local com proxy:

```bash
python3 servidor_local.py
```

Abra `http://127.0.0.1:8765/`. Não use `python3 -m http.server` para a busca ao vivo, porque ele não cria o endpoint `/api/datajud`.

## Estrutura

```
.
├── consulta_stj_parana.py    # Motor da consulta + CLI
├── gerar_site.py             # Gera docs/ para GitHub Pages
├── docs/index.html           # Página pública
├── .github/workflows/
│   ├── consulta.yml            # Consulta API + atualiza docs/
│   └── ci.yml                  # Verificação no push
├── app.py                    # Interface Streamlit (opcional, local)
└── requirements.txt
```

## Critérios de filtro

| Modo       | Descrição                                   |
|------------|---------------------------------------------|
| `ambos`    | Trânsito em julgado **e** baixa definitiva  |
| `transito` | Somente trânsito em julgado                 |
| `baixa`    | Somente baixa definitiva                    |
| `qualquer` | Trânsito **ou** baixa definitiva            |

Processos do Paraná: padrão `.8.16.` no número CNJ (TJPR).
