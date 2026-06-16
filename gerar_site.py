#!/usr/bin/env python3
"""Executa a consulta e gera arquivos para GitHub Pages (docs/)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from consulta_stj_parana import (
    FiltroDatas,
    buscar_processos,
    exportar_csv,
    exportar_excel,
)

DOCS = Path(__file__).resolve().parent / "docs"


def processo_para_json(proc) -> dict:
    dados = proc.as_dict()
    dados["timeline"] = [
        {
            "codigo": m.codigo,
            "nome": m.nome,
            "data": m.data_formatada(),
            "orgao": m.orgao,
        }
        for m in proc.timeline
    ]
    return dados


def main() -> int:
    parser = argparse.ArgumentParser(description="Consulta STJ Paraná e gera site em docs/")
    parser.add_argument("--modo", choices=["ambos", "transito", "baixa", "qualquer"], default="ambos")
    parser.add_argument("--data-inicio", required=True, help="AAAA-MM-DD")
    parser.add_argument("--data-fim", required=True, help="AAAA-MM-DD")
    parser.add_argument("--tipo-data", choices=["movimentacao", "ajuizamento", "atualizacao"], default="movimentacao")
    parser.add_argument("--limite", type=int, default=200)
    args = parser.parse_args()

    filtro = FiltroDatas(
        data_inicio=datetime.strptime(args.data_inicio, "%Y-%m-%d").date(),
        data_fim=datetime.strptime(args.data_fim, "%Y-%m-%d").date(),
        tipo=args.tipo_data,
    )
    filtro.validar()

    print("Consultando API Datajud...", file=sys.stderr)
    processos = buscar_processos(modo=args.modo, limite=args.limite, filtro_datas=filtro)

    DOCS.mkdir(exist_ok=True)
    exportar_csv(DOCS / "resultados.csv", processos)
    exportar_excel(DOCS / "resultados.xlsx", processos)

    payload = {
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "filtro": {
            "data_inicio": args.data_inicio,
            "data_fim": args.data_fim,
            "modo": args.modo,
            "tipo_data": args.tipo_data,
            "limite": args.limite,
        },
        "total": len(processos),
        "processos": [processo_para_json(p) for p in processos],
    }
    (DOCS / "resultados.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"OK: {len(processos)} processo(s) → {DOCS}/", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
