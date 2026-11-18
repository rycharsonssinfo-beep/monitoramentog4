#!/usr/bin/env python3
"""Ajuste seguro e idempotente da área reservada à barra do Monitor v3.54.0."""
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
MARKER = "ss-bar-safe-area-v354"
ANCHOR = "body.controls-overlay #stage{top:0!important;height:calc(100vh - var(--ticker-h))!important;bottom:auto!important}"
SAFE_CSS = (
    "/* " + MARKER + " */"
    "body.bar-top.controls-overlay #stage,body.bar-top.controls-hidden #stage{"
    "top:calc(var(--toolbar-h) + var(--progress-h))!important;"
    "height:calc(100vh - var(--toolbar-h) - var(--progress-h) - var(--ticker-h))!important;"
    "bottom:auto!important;transition:none!important}"
    "body.bar-bottom.controls-overlay #stage,body.bar-bottom.controls-hidden #stage{"
    "top:0!important;"
    "height:calc(100vh - var(--toolbar-h) - var(--progress-h) - var(--ticker-h))!important;"
    "bottom:auto!important;transition:none!important}"
)

def apply(text: str) -> str:
    if MARKER not in text:
        if text.count(ANCHOR) != 1:
            raise ValueError("Âncora CSS da barra não é única. Arquivo preservado.")
        text = text.replace(ANCHOR, ANCHOR + SAFE_CSS, 1)
    if 'APP_VERSION = "3.53.0"' in text:
        if text.count('APP_VERSION = "3.53.0"') != 1:
            raise ValueError("Declarações de versão repetidas. Arquivo preservado.")
        text = text.replace('APP_VERSION = "3.53.0"', 'APP_VERSION = "3.54.0"', 1)
    if text.count(MARKER) != 1 or text.count('APP_VERSION = "3.54.0"') != 1:
        raise ValueError("Versão/ajuste da barra ausente ou duplicado.")
    ast.parse(text, filename="main.py")
    return text

def main() -> None:
    original = MAIN.read_text(encoding="utf-8")
    updated = apply(original)
    if updated != original:
        MAIN.write_text(updated, encoding="utf-8")
        print("OK: barra com espaço superior fixo, sem sobreposição e sem redimensionamento.")
    else:
        print("OK: ajuste v3.54.0 já aplicado.")
if __name__ == "__main__":
    main()
