/* Tooltip acessível de filas G4Flex: somente os dados recebidos no snapshot.
   Lê o title existente (g4fQueueTitle); nunca confunde fila inicial com filas logadas.
   Eventos delegados: continuam funcionando após re-render do painel. */
function g4fQueueTooltipInit(host){
 if(!host || host._g4fQueueTooltipReady)return;
 host._g4fQueueTooltipReady=true;
 const tip=document.createElement('aside');
 tip.className='g4f-queue-tooltip';
 tip.id='g4f-queue-popover-'+Math.random().toString(36).slice(2,9);
 tip.setAttribute('role','tooltip');
 tip.hidden=true;
 document.body.appendChild(tip);
 let current=null,hideTimer=null;
 const cancel=()=>{if(hideTimer){clearTimeout(hideTimer);hideTimer=null;}};
 function hide(){
   cancel();
   if(current){current.removeAttribute('aria-describedby');current=null;}
   tip.hidden=true;
 }
 function deferHide(){cancel();hideTimer=setTimeout(hide,180);}
 function textFrom(el){
   if(!el)return'';
   const t=el.getAttribute('data-g4f-queue-text')||el.getAttribute('title')||'';
   return t.startsWith('Filas em que está logado:')?t:'';
 }
 function getTrigger(target){
   const el=target?.closest?.('strong, img, .g4f-avatar');
   if(!el)return null;
   if(el.matches('strong')){
     return textFrom(el)?el:null;
   }
   const group=el.closest('.ss-list-name,.ss-agent,.g4f-agent,.g4f-card,.ss-card,.g4f-agent-card');
   if(!group)return null;
   const strong=[...group.querySelectorAll('strong')].find(x=>textFrom(x));
   return strong||null;
 }
 function place(el){
   const r=el.getBoundingClientRect();
   const w=tip.offsetWidth||305,h=tip.offsetHeight||180;
   const gap=10;
   let x=r.right+gap;
   if(x+w>window.innerWidth-12)x=r.left-w-gap;
   if(x<12)x=Math.min(Math.max(12,r.left),Math.max(12,window.innerWidth-w-12));
   const y=Math.max(12,Math.min(r.top-14,window.innerHeight-h-12));
   tip.style.left=Math.round(x)+'px';
   tip.style.top=Math.round(y)+'px';
 }
 function show(el){
   const value=textFrom(el);if(!value)return;
   cancel();
   if(current===el&&!tip.hidden){place(el);return;}
   if(current)current.removeAttribute('aria-describedby');
   current=el;
   if(el.hasAttribute('title')){
     el.setAttribute('data-g4f-queue-text',value);
     el.removeAttribute('title'); // substitui tooltip nativo do navegador
   }
   const queues=value.split(/\r?\n/).slice(1).map(s=>s.trim()).filter(Boolean).slice(0,60);
   if(!queues.length){hide();return;}
   tip.replaceChildren();
   const head=document.createElement('div');head.className='g4f-queue-tooltip-heading';
   const heading=document.createElement('strong');heading.textContent='Filas em que está logado';
   const number=document.createElement('span');number.className='g4f-queue-tooltip-count';number.textContent=queues.length+' filas';
   head.append(heading,number);
   const list=document.createElement('ul');list.className='g4f-queue-tooltip-list';
   for(const name of queues){
     const li=document.createElement('li');
     const dot=document.createElement('span');dot.className='g4f-queue-tooltip-dot';dot.setAttribute('aria-hidden','true');
     const t=document.createElement('span');t.textContent=name;
     li.append(dot,t);list.appendChild(li);
   }
   const foot=document.createElement('p');
   foot.className='g4f-queue-tooltip-foot';
   foot.textContent='Filas vinculadas ao atendente · não indica a fila da conversa atual.';
   tip.append(head,list,foot);tip.hidden=false;
   el.setAttribute('aria-describedby',tip.id);
   place(el);
 }
 host.addEventListener('mouseover',ev=>{
   const node=getTrigger(ev.target);
   if(node)show(node);else if(current && !tip.contains(ev.relatedTarget))deferHide();
 });
 host.addEventListener('mouseout',ev=>{
   if(current && !tip.contains(ev.relatedTarget))deferHide();
 });
 host.addEventListener('focusin',ev=>{const node=getTrigger(ev.target);if(node)show(node);});
 host.addEventListener('focusout',ev=>{if(current && !tip.contains(ev.relatedTarget))deferHide();});
 host.addEventListener('pointerdown',ev=>{
   const node=getTrigger(ev.target);
   if(ev.pointerType==='touch'&&node){show(node);}
 });
 tip.addEventListener('mouseenter',cancel);
 tip.addEventListener('mouseleave',deferHide);
 document.addEventListener('keydown',ev=>{if(ev.key==='Escape')hide();});
 document.addEventListener('pointerdown',ev=>{if(!tip.hidden&&!tip.contains(ev.target)&&!host.contains(ev.target))hide();});
 function enhance(){
   if(!host.isConnected){hide();return;}
   for(const name of host.querySelectorAll('strong[title^="Filas em que está logado:"],strong[data-g4f-queue-text]')){
     if(!name.hasAttribute('tabindex'))name.tabIndex=0;
   }
   if(current&&!current.isConnected)hide();
 }
 const observer=new MutationObserver(enhance);
 observer.observe(host,{subtree:true,childList:true});
 enhance();
}
