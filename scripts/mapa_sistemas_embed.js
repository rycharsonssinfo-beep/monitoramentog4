(function ssMapInstall(){
  const urls=["https://cdn.jsdelivr.net/gh/henriquemalvar/br-geojson@main/dist/municipios/CE.geojson","https://raw.githubusercontent.com/henriquemalvar/br-geojson/main/dist/municipios/CE.geojson","https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-23-mun.json"];
  const norm=v=>String(v||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]/g,"");
  const name=f=>String((f.properties||{}).nome||(f.properties||{}).name||(f.properties||{}).NM_MUN||(f.properties||{}).NM_MUNICIP||"");
  const code=f=>String((f.properties||{}).cd_geocmu||(f.properties||{}).codigo_ibge||(f.properties||{}).id||"");
  const modes=["portais","fluxus","veiculos"];
  const labels={portais:"Portal do Contribuinte",fluxus:"Fluxus",veiculos:"Veículos"};
  const colors=["#8995a8","#f5bf33","#15ad79","#1679d4"];
  let geo=null, lastDataFetch=0, lastLoadErrors=[];
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

/* S&S MAPA PREMIUM v2 — acabamento visual sem alterar os dados ou regras */
.ss-map-layer{inset:5px;padding:22px 24px 24px;background:radial-gradient(ellipse at 45% -22%,rgba(21,110,185,.23),transparent 60%),linear-gradient(140deg,#06172d 0%,#071d36 48%,#06162d 100%);border:1px solid #2a5278;border-radius:18px;box-shadow:0 28px 80px rgba(0,9,25,.48);color:#eef7ff}
.ss-map-head{padding:2px 0 20px;border-bottom:1px solid rgba(134,185,229,.15)}
/* O cabeçalho já utiliza um SVG real: sem pseudoelementos nos contêineres de ações. */
.ss-map-head>div.ss-map-head-title{display:flex;align-items:center;gap:14px;padding-left:0;position:relative;min-width:0}
.ss-map-head>div.ss-map-head-title:before,.ss-map-head>div.ss-map-head-title:after{content:none;display:none}
.ss-map-head-icon{display:grid;place-items:center;flex:0 0 49px;width:49px;height:49px;border-radius:13px;color:#8bd9ff;background:linear-gradient(145deg,#123f69,#095b96);border:1px solid rgba(141,211,255,.46);box-shadow:inset 0 1px rgba(255,255,255,.16),0 10px 24px rgba(0,15,38,.32)}
.ss-map-head-icon svg{display:block;filter:drop-shadow(0 2px 5px rgba(0,24,56,.36))}
.ss-map-head .ss-map-head-title h2{margin:0;font-size:clamp(23px,2.05vw,30px);line-height:1.15;font-weight:850;letter-spacing:-.6px}
@media(max-width:670px){.ss-map-head>div.ss-map-head-title{padding-left:0}.ss-map-head-icon{width:44px;height:44px;flex-basis:44px}.ss-map-head-icon svg{width:27px;height:27px}}
.ss-map-head h2{font-weight:850;font-size:clamp(21px,2.05vw,29px);letter-spacing:-.65px;text-shadow:0 2px 16px #00172d80}
.ss-map-head p{font-size:13px;color:#b9d0e6;margin:7px 0 0;letter-spacing:.05px}
.ss-map-back{background:linear-gradient(140deg,#163e63,#0d304f);border:1px solid #44759f;border-radius:10px;padding:11px 15px;transition:.18s ease;box-shadow:inset 0 1px rgba(255,255,255,.12)}
.ss-map-back:hover{transform:translateY(-1px);border-color:#7bc1ee;background:#184e7b}
.ss-map-stats{gap:12px;margin:19px 0 20px;grid-template-columns:repeat(5,minmax(0,1fr))}
.ss-map-stat{position:relative;overflow:hidden;border:1px solid rgba(132,181,225,.22);background:linear-gradient(128deg,rgba(25,57,91,.92),rgba(16,41,72,.93));border-radius:13px;min-height:77px;padding:15px 11px 13px 62px;box-shadow:0 9px 22px #000f2733,inset 0 1px rgba(255,255,255,.045);display:flex;flex-direction:column;justify-content:center}
.ss-map-stat:before{content:"◈";position:absolute;top:15px;left:13px;display:grid;place-items:center;width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,#0c508f,#0d315d);color:#45b5ff;font-weight:900;font-size:22px}
.ss-map-stat:nth-child(2):before{content:"✓";background:linear-gradient(135deg,#0e6555,#0c3e43);color:#51dfae}
.ss-map-stat:nth-child(3):before{content:"▣";background:linear-gradient(135deg,#075b62,#113d50);color:#4de0bc}
.ss-map-stat:nth-child(4):before{content:"⌘";background:linear-gradient(135deg,#453984,#222f62);color:#b9a3ff}
.ss-map-stat:nth-child(5):before{content:"◆";background:linear-gradient(135deg,#86501e,#5f3c23);color:#ffba5b}
.ss-map-stat b{font-size:clamp(21px,2vw,28px);line-height:1.06;letter-spacing:-.6px;font-variant-numeric:tabular-nums;color:#fff}
.ss-map-stat span{margin-top:6px;font-size:11px;color:#c5d6e7;font-weight:600}
.ss-map-grid{grid-template-columns:minmax(187px,225px) minmax(340px,1fr) minmax(285px,365px);gap:15px;align-items:stretch}
.ss-map-panel{background:linear-gradient(145deg,rgba(20,48,79,.97),rgba(11,33,59,.98));border:1px solid rgba(111,162,209,.26);border-radius:14px;padding:18px;box-shadow:inset 0 1px rgba(255,255,255,.04),0 14px 28px #020e2226}
.ss-map-panel h3{font-size:15px;letter-spacing:-.15px;font-weight:850;color:#f7fbff;margin-bottom:17px}
.ss-map-panel label{padding:9px 9px;margin:2px -4px;min-height:36px;display:flex;align-items:center;gap:9px;border-radius:8px;font-size:12px;font-weight:650;color:#c9daeb;transition:background .15s ease}
.ss-map-panel label:hover{background:#234765;color:white}
.ss-map-panel input[type=radio]{accent-color:#2692ec;width:16px;height:16px;margin:0}
.ss-map-panel label:has(input:checked){background:rgba(25,104,166,.24);color:#fff}
.ss-map-panel input[type=search]{margin-top:13px;padding:12px 13px 12px 37px;border:1px solid rgba(110,163,207,.42);background:#0b2440;color:#fff;border-radius:10px;font-size:12px;outline:none;box-shadow:inset 0 1px 5px #000b1d33}
.ss-map-panel input[type=search]:focus{border-color:#62b8ef;box-shadow:0 0 0 3px #228ed229}
.ss-map-panel input[type=search]::placeholder{color:#8faec8}
.ss-map-grid>.ss-map-panel:first-child{position:relative}
.ss-map-grid>.ss-map-panel:first-child:before{content:"⌕";position:absolute;top:258px;left:31px;color:#7fc6fb;font-size:23px;pointer-events:none}
.ss-map-panel h3[style]{padding-top:11px;border-top:1px solid rgba(161,197,227,.14)}
.ss-map-legend{gap:11px;font-weight:600;color:#c8d8e8;margin:15px 0;font-size:12px}
.ss-map-swatch{width:23px;height:23px;border-radius:6px;border:1px solid #ffffff25;box-shadow:inset 0 1px rgba(255,255,255,.18)}
.ss-map-note{color:#b7cce0;font-size:12px;line-height:1.6}
.ss-map-grid>.ss-map-panel:nth-child(2){padding:14px;background:radial-gradient(ellipse at 50% 35%,#10375d55,transparent 75%),linear-gradient(145deg,#09203b,#081b32)}
.ss-map-grid>.ss-map-panel:nth-child(2)>h3{margin:2px 6px 10px;font-size:14px;color:#bcd8ed}
.ss-map-svg{height:min(67vh,660px);min-height:485px;background:radial-gradient(ellipse at 48% 40%,rgba(18,73,117,.2),transparent 70%),#081b32;border-radius:12px}
.ss-map-svg path{stroke:#c3dbed;stroke-width:.9;fill-opacity:.96;transition:fill-opacity .15s ease,filter .15s ease}
.ss-map-svg path:hover{stroke:#fff;stroke-width:2.1;filter:drop-shadow(0 0 4px #a2dbff)}
.ss-map-svg path.picked{stroke:#fff;stroke-width:2.9;filter:drop-shadow(0 0 7px rgba(106,197,255,.75))}
.ss-map-detail{padding:0;overflow:hidden;background:linear-gradient(145deg,#102d4e,#0c213c)}
.ss-map-detail>.ss-map-city{margin:0;padding:27px 19px 3px;background:radial-gradient(circle at 85% 15%,#2477aa77,transparent 47%),linear-gradient(120deg,#0c456f,#173e67);font-size:26px;letter-spacing:-.5px}
.ss-map-detail>.ss-map-city:before{content:"●";color:#62bcff;font-size:17px;margin-right:9px;vertical-align:3px}
.ss-map-detail>.ss-map-city+.ss-map-note{margin:0 0 17px;padding:4px 19px 20px;background:linear-gradient(120deg,#0c456f,#173e67);border-bottom:1px solid rgba(119,195,242,.24)}
.ss-map-detail>h3{padding:0 15px;font-size:15px;margin:15px 0}
.ss-map-detail>.ss-map-info{margin:10px 12px;padding:14px;border-radius:11px;background:linear-gradient(125deg,rgba(28,63,99,.95),rgba(18,49,80,.92));border:1px solid rgba(137,181,214,.23);box-shadow:inset 0 1px rgba(255,255,255,.055)}
.ss-map-info strong{font-size:13px;display:inline-block;max-width:63%;color:#f2f8ff}
.ss-map-info .ss-map-pill{border-radius:6px;padding:5px 9px;float:right;background:#526680;font-weight:750;color:#eef5fe;font-size:10px}
.ss-map-info .ss-map-pill.yes{background:#07865e;color:#e4fff2}
.ss-map-info .ss-map-note{margin:11px 0 3px;font-size:11px}
.ss-map-info a{display:block;margin:9px 0 0;padding:9px 10px 9px 29px;border:1px solid #426d93;border-radius:7px;background:rgba(18,75,117,.42);color:#b8e3ff;text-decoration:none;font-size:11px;overflow-wrap:anywhere;position:relative;transition:background .15s}
.ss-map-info a:before{content:"↗";position:absolute;left:9px;top:7px;font-size:15px}
.ss-map-info a:hover{background:#1b5c89;border-color:#66baf1;color:white}
.ss-map-detail>.ss-map-note:last-child{margin:17px 12px;padding:13px;border:1px solid #39668a;background:#1d456a;border-radius:10px;color:#cce6fb}
.ss-map-open{background:linear-gradient(135deg,#11598f,#073e74);border:1px solid #87bbdf;border-radius:9px;padding:9px 14px;box-shadow:0 3px 11px rgba(0,33,78,.24)}
.ss-map-open:hover{filter:brightness(1.12)}
@media(max-width:1180px){.ss-map-grid{grid-template-columns:195px minmax(285px,1fr)}.ss-map-detail{grid-column:1/-1}.ss-map-svg{height:550px}.ss-map-stats{grid-template-columns:repeat(3,1fr)}}
@media(max-width:670px){.ss-map-layer{padding:13px}.ss-map-grid{display:block}.ss-map-panel{margin:0 0 12px}.ss-map-stats{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.ss-map-stat{min-height:67px;padding-left:57px}.ss-map-head>div{padding-left:0}.ss-map-head>div:before,.ss-map-head>div:after{display:none}.ss-map-svg{height:480px;min-height:400px}.ss-map-grid>.ss-map-panel:first-child:before{display:none}}

  `;
  function statusCity(c){return modes.filter(k=>c.data[k].length).length}
  function ssMapReadLabel(value){
    return ({online:"Online na última consulta",offline:"Indisponível na última consulta",
      stale:"Leitura desatualizada",nao_verificado:"Sem leitura",
      suspeita_falha:"Falha em verificação",recuperando:"Recuperação em verificação",
      verificacao_bloqueada:"Verificação bloqueada"})[value]||"Estado não confirmado";
  }
  async function loadGeo(){
    if(geo)return geo;
    for(const url of urls){
      try{const r=await fetch(url);if(!r.ok)continue;const j=await r.json();if(j.features && j.features.length>=180){geo=j;return j}}catch(e){console.warn("Mapa: falha de fonte",e)}
    }
    throw Error("Não foi possível carregar a malha municipal do Ceará.");
  }
  async function loadSystemData(force=false){
    if(!force && lastDataFetch && Date.now()-lastDataFetch<30000)return [...lastLoadErrors];
    const errors=[];
    await Promise.all(modes.map(async m=>{
      try{
        const select="id,municipio,uf,url,estado,ultima_verificacao,inicio_falha,http_status,latencia_ms,detalhe,mudou_em"+(m==="veiculos"?",cidade,entidade,categoria":"");
        const fetched=await portalFetchTable(portalServices[m].current,select,"order=municipio.asc&limit=500");
        if(!Array.isArray(fetched))throw Error("Consulta retornou um formato inesperado.");
        portalDatas[m]=fetched;
      }catch(e){
        errors.push(m);
        console.warn("Mapa: falha na consulta de "+m,e);
        // Não descartar a última coleta válida; os status vencidos serão sinalizados.
      }
    }));
    lastDataFetch=Date.now();
    lastLoadErrors=errors;
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
        city.data[mode].push({id:String(r.id||""),municipio:String(r.municipio||""),name:String(r.entidade||raw),url,estado:portalState(r),ultima_verificacao:String(r.ultima_verificacao||"")});
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
      layer.dispatchEvent(new CustomEvent("ss-map-data-ready",{detail:{cities:cities.map(c=>({name:c.name,code:c.code,key:c.key,systems:c.data})),errors:[...lastLoadErrors]}}));
      const count=c=>statusCity(c);
      layer.querySelector("[data-sm-total]").textContent=cities.length;
      layer.querySelector("[data-sm-covered]").textContent=cities.filter(c=>count(c)).length;
      modes.forEach(m=>{
        layer.querySelector("[data-sm-"+m+"]").textContent=cities.filter(c=>c.data[m].length).length;
        const online=cities.filter(c=>c.data[m].some(row=>row.estado==="online")).length;
        const stat=layer.querySelector("[data-sm-online-"+m+"]");
        if(stat)stat.textContent=online+" municípios online na última leitura";
      });
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
      const scale=Math.min(666/width,740/height),offX=(690-scale*width)/2,offY=(760-scale*height)/2;
      const project=p=>[offX+(p[0]-bounds[0])*scale,offY+(bounds[3]-p[1])*scale];
      const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
      svg.setAttribute("viewBox","0 0 690 760");svg.setAttribute("role","img");svg.setAttribute("aria-label","Municípios do Ceará");svg.classList.add("ss-map-svg");area.replaceWith(svg);
      const paths=new Map();let selected="",activeModes=new Set();
      const matches=c=>!activeModes.size||[...activeModes].every(k=>c.data[k].length>0);
      function update(){
        let matched=0;
        for(const c of cities){
          const p=paths.get(c.key);
          if(!p)continue;
          const match=matches(c);
          if(match&&count(c))matched++;
          p.setAttribute("fill",match?colors[count(c)]:"#8995a8");
          p.dataset.ssFiltermatch=match?"1":"0";
          p.style.opacity=match?"1":"0.53";
          p.classList.toggle("picked",selected===c.key);
        }
        const status=layer.querySelector("[data-sm-filter-count]");
        if(status)status.textContent=activeModes.size?
          matched+" municípios com a combinação selecionada":
          cities.filter(c=>count(c)).length+" municípios atendidos";
        layer.dispatchEvent(new CustomEvent("ss-map-filter-change",{detail:{modes:[...activeModes]}}));
      }
      function select(c,focus=false){
        selected=c.key;update();
        const selectedFeedback=layer.querySelector("[data-sm-search-feedback]");
        if(selectedFeedback)selectedFeedback.textContent="Município selecionado: "+c.name;
        const safe=portalEscape;
        let html='<div class="ss-map-city">'+safe(c.name)+' — CE</div><div class="ss-map-note">Código IBGE: '+safe(c.code||"não informado")+'</div><h3>Sistemas cadastrados</h3>';
        for(const mode of modes){
          const rows=c.data[mode];
          const symbol=({portais:"◎",fluxus:"⌘",veiculos:"▣"})[mode];
          const online=rows.filter(r=>r.estado==="online").length;
          html+='<section class="ss-map-info ss-map-service ss-map-service-'+mode+'"><div class="ss-map-service-top">'+
            '<span class="ss-map-service-icon" aria-hidden="true">'+symbol+'</span><strong>'+labels[mode]+'</strong>'+
            '<span class="ss-map-pill '+(rows.length?"yes":"")+'">'+(rows.length?"Cadastrado":"Não identificado")+'</span></div>';
          if(!rows.length)html+='<p class="ss-map-empty-service">Nenhum ambiente cadastrado neste município.</p>';
          rows.forEach(row=>{
            const tone=row.estado==="online"?"online":row.estado==="offline"?"offline":"unknown";
            html+='<div class="ss-map-service-entry"><div class="ss-map-entry-name">'+safe(row.name)+'</div>'+
              '<span class="ss-map-read-status '+tone+'">'+safe(ssMapReadLabel(row.estado))+'</span>';
            if(row.url){
              let host="";
              try{host=new URL(row.url).hostname}catch(_){}
              html+='<a class="ss-map-service-link" target="_blank" rel="noopener noreferrer" href="'+safe(row.url)+'" title="'+safe(row.url)+'">'+
                '<span>↗ &nbsp; Acessar sistema</span><small>'+safe(host)+'</small></a>';
            }
            html+='</div>';
          });
          html+='</section>';
        }
        html+='<p class="ss-map-note">'+count(c)+' tipo(s) de sistema cadastrado(s). Cadastro não confirma disponibilidade em tempo real.</p>';
        layer.querySelector("[data-sm-detail]").innerHTML=html;
        layer.dispatchEvent(new CustomEvent("ss-map-city-selected",{detail:{key:c.key,name:c.name,focus}}));
      }
      for(const c of cities){
        const d=polyPath(c.f,project);if(!d)continue;
        const p=document.createElementNS("http://www.w3.org/2000/svg","path");
        p.setAttribute("d",d);p.setAttribute("fill",colors[count(c)]);p.setAttribute("fill-rule","evenodd");
        const title=document.createElementNS("http://www.w3.org/2000/svg","title");title.textContent=c.name;p.appendChild(title);
        p.onclick=()=>select(c,false);p.dataset.ssCity=c.key;svg.appendChild(p);paths.set(c.key,p);
      }
      const options=[...cities].sort((a,b)=>a.name.localeCompare(b.name,"pt-BR"));
      const input=layer.querySelector("[data-sm-search]");
      const feedback=layer.querySelector("[data-sm-search-feedback]");
      const findCity=value=>{
        const q=norm(value);
        if(!q)return null;
        return keyMap.get(q)||options.find(c=>c.key.startsWith(q))||options.find(c=>c.key.includes(q));
      };
      function runSearch(allowPartial=false){
        const raw=input.value.trim();
        if(!raw){feedback.textContent="Digite um município para localizar.";return}
        const key=norm(raw),exact=keyMap.get(key);
        const city=exact||(allowPartial?findCity(raw):null);
        if(city){
          select(city,true);
        }else if(allowPartial)feedback.textContent="Município não encontrado na malha do Ceará.";
      }
      input.addEventListener("input",()=>{
        if(keyMap.has(norm(input.value)))runSearch(false);
      });
      input.addEventListener("change",()=>runSearch(true));
      input.addEventListener("keydown",e=>{if(e.key==="Enter"){e.preventDefault();runSearch(true)}});
      const checks=[...layer.querySelectorAll("[data-sm-mode]")];
      function changeFilters(){
        activeModes=new Set(checks.filter(e=>e.checked).map(e=>e.dataset.smMode));
        const allBtn=layer.querySelector("[data-sm-all-filter]");
        if(allBtn)allBtn.classList.toggle("selected",activeModes.size===0);
        update();
      }
      checks.forEach(check=>check.addEventListener("change",changeFilters));
      layer.querySelector("[data-sm-all-filter]").onclick=()=>{
        checks.forEach(c=>c.checked=false);changeFilters();
      };
      update();
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
    <div class="ss-map-head"><div class="ss-map-head-title"><span class="ss-map-head-icon" aria-hidden="true"><svg viewBox="0 0 32 32" width="31" height="31" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 7.5 12 4l8 3.5L28.5 4v20.5L20 28l-8-3.5L3.5 28z"/><path d="M12 4v20.5M20 7.5V28"/></svg></span><h2>Mapa de Sistemas</h2></div><button type="button" class="ss-map-back" data-sm-back>← Voltar ao monitor</button></div>
    <div class="ss-map-stats"><div class="ss-map-stat"><b data-sm-total>—</b><span>Municípios CE</span></div><div class="ss-map-stat"><b data-sm-covered>—</b><span>Municípios atendidos</span></div><div class="ss-map-stat" title="Municípios com Portal do Contribuinte cadastrado"><b data-sm-portais>—</b><span>Portal do Contribuinte</span><small data-sm-online-portais>—</small></div><div class="ss-map-stat" title="Municípios com Fluxus cadastrado"><b data-sm-fluxus>—</b><span>Fluxus</span><small data-sm-online-fluxus>—</small></div><div class="ss-map-stat" title="Municípios com Veículos cadastrados; cada município pode ter vários ambientes"><b data-sm-veiculos>—</b><span>Veículos · municípios</span><small data-sm-online-veiculos>—</small></div></div>
    <div class="ss-map-grid"><aside class="ss-map-panel"><h3>Filtros</h3><button type="button" data-sm-all-filter class="ss-map-all-filter selected">Todos os sistemas</button><p class="ss-map-filter-hint">Selecione um ou mais sistemas. Os municípios destacados precisam ter todos os selecionados.</p><label class="ss-map-check"><input type="checkbox" data-sm-mode="portais"> Portal do Contribuinte</label><label class="ss-map-check"><input type="checkbox" data-sm-mode="fluxus"> Fluxus</label><label class="ss-map-check"><input type="checkbox" data-sm-mode="veiculos"> Veículos</label><div class="ss-map-search-box"><span aria-hidden="true">⌕</span><input type="search" data-sm-search list="ss-map-city-options" autocomplete="off" placeholder="Localizar município..."></div><datalist id="ss-map-city-options" data-sm-cities></datalist><div data-sm-search-feedback class="ss-map-search-feedback">Digite um município para localizar.</div><div class="ss-map-filter-summary" data-sm-filter-count>—</div><h3 style="margin-top:24px">Legenda</h3><div class="ss-map-legend"><span class="ss-map-swatch" style="background:#1679d4"></span>3 tipos de sistema</div><div class="ss-map-legend"><span class="ss-map-swatch" style="background:#15ad79"></span>2 tipos de sistema</div><div class="ss-map-legend"><span class="ss-map-swatch" style="background:#f5bf33"></span>1 tipo de sistema</div><div class="ss-map-legend"><span class="ss-map-swatch" style="background:#8995a8"></span>Sem sistema identificado</div><p class="ss-map-note">Cores: quantidade de sistemas cadastrados. Situação online: última consulta do monitor.</p></aside><div class="ss-map-panel"><h3>Municípios do Ceará</h3><div data-sm-geo class="ss-map-note">Carregando mapa e sistemas cadastrados...</div></div><aside class="ss-map-panel ss-map-detail" data-sm-detail><h3>Selecione um município</h3></aside></div>`;
    host.appendChild(layer);layer.querySelector("[data-sm-back]").onclick=()=>layer.remove();populate(layer);
  };
})();