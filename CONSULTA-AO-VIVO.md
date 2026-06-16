# Consulta ao vivo no site

O GitHub Pages **não consegue** chamar a API do Datajud direto do navegador (bloqueio CORS).

## Opção A — Vercel (recomendado, consulta instantânea)

1. Acesse [vercel.com](https://vercel.com) → **Add New Project**
2. Importe o repositório **narleysousa/Consulta-STJ**
3. Deploy (sem alterar nada — usa `vercel.json` + pasta `api/`)
4. Use o site na URL da Vercel: consulta ao vivo funciona com um clique

O GitHub Pages continua funcionando para visualização; a Vercel adiciona o proxy `/api/datajud`.

## Opção B — GitHub Actions (já funciona)

Ao clicar **Consultar processos** no GitHub Pages:

1. O site abre a Action automaticamente
2. Clique **Run workflow** com as datas desejadas
3. O site aguarda e atualiza sozinho (~1–2 min)

## Opção C — Local (igual ao print do Streamlit)

```bash
pip install -r requirements-web.txt
./iniciar.sh
```

Abre em http://localhost:8501 com consulta instantânea.
