# -*- coding: utf-8 -*-
"""Mapa de Sistemas do Monitor Grupo S&S.

Página isolada: não altera a lógica do SIM nem dos demais monitores.
Fonte preferencial: mapa_sistemas.json (dados explícitos).
Fonte complementar: URLs identificáveis no main.py, sempre com classificação conservadora.
"""
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parents[1]
GEO_URLS = [
    "https://cdn.jsdelivr.net/gh/henriquemalvar/br-geojson@main/dist/municipios/CE.geojson",
    "https://raw.githubusercontent.com/henriquemalvar/br-geojson/main/dist/municipios/CE.geojson",
]
SYSTEMS = ("Portal do Contribuinte", "Fluxus", "Veículos")
COLORS = {0: "#8995a8", 1: "#f5bf33", 2: "#15ad79", 3: "#1679d4"}


def norm(text):
    text = unicodedata.normalize("NFKD", str(text))
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in text if not unicodedata.combining(c)).lower())


def classify(url, near_text=""):
    lower = url.lower()
    context = near_text.lower()
    path = urlsplit(url).path.lower()
    host = (urlsplit(url).hostname or "").lower()
    if "/portal/" in path or ("portal" in host and "contrib" in context):
        return SYSTEMS[0]
    if "fluxus" in host or "fluxus" in path or ("fluxus" in context and "http" in lower):
        return SYSTEMS[1]
    if "veiculo" in host or "frotas" in host or "veiculo" in path or "frotas" in path:
        return SYSTEMS[2]
    return None


@st.cache_data(ttl=600, show_spinner=False)
def links_detectados():
    """Autoidentifica apenas URLs que carregam uma pista verificável do sistema.

    Sem correspondência ao município, o URL é ignorado no mapa.
    Dados explícitos do JSON prevalecem sobre detecção automática.
    """
    path = ROOT / "main.py"
    if not path.is_file():
        return []
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    found = []
    # Não executa nem importa o main.py: análise somente textual, sem efeitos colaterais.
    for match in re.finditer(r"https?://[^\s\"'<>\]\[{}\\]+", source):
        url = match.group(0).rstrip(".,;)'")
        if len(url) > 350 or "{" in url or "}" in url:
            continue
        near = source[max(0, match.start() - 110): match.start()]
        kind = classify(url, near)
        if kind:
            found.append({"url": url, "sistema": kind})
    return found


def registros_explicitos():
    """Formato: lista de {municipio, sistema, url}; nenhum status é presumido."""
    file = ROOT / "mapa_sistemas.json"
    if not file.is_file():
        return []
    try:
        raw = json.loads(file.read_text(encoding="utf-8"))
        entries = raw.get("registros", []) if isinstance(raw, dict) else raw
        return [
            {"municipio": x["municipio"], "sistema": x["sistema"], "url": x["url"]}
            for x in entries if isinstance(x, dict)
            and all(isinstance(x.get(k), str) for k in ("municipio", "sistema", "url"))
            and x["sistema"] in SYSTEMS
            and x["url"].startswith(("https://", "http://"))
        ]
    except (OSError, ValueError, TypeError, KeyError):
        return []


def registros():
    result = []
    seen = set()
    explicit = registros_explicitos()
    for item in explicit:
        key = (norm(item["municipio"]), item["sistema"], item["url"])
        if key not in seen:
            seen.add(key)
            result.append(item)
    # Descoberta automática apenas por domínio/subdomínio reconhecível.
    # Correspondência final de município acontece no navegador, pela malha oficial.
    for item in links_detectados():
        if item["url"] not in {x["url"] for x in explicit}:
            result.append(item)
    return result


st.set_page_config(page_title="Mapa de Sistemas | Grupo S&S", page_icon="🗺️", layout="wide")
# A página deve respeitar a sessão do Monitor, mesmo em acesso direto à URL.
import time
if (not st.session_state.get("_monitor_auth_authenticated")
        or not str(st.session_state.get("_monitor_auth_access_token") or "").strip()):
    st.error("Acesso restrito. Entre no Monitor Grupo S&S antes de abrir o mapa.")
    st.stop()
_exp = float(st.session_state.get("_monitor_auth_expires_at") or 0)
if _exp and time.time() >= (_exp - 90):
    st.warning("Sua sessão expirou. Volte ao Monitor para autenticar-se novamente.")
    st.stop()


st.markdown(
    "<style>.block-container{padding-top:1rem;padding-bottom:1rem;max-width:100%}"
    "header[data-testid='stHeader']{background:transparent}</style>",
    unsafe_allow_html=True,
)
payload = json.dumps(
    {"links": registros(), "geo_urls": GEO_URLS, "colors": COLORS},
    ensure_ascii=False,
).replace("</", "<\\/")

HTML = r"""
<!DOCTYPE html><html lang="pt-br"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
*{box-sizing:border-box}body{margin:0;color:#ecf4ff;background:#071b33;font-family:Inter,"Segoe UI",Arial,sans-serif}
.shell{min-height:820px;background:linear-gradient(120deg,#081a31,#092748);padding:22px;border-radius:16px}
h1{margin:0 0 5px;font-size:27px}.sub{color:#b6c9df;margin:0 0 18px;font-size:14px}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:17px}
.stat{border:1px solid #315572;background:#112d4d;border-radius:12px;padding:11px 16px;min-width:145px;flex:1}
.stat b{font-size:24px;display:block}.stat small{font-size:12px;color:#b5cbdd}
.columns{display:grid;grid-template-columns:245px minmax(320px,1fr) 340px;gap:14px;min-height:620px}
.panel{border:1px solid #294a6b;border-radius:14px;background:#102a49;padding:16px}
.panel h3{font-size:17px;margin:0 0 17px}.filters label{display:block;margin-bottom:14px;font-size:14px;cursor:pointer}
input[type=radio]{accent-color:#1686e4}input[type=text]{width:100%;border:1px solid #466785;padding:12px;background:#09213d;color:white;border-radius:8px}
#map{height:615px;border-radius:13px;background:#0c2441}.mapwrap{min-width:0}
.legend{margin-top:25px}.legend div{display:flex;align-items:center;margin:11px 0;gap:10px;font-size:12px}
.swatch{width:18px;height:18px;border-radius:5px;flex:none}
.city{font-size:24px;font-weight:700;margin-bottom:4px}.muted{color:#b8c9da;font-size:13px}
.item{background:#163657;border:1px solid #355574;border-radius:10px;padding:13px;margin:11px 0}
.itemtop{display:flex;justify-content:space-between;gap:6px;font-weight:700;font-size:14px}
.pill{font-size:11px;padding:4px 8px;border-radius:6px;white-space:nowrap}
.yes{background:#067e5c;color:#fff}.no{background:#3c516c;color:#e4eaf2}
a{color:#9bd4ff;word-break:break-all;font-size:12px;display:block;margin-top:8px}
.notice{margin-top:16px;padding:12px;border-radius:9px;background:#18446f;font-size:13px;line-height:1.6}
.leaflet-container{font-family:inherit}.leaflet-tooltip{font-weight:700}
@media(max-width:1080px){.columns{grid-template-columns:210px 1fr}.detail{grid-column:1/-1}}
@media(max-width:680px){.columns{display:block}.panel{margin-bottom:14px}#map{height:480px}.shell{padding:12px}}
</style></head><body><main class="shell">
<h1>▧ Mapa de Sistemas — Grupo S&S</h1>
<p class="sub">Consulte por município a presença cadastrada de Portais do Contribuinte, Fluxus e Veículos.</p>
<div class="stats">
<div class="stat"><b id="total">—</b><small>Municípios no mapa</small></div>
<div class="stat"><b id="covered">—</b><small>Municípios com sistemas</small></div>
<div class="stat"><b id="portal">—</b><small>Portal do Contribuinte</small></div>
<div class="stat"><b id="fluxus">—</b><small>Fluxus</small></div>
<div class="stat"><b id="veiculos">—</b><small>Veículos</small></div>
</div>
<div class="columns">
<aside class="panel filters"><h3>Filtros</h3>
<label><input type="radio" name="filter" value="todos" checked> Todos os sistemas</label>
<label><input type="radio" name="filter" value="Portal do Contribuinte"> Portal do Contribuinte</label>
<label><input type="radio" name="filter" value="Fluxus"> Fluxus</label>
<label><input type="radio" name="filter" value="Veículos"> Veículos</label>
<input id="search" type="text" placeholder="Buscar município..." list="cities">
<datalist id="cities"></datalist>
<div class="legend"><h3>Legenda</h3>
<div><span class="swatch" style="background:#1679d4"></span>3 sistemas cadastrados</div>
<div><span class="swatch" style="background:#15ad79"></span>2 sistemas cadastrados</div>
<div><span class="swatch" style="background:#f5bf33"></span>1 sistema cadastrado</div>
<div><span class="swatch" style="background:#8995a8"></span>Sem cadastro identificado</div></div>
<p class="muted">Cores representam cadastro, não disponibilidade online.</p>
</aside>
<section class="mapwrap"><div id="map"></div></section>
<aside class="panel detail"><div id="details"><h3>Selecione um município</h3><p class="muted">Clique no mapa ou pesquise pelo nome para visualizar os sistemas e links cadastrados.</p></div></aside>
</div></main>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const DATA=__DATA__;
const normalize=s=>String(s||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]/g,"");
const esc=s=>String(s||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const types=["Portal do Contribuinte","Fluxus","Veículos"];
const colors=DATA.colors;
const map=L.map("map",{zoomControl:true,attributionControl:false}).setView([-5.0,-39.5],7);
let geo=null,selected=null,layer=null,activeFilter="todos";
const entries=new Map();
function proper(f) {const p=f.properties||{};return p.nome||p.name||p.NM_MUN||p.NM_MUNICIP||p.municipio||p.city||"";}
function code(f){const p=f.properties||{};return p.cd_geocmu||p.codigo_ibge||p.codarea||p.id||"";}
function findCity(url, cities) {
  try {
    const u=new URL(url),host=normalize(u.hostname.split(".")[0]);
    const path=normalize(u.pathname);
    const matches=cities.filter(c=>c.key.length>=4 && (host===c.key || host.includes(c.key) || path.includes(c.key)));
    matches.sort((a,b)=>b.key.length-a.key.length);
    return matches[0]?.key||null;
  } catch {return null;}
}
function initData(features){
  const cities=features.map(f=>({key:normalize(proper(f)),name:proper(f),code:code(f)})).filter(c=>c.key);
  cities.forEach(c=>entries.set(c.key,{...c,systems:{}}));
  DATA.links.forEach(x=>{
    let k=x.municipio?normalize(x.municipio):findCity(x.url,cities);
    if(!entries.has(k)||!types.includes(x.sistema)||!/^https?:\/\//.test(x.url))return;
    let el=entries.get(k);
    if(!el.systems[x.sistema])el.systems[x.sistema]=[];
    if(!el.systems[x.sistema].includes(x.url))el.systems[x.sistema].push(x.url);
  });
  document.getElementById("cities").innerHTML=cities.sort((a,b)=>a.name.localeCompare(b.name,"pt-BR")).map(c=>'<option value="'+esc(c.name)+'">').join("");
  const all=[...entries.values()];
  document.getElementById("total").textContent=all.length;
  document.getElementById("covered").textContent=all.filter(c=>Object.keys(c.systems).length).length;
  [["portal",types[0]],["fluxus",types[1]],["veiculos",types[2]]].forEach(([id,t])=>
    document.getElementById(id).textContent=all.filter(c=>c.systems[t]?.length).length);
}
function count(c){
  if(!c)return 0;
  return activeFilter==="todos"?types.filter(t=>c.systems[t]?.length).length:Number(!!c.systems[activeFilter]?.length);
}
function style(f){
 const c=entries.get(normalize(proper(f)));
 const n=count(c);
 return {color:"#c5d8eb",weight:selected===normalize(proper(f))?3:0.8,fillColor:activeFilter==="todos"?colors[n]:(n?"#1679d4":"#8995a8"),fillOpacity:selected===normalize(proper(f))?1:.9};
}
function details(key){
 selected=key;
 const c=entries.get(key);
 if(!c)return;
 let html='<div class="city">'+esc(c.name)+' — CE</div><p class="muted">Código IBGE: '+esc(c.code||"não informado")+'</p><hr style="border:0;border-top:1px solid #355574;margin:16px 0"><h3>Sistemas do Grupo S&S no município</h3>';
 types.forEach(t=>{
   const urls=c.systems[t]||[];
   html+='<div class="item"><div class="itemtop"><span>'+esc(t)+'</span><span class="pill '+(urls.length?'yes':'no')+'">'+(urls.length?'Cadastrado':'Não identificado')+'</span></div>';
   urls.forEach(url=>html+='<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+esc(url)+' ↗</a>');
   html+='</div>';
 });
 html+='<div class="notice">'+Object.keys(c.systems).length+' sistema(s) identificado(s) para '+esc(c.name)+'. Dados provenientes dos cadastros ou dos links localizados no Monitor; presença não significa que o site esteja online.</div>';
 document.getElementById("details").innerHTML=html;
 layer?.setStyle(style);
}
function selectFeature(f){
 const k=normalize(proper(f));details(k);
 layer?.eachLayer(l=>{if(normalize(proper(l.feature))===k)map.fitBounds(l.getBounds(),{maxZoom:9,padding:[30,30]});});
}
async function load(){
 let collection=null;
 for(const url of DATA.geo_urls){try{const r=await fetch(url);if(!r.ok)throw Error(r.status);const g=await r.json();if(g.features?.length){collection=g;break}}catch(e){console.warn("GeoJSON",e)}}
 if(!collection){document.getElementById("map").innerHTML='<p style="padding:30px">Não foi possível carregar a malha municipal. Verifique a conexão com a internet.</p>';return}
 initData(collection.features);
 layer=L.geoJSON(collection,{style,onEachFeature:(f,l)=>{
  l.bindTooltip(proper(f));
  l.on("click",()=>selectFeature(f));
  l.on("mouseover",()=>l.setStyle({weight:2,fillOpacity:1}));
  l.on("mouseout",()=>layer.setStyle(style));
 }}).addTo(map);
 map.fitBounds(layer.getBounds(),{padding:[8,8]});
 document.querySelectorAll('input[name="filter"]').forEach(el=>el.addEventListener("change",e=>{activeFilter=e.target.value;layer.setStyle(style)}));
 document.getElementById("search").addEventListener("change",e=>{
  const found=[...entries.values()].find(c=>normalize(c.name)===normalize(e.target.value));
  if(found){details(found.key);layer.eachLayer(l=>{if(normalize(proper(l.feature))===found.key)map.fitBounds(l.getBounds(),{maxZoom:9,padding:[30,30]})});}
 });
 const caucaia=entries.get("caucaia");
 if(caucaia)details("caucaia");
}
load();
</script></body></html>
"""
components.html(HTML.replace("__DATA__", payload), height=900, scrolling=True)
