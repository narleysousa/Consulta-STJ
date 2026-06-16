# STJ Paraná — Consulta Processual

Ferramenta para automatizar a busca de processos no **STJ com origem no Paraná (TJPR)** que possuem:

- **Trânsito em julgado** (movimento TPU 848)
- **Baixa definitiva / baixa dos autos à origem** (movimento TPU 22)

Utiliza a [API pública do Datajud/CNJ](https://datajud-wiki.cnj.jus.br/api-publica/).

## Funcionalidades

- Busca por período com filtros de data (movimentação, ajuizamento ou última atualização)
- Busca por um ou mais números CNJ
- Tabela de resultados com filtros e exportação CSV/Excel
- Detalhes e timeline de movimentos ao clicar em um processo
- Linha de comando para automação e exportação em lote

## Executar localmente

### Pré-requisitos

- Python 3.10 ou superior

### Instalação

```bash
git clone https://github.com/narleysousa/Consulta-STJ.git
cd Consulta-STJ
pip install -r requirements.txt
```

### Interface web

```bash
python3 -m streamlit run app.py
```

Ou:

```bash
chmod +x iniciar.sh
./iniciar.sh
```

Acesse: **http://localhost:8501**

### Linha de comando

```bash
# Últimos 30 dias — trânsito + baixa
python3 consulta_stj_parana.py \
  --modo ambos \
  --data-inicio 2026-05-01 \
  --data-fim 2026-06-16 \
  --tipo-data movimentacao \
  --limite 200

# Exportar para Excel
python3 consulta_stj_parana.py \
  --modo ambos \
  --data-inicio 2026-01-01 \
  --data-fim 2026-06-16 \
  --excel resultado.xlsx
```

## Publicar no GitHub

```bash
cd Consulta-STJ
git init
git add .
git commit -m "Publica consulta STJ Paraná"
git branch -M main
git remote add origin https://github.com/narleysousa/Consulta-STJ.git
git push -u origin main
```

## Deploy no Streamlit Community Cloud

### Opção 1 — Pelo navegador (recomendado)

```bash
chmod +x deploy_streamlit.sh
./deploy_streamlit.sh
```

Ou acesse [share.streamlit.io/deploy](https://share.streamlit.io/deploy) e preencha:

| Campo | Valor |
|-------|-------|
| Repositório | `narleysousa/Consulta-STJ` |
| Branch | `main` |
| Arquivo principal | `app.py` |
| Python (Advanced) | `3.11` |
| URL personalizada (opcional) | `consulta-stj` → `https://consulta-stj.streamlit.app` |

Também pode colar diretamente a URL do GitHub:

`https://github.com/narleysousa/Consulta-STJ/blob/main/app.py`

### Opção 2 — Via API (automatizado)

1. Gere um token em [share.streamlit.io](https://share.streamlit.io) → **Settings** → **API tokens**
2. Execute:

```bash
export STREAMLIT_TOKEN="seu-token-aqui"
./deploy_streamlit.sh --api
```

O projeto já inclui `requirements.txt`, `runtime.txt` e `.streamlit/config.toml` prontos para o deploy.

## Estrutura do projeto

```
.
├── app.py                    # Interface web (Streamlit)
├── consulta_stj_parana.py    # Backend e CLI
├── requirements.txt
├── runtime.txt
├── iniciar.sh
├── .streamlit/config.toml
└── .github/workflows/ci.yml
```

## Critérios de filtro

| Modo       | Descrição                                      |
|------------|------------------------------------------------|
| `ambos`    | Trânsito em julgado **e** baixa definitiva     |
| `transito` | Somente trânsito em julgado                    |
| `baixa`    | Somente baixa definitiva                       |
| `qualquer` | Trânsito **ou** baixa definitiva               |

Processos do Paraná são identificados pelo padrão `.8.16.` no número CNJ (Justiça Estadual / TJPR).

## Licença

Uso livre. A API do Datajud é pública e sujeita aos termos do CNJ.
