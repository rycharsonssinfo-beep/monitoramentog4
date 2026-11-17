#!/usr/bin/env python3
"""Ajusta exibição da barra do Monitor sem redimensionar os painéis.
Aplica mudanças pontuais e idempotentes ao HTML da Central do Monitor.
"""
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
CHECK_ONLY = "--check" in sys.argv
MARKER = "ss-controls-edge-only-v1"

CSS_BEFORE = (
    "body.controls-hidden #stage{top:0!important;"
    "height:calc(100vh - var(--ticker-h))!important;bottom:auto!important}"
)
CSS_AFTER = (
    CSS_BEFORE
    + "/* " + MARKER + " */"
    + "body.controls-overlay #stage{top:0!important;"
    "height:calc(100vh - var(--ticker-h))!important;bottom:auto!important}"
)

CONTROLS_BEFORE = """            function showControls(){
                const wasHidden=controlShell.classList.contains('hidden');
                controlShell.classList.remove('hidden'); document.body.classList.remove('controls-hidden'); document.body.style.cursor=''; clearTimeout(hideTimer);
                if(wasHidden)requestAnimationFrame(()=>updateFocus(Math.max(0,targetEndMs-Date.now()),true));
                if(settings.autoHide||kioskMode)hideTimer=setTimeout(hideControls,kioskMode?2200:4300);
            }
            function hideControls(){
                if(!(settings.autoHide||kioskMode))return;
                closeMoreMenu(); controlShell.classList.add('hidden'); document.body.classList.add('controls-hidden'); if(kioskMode)document.body.style.cursor='none';
                requestAnimationFrame(()=>updateFocus(Math.max(0,targetEndMs-Date.now()),true));
            }"""

CONTROLS_AFTER = """            function scheduleControlsHide(delayMs=kioskMode?2200:4300){
                clearTimeout(hideTimer);
                if(settings.autoHide||kioskMode)hideTimer=setTimeout(hideControls,delayMs);
            }
            function showControls(){
                // Barra flutuante: abrir/fechar não redimensiona nem recalcula o iframe.
                const overlay=Boolean(settings.autoHide||kioskMode);
                document.body.classList.toggle('controls-overlay',overlay);
                const wasHidden=controlShell.classList.contains('hidden');
                controlShell.classList.remove('hidden');
                document.body.classList.remove('controls-hidden');
                document.body.style.cursor='';
                if(wasHidden&&!overlay)requestAnimationFrame(()=>updateFocus(Math.max(0,targetEndMs-Date.now()),true));
                scheduleControlsHide();
            }
            function hideControls(){
                if(!(settings.autoHide||kioskMode))return;
                // Não ocultar controles enquanto o menu de opções está aberto.
                if(moreMenu&&moreMenu.classList.contains('open')){scheduleControlsHide();return;}
                controlShell.classList.add('hidden');
                document.body.classList.add('controls-hidden');
                if(kioskMode)document.body.style.cursor='none';
                if(!document.body.classList.contains('controls-overlay')){
                    requestAnimationFrame(()=>updateFocus(Math.max(0,targetEndMs-Date.now()),true));
                }
            }"""

EVENTS_BEFORE = """            document.addEventListener('mousemove',showControls,{passive:true}); document.addEventListener('touchstart',showControls,{passive:true});
            document.addEventListener('click',(e)=>{ if(moreMenu && !moreMenu.contains(e.target) && e.target!==moreBtn)closeMoreMenu(); });
            if(revealStrip){ revealStrip.addEventListener('mouseenter',showControls); revealStrip.addEventListener('touchstart',showControls,{passive:true}); }"""

EVENTS_AFTER = """            function nearControlEdge(y){
                if(!Number.isFinite(y))return false;
                const bottom=document.body.classList.contains('bar-bottom');
                return bottom?y>=window.innerHeight-12:y<=12;
            }
            // Apenas a borda da tela revela os controles; nenhum movimento no painel os abre.
            document.addEventListener('mousemove',(event)=>{
                if(nearControlEdge(event.clientY))showControls();
            },{passive:true});
            document.addEventListener('touchstart',(event)=>{
                const touch=event.touches&&event.touches[0];
                if(touch&&nearControlEdge(touch.clientY))showControls();
            },{passive:true});
            controlShell.addEventListener('mouseenter',()=>{
                if(!controlShell.classList.contains('hidden'))clearTimeout(hideTimer);
            });
            controlShell.addEventListener('mouseleave',()=>{
                if(!controlShell.classList.contains('hidden'))scheduleControlsHide(1100);
            });
            document.addEventListener('click',(e)=>{ if(moreMenu && !moreMenu.contains(e.target) && e.target!==moreBtn)closeMoreMenu(); });
            if(revealStrip){ revealStrip.addEventListener('mouseenter',showControls); revealStrip.addEventListener('touchstart',showControls,{passive:true}); }"""

def one_replace(source: str, old: str, new: str, name: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{name}: esperado 1 trecho único; encontrados {count}. Nenhuma alteração aplicada.")
    return source.replace(old, new, 1)

def verify(source: str) -> None:
    expected = (
        "body.controls-overlay #stage{top:0!important;",
        "function nearControlEdge(y){",
        "if(nearControlEdge(event.clientY))showControls();",
        "controlShell.addEventListener('mouseenter'",
        "controlShell.addEventListener('mouseleave'",
        "if(moreMenu&&moreMenu.classList.contains('open'))",
    )
    for item in expected:
        if item not in source:
            raise RuntimeError("Implementação incompleta: " + item)
    if "document.addEventListener('mousemove',showControls" in source:
        raise RuntimeError("Evento global anterior de exibição da barra ainda está ativo.")
    ast.parse(source, filename=str(MAIN))

def main() -> None:
    original = MAIN.read_text(encoding="utf-8")
    if MARKER in original:
        verify(original)
        print("Barra superior já ajustada e validada; sem alterações.")
        return
    if CHECK_ONLY:
        raise RuntimeError("A correção da barra ainda não foi aplicada.")
    source = one_replace(original, CSS_BEFORE, CSS_AFTER, "CSS da área dos painéis")
    source = one_replace(source, CONTROLS_BEFORE, CONTROLS_AFTER, "exibição e recolhimento dos controles")
    source = one_replace(source, EVENTS_BEFORE, EVENTS_AFTER, "eventos do ponteiro e toque")
    verify(source)
    MAIN.write_text(source, encoding="utf-8")
    print("Barra do monitor: ativação somente pela borda; painel estável; Python válido.")

if __name__ == "__main__":
    main()
