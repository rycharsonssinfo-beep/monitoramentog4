(function ssMapInstall(){
  const urls=["https://cdn.jsdelivr.net/gh/henriquemalvar/br-geojson@main/dist/municipios/CE.geojson","https://raw.githubusercontent.com/henriquemalvar/br-geojson/main/dist/municipios/CE.geojson","https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-23-mun.json"];
  const norm=v=>String(v||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]/g,"");
  const name=f=>String((f.properties||{}).nome||(f.properties||{}).name||(f.properties||{}).NM_MUN||(f.properties||{}).NM_MUNICIP||"");
  const code=f=>String((f.properties||{}).cd_geocmu||(f.properties||{}).codigo_ibge||(f.properties||{}).id||"");
  const modes=["portais","fluxus","veiculos"];
  const labels={portais:"Portal do Contribuinte",fluxus:"Fluxus",veiculos:"Veículos"};
  const colors=["#8995a8","#f5bf33","#15ad79","#1679d4"];
  let geo=null;
  const css=String.raw`
  .ss-map-open{border:1px solid #a6c6df;background:#0e5b95;color:white;padding:9px 13px;border-radius:9px;font-size:12px;font-weight:800;cursor:pointer;white-space:nowrap}
  .ss-map-layer{position:absolute;z-index:32;inset:8px;overflow:auto;background:#081e37;border:1px solid #345d81;border-radius:14px;color:#e8f5ff;padding:17px;font-family:Arial,Segoe UI,sans-serif}
  .ss-map-head{display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap;border-bottom:1px solid #355a7d;padding-bottom:15px}
  .ss-map-head h2{color:white;margin:0;font-size:24px}.ss-map-head p{color:#aac5dc;font-size:13px;margin:7px 0}
  .ss-map-back{border:1px solid #6c92b3;background:#1d4468;color:white;padding:11px;border-radius:8px;cursor:pointer;font-weight:700}
  .ss-map-stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;margin:14px 0}
  .ss-map-stat{padding:11px;border-radius:10px;border:1px solid #325877;background:#143451}
  .ss-map-stat b{display:block;font-size:22px}.ss-map-stat span{font-size:11px;color:#b1cbdf}
  .ss-map-grid{display:grid;grid-template-columns:205px minmax(300px,1fr) 310px;gap:12px}
  .ss-map-panel{border:1px solid #345a7b;background:#112f4e;padding:14px;border-radius:11px;min-width:0}
  .ss-map-panel h3{font-size:16px;margin:0 0 14px;color:white}
  .ss-map-panel label{display:block;margin:12px 0;font-size:13px;cursor:pointer}.ss-map-panel input[type=radio]{accent-color:#1489db}
  .ss-map-panel input[type=search]{background:#09233d;color:white;border:1px solid #557997;padding:11px;width:100%;border-radius:8px;box-sizing:border-box}
  .ss-map-legend{display:flex;gap:8px;align-items:center;margin:12px 0;font-size:12px}.ss-map-swatch{width:18px;height:18px;border-radius:5px}
  .ss-map-svg{display:block;width:100%;height:580px;background:#0a2646;border-radius:10px}
  .ss-map-svg path{stroke:#d0deec;stroke-width:.7;vector-effect:non-scaling-stroke;cursor:pointer}
  .ss-map-svg path:hover,.ss-map-svg path.picked{stroke:white;stroke-width:2.4;fill-opacity:1}
  .ss-map-info{border:1px solid #40627e;background:#193c5c;margin:10px 0;padding:12px;border-radius:9px}
  .ss-map-info strong{font-size:13px}.ss-map-pill{float:right;background:#596e84;font-size:11px;padding:3px 6px;border-radius:5px}.ss-map-pill.yes{background:#067e5b}
  .ss-map-info a{display:block;color:#a9dcff;font-size:11px;margin-top:8px;word-break:break-all;text-decoration:underline}
  .ss-map-note{font-size:12px;color:#bbd0e2;line-height:1.5;margin:12px 0}.ss-map-city{font-size:24px;font-weight:800;margin-bottom:8px}
  @media(max-width:1150px){.ss-map-grid{grid-template-columns:180px minmax(280px,1fr)}.ss-map-detail{grid-column:1/-1}}
  @media(max-width:650px){.ss-map-grid{display:block}.ss-map-panel{margin-bottom:12px}.ss-map-stats{grid-template-columns:repeat(2,1fr)}.ss-map-svg{height:440px}}
  `;
  function statusCity(c){return modes.filter(k=>c.data[k].length).length}
  async function loadGeo(){
    if(geo)return geo;
    for(const url of urls){
      try{const r=await fetch(url);if(!r.ok)continue;const j=await r.json();if(j.features && j.features.length>=180){geo=j;return j}}catch(e){console.warn("Mapa: falha de fonte",e)}
    }
    throw Error("Não foi possível carregar a malha municipal do Ceará.");
  }
  async function loadSystemData(){
    await Promise.all(modes.map(async m=>{
      if(portalDatas[m]?.length)return;
      try{
        const select="id,municipio,uf,url,estado,ultima_verificacao"+(m==="veiculos"?",cidade,entidade,categoria":"");
        portalDatas[m]=await portalFetchTable(portalServices[m].current,select,"order=municipio.asc&limit=500");
      }catch(e){console.warn("Mapa: erro ao consultar "+m,e)}
    }));
  }
  function cityRows(features){
    const cities=features.map(f=>({f,name:name(f),key:norm(name(f)),code:code(f),data:{portais:[],fluxus:[],veiculos:[]}})).filter(c=>c.key);
    const lookup=new Map(cities.map(c=>[c.key,c]));
    const longest=[...cities].sort((a,b)=>b.key.length-a.key.length);
    for(const mode of modes)for(const r of portalDatas[mode]||[]){
      const uf=String(r.uf||"CE").toUpperCase();if(uf!=="CE"&&uf!=="CEARA")continue;
      const raw=String(mode==="veiculos"?(r.cidade||r.municipio||""):(r.municipio||""));
      const key=norm(raw);const city=lookup.get(key)||longest.find(c=>c.key.length>=5 && key.includes(c.key));
      if(!city)continue;
      const url=portalSafeUrl(r.url)||"";
      if(!city.data[mode].some(x=>x.url===url&&x.name===String(r.entidade||raw)))
        city.data[mode].push({name:String(r.entidade||raw),url,estado:portalState(r)});
    }
    return cities;
  }
  function polyPath(f,proj){
    const g=f.geometry||{},poly=g.type==="Polygon"?[g.coordinates]:g.type==="MultiPolygon"?g.coordinates:[];
    let out="";
    for(const rings of poly||[])for(const ring of rings){
      if(!ring?.length)continue;
      out+=ring.map((p,i)=>{const xy=proj(p);return (i?"L":"M")+xy[0].toFixed(1)+" "+xy[1].toFixed(1)}).join("")+"Z";
    }
    return out;
  }
  async function populate(layer){
    const area=layer.querySelector("[data-sm-geo]");
    try{
      await Promise.all([loadGeo(),loadSystemData()]);
      if(!layer.isConnected)return;
      const cities=cityRows(geo.features),keyMap=new Map(cities.map(c=>[c.key,c]));
      const count=c=>statusCity(c);
      layer.querySelector("[data-sm-total]").textContent=cities.length;
      layer.querySelector("[data-sm-covered]").textContent=cities.filter(c=>count(c)).length;
      modes.forEach(m=>layer.querySelector("[data-sm-"+m+"]").textContent=cities.filter(c=>c.data[m].length).length);
      layer.querySelector("[data-sm-cities]").innerHTML=cities.map(c=>'<option value="'+portalEscape(c.name)+'"></option>').join("");
      let bounds=[Infinity,Infinity,-Infinity,-Infinity];
      function traverse(coords){
        if(!Array.isArray(coords))return;
        if(typeof coords[0]==="number"){bounds[0]=Math.min(bounds[0],coords[0]);bounds[1]=Math.min(bounds[1],coords[1]);bounds[2]=Math.max(bounds[2],coords[0]);bounds[3]=Math.max(bounds[3],coords[1]);return}
        coords.forEach(traverse);
      }
      cities.forEach(c=>traverse(c.f.geometry?.coordinates));
      const width=bounds[2]-bounds[0],height=bounds[3]-bounds[1];
      if(!Number.isFinite(width)||width<=0||height<=0)throw Error("Malha municipal inválida.");
      const scale=Math.min(640/width,720/height),offX=(690-scale*width)/2,offY=(760-scale*height)/2;
      const project=p=>[offX+(p[0]-bounds[0])*scale,offY+(bounds[3]-p[1])*scale];
      const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
      svg.setAttribute("viewBox","0 0 690 760");svg.setAttribute("role","img");svg.setAttribute("aria-label","Municípios do Ceará");svg.classList.add("ss-map-svg");area.replaceWith(svg);
      const paths=new Map();let selected="",filter="todos";
      function update(){for(const c of cities){const p=paths.get(c.key);if(p){p.setAttribute("fill",filter==="todos"?colors[count(c)]:(c.data[filter].length?"#1679d4":"#8995a8"));p.classList.toggle("picked",selected===c.key)}}}
      function select(c){
        selected=c.key;update();
        const safe=portalEscape;
        let html='<div class="ss-map-city">'+safe(c.name)+' — CE</div><div class="ss-map-note">Código IBGE: '+safe(c.code||"não informado")+'</div><h3>Sistemas do Grupo S&S</h3>';
        for(const mode of modes){
          const rows=c.data[mode];
          html+='<div class="ss-map-info"><strong>'+labels[mode]+'</strong><span class="ss-map-pill '+(rows.length?"yes":"")+'">'+(rows.length?"Cadastrado":"Não identificado")+'</span>';
          for(const row of rows){
            html+='<div class="ss-map-note">'+safe(row.name)+(row.estado==="online"?" • Online":"")+'</div>';
            if(row.url)html+='<a target="_blank" rel="noopener noreferrer" href="'+safe(row.url)+'">'+safe(row.url)+'</a>';
          }
          html+='</div>';
        }
        html+='<p class="ss-map-note">'+count(c)+' tipo(s) de sistema cadastrado(s). Cadastro não confirma disponibilidade em tempo real.</p>';
        layer.querySelector("[data-sm-detail]").innerHTML=html;
      }
      for(const c of cities){
        const d=polyPath(c.f,project);if(!d)continue;
        const p=document.createElementNS("http://www.w3.org/2000/svg","path");
        p.setAttribute("d",d);p.setAttribute("fill",colors[count(c)]);p.setAttribute("fill-rule","evenodd");
        const title=document.createElementNS("http://www.w3.org/2000/svg","title");title.textContent=c.name;p.appendChild(title);
        p.onclick=()=>select(c);svg.appendChild(p);paths.set(c.key,p);
      }
      layer.querySelectorAll('[name="ss-map-filter"]').forEach(r=>r.onchange=()=>{filter=r.value;update()});
      layer.querySelector("[data-sm-search]").onchange=e=>{const c=keyMap.get(norm(e.target.value));if(c)select(c)};
      if(keyMap.has("caucaia"))select(keyMap.get("caucaia"));
    }catch(e){console.error(e);area.textContent="Erro ao carregar o mapa: "+String(e.message||e)}
  }
  window.ssMapOpen=function(host){
    if(!document.getElementById("ss-map-styles")){
      const style=document.createElement("style");style.id="ss-map-styles";style.textContent=css;document.head.appendChild(style);
    }
    const old=host.querySelector("[data-ss-map]");if(old){old.remove();return}
    const layer=document.createElement("section");layer.className="ss-map-layer";layer.setAttribute("data-ss-map","1");
    layer.innerHTML=`
    <div class="ss-map-head"><div><h2>▧ Mapa de Sistemas — Grupo S&S</h2><p>Consulte a presença dos sistemas por município, incluindo Caucaia.</p></div><button type="button" class="ss-map-back" data-sm-back>← Voltar ao monitor</button></div>
    <div class="ss-map-stats"><div class="ss-map-stat"><b data-sm-total>—</b><span>Municípios CE</span></div><div class="ss-map-stat"><b data-sm-covered>—</b><span>Municípios atendidos</span></div><div class="ss-map-stat"><b data-sm-portais>—</b><span>Portal do Contribuinte</span></div><div class="ss-map-stat"><b data-sm-fluxus>—</b><span>Fluxus</span></div><div class="ss-map-stat"><b data-sm-veiculos>—</b><span>Veículos</span></div></div>
    <div class="ss-map-grid"><aside class="ss-map-panel"><h3>Filtros</h3><label><input type="radio" name="ss-map-filter" value="todos" checked> Todos os sistemas</label><label><input type="radio" name="ss-map-filter" value="portais"> Portal do Contribuinte</label><label><input type="radio" name="ss-map-filter" value="fluxus"> Fluxus</label><label><input type="radio" name="ss-map-filter" value="veiculos"> Veículos</label><input type="search" data-sm-search list="ss-map-city-options" placeholder="Buscar município..."><datalist id="ss-map-city-options" data-sm-cities></datalist><h3 style="margin-top:24px">Legenda</h3><div class="ss-map-legend"><span class="ss-map-swatch" style="background:#1679d4"></span>3 sistemas</div><div class="ss-map-legend"><span class="ss-map-swatch" style="background:#15ad79"></span>2 sistemas</div><div class="ss-map-legend"><span class="ss-map-swatch" style="background:#f5bf33"></span>1 sistema</div><div class="ss-map-legend"><span class="ss-map-swatch" style="background:#8995a8"></span>Sem registro</div><p class="ss-map-note">As cores representam cadastro, não disponibilidade online.</p></aside><div class="ss-map-panel"><h3>Municípios do Ceará</h3><div data-sm-geo class="ss-map-note">Carregando mapa e sistemas cadastrados...</div></div><aside class="ss-map-panel ss-map-detail" data-sm-detail><h3>Selecione um município</h3></aside></div>`;
    host.appendChild(layer);layer.querySelector("[data-sm-back]").onclick=()=>layer.remove();populate(layer);
  };
})();