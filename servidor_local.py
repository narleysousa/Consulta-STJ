#!/usr/bin/env python3
"""Servidor local para o site estatico com proxy Datajud.

Use este arquivo quando quiser testar a consulta ao vivo no navegador local.
`python -m http.server` serve os arquivos, mas nao cria o endpoint
`/api/datajud`; este servidor faz as duas coisas.
"""

from __future__ import annotations

import json
import mimetypes
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

API_URL = "https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search"
API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/api/datajud":
            self.send_error(404, "Endpoint nao encontrado")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(content_length)
            json.loads(payload.decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            self._json_response(400, {"error": "JSON invalido"})
            return

        req = urllib.request.Request(
            API_URL,
            data=payload,
            headers={
                "Authorization": f"APIKey {API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.HTTPError as exc:
            body = exc.read() or json.dumps({"error": f"Datajud HTTP {exc.code}"}).encode("utf-8")
            self.send_response(exc.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except urllib.error.URLError as exc:
            self._json_response(502, {"error": f"Falha ao acessar Datajud: {exc.reason}"})

    def guess_type(self, path: str) -> str:
        if path.endswith(".js"):
            return "text/javascript"
        return mimetypes.guess_type(path)[0] or super().guess_type(path)

    def _json_response(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Site local em http://127.0.0.1:8765")
    print("Proxy Datajud em http://127.0.0.1:8765/api/datajud")
    server.serve_forever()


if __name__ == "__main__":
    main()
