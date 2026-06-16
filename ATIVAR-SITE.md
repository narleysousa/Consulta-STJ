# ⚠️ ATIVAR O SITE (obrigatório — só uma vez)

O site **não funciona** até você fazer isso:

## Passo a passo

1. Abra: **https://github.com/narleysousa/Consulta-STJ/settings/pages**

2. Em **Build and deployment** → **Source**, escolha:
   **Deploy from a branch**

3. Configure exatamente assim:

   | Campo  | Valor    |
   |--------|----------|
   | Branch | `main`   |
   | Folder | `/docs`  |

4. Clique em **Save**

5. Aguarde 1–2 minutos e acesse:
   **https://narleysousa.github.io/Consulta-STJ/**

---

## Se ainda der 404

- Confirme que está **`main`** + **`/docs`** (não `gh-pages`, não `/root`)
- Vá em **Actions** → **Consulta STJ** → **Run workflow** (para gerar dados)
- Espere 2–3 minutos após o Save

## Rodar nova consulta

**Actions** → **Consulta STJ** → **Run workflow**
