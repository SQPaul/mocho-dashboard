import {createTerrainMap,bindMapControls,showPopup,reduced} from './map-common.js';
const el = s => document.querySelector(s);
const svgNS = 'http://www.w3.org/2000/svg';
const fmt = n => n.toLocaleString('es-CL', {minimumFractionDigits:2, maximumFractionDigits:3});
const svg = (tag, attrs, content='') => { const n=document.createElementNS(svgNS,tag); Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v)); n.textContent=content; return n; };
let variationData,mapData,variationMap,chapterLoading;
const selectedContours=new Set([1976,2026]);
const palette=['#f1d471','#dfabed','#63d9f5','#eab58a','#dfef78','#87b7fc','#f6a1bd','#89e5c0','#d5b46b','#c995ff','#ff935e','#ffffff'];
function setupContourMap() {
  const controls=el('#contour-controls'),select=el('#contour-select'),message=el('#variation-map-message');
  const notice=text=>{message.textContent=text;message.classList.remove('hidden');message.classList.add('notice');};
  variationMap=createTerrainMap('variation-map',variationData,'./data/satellite-2026.webp');
  window.mochoVariationMap=variationMap;
  const nav=bindMapControls(variationMap,el('.variation-map-panel'),'variation-',notice,()=>notice('No fue posible cargar la imagen de 2026. Recarga la página para reintentar.'));
  const coverage=mapData.missingYears.length?` Sin geometría localizada: ${mapData.missingYears.join(', ')}.`:' Cobertura completa de la serie publicada.';
  el('#contour-note').textContent=`${mapData.availableYears.length} delimitaciones verificadas.${coverage}`;
  const years=[...mapData.availableYears,...mapData.missingYears].sort((a,b)=>a-b);
  years.forEach(year=>{
    const label=document.createElement('label'),input=document.createElement('input'),swatch=document.createElement('i');
    input.type='checkbox';input.dataset.year=year;input.checked=selectedContours.has(year);input.disabled=!mapData.availableYears.includes(year);input.setAttribute('aria-label',`Mostrar contorno ${year}`);
    swatch.style.background=palette[mapData.availableYears.indexOf(year)]||'#b7c0b1';label.append(input,swatch,document.createTextNode(String(year)));
    if(input.disabled)label.title='Geometría no localizada';
    input.onchange=()=>{input.checked?selectedContours.add(year):selectedContours.delete(year);syncContours();};controls.append(label);
    if(!input.disabled)select.add(new Option(String(year),year));
  });
  for(const [name,action] of [['Mostrar todos',()=>mapData.availableYears.forEach(y=>selectedContours.add(y))],['Restablecer comparación',()=>{selectedContours.clear();selectedContours.add(1976);selectedContours.add(2026);}]]){
    const button=document.createElement('button');button.textContent=name;button.onclick=()=>{action();syncContours();};controls.append(button);
  }
  select.onchange=()=>{if(select.value)inspectContour(+select.value);};
  variationMap.on('load',()=>{
    variationMap.addSource('icecap-history',{type:'geojson',data:mapData});
    mapData.availableYears.forEach((year,i)=>variationMap.addLayer({id:`contour-${year}`,type:'line',source:'icecap-history',filter:['==',['get','year'],year],paint:{'line-color':palette[i],'line-width':year===2026?2.8:1.8,'line-opacity':.95}}));
    syncContours();if(!nav.terrainFailed&&!message.classList.contains('notice'))message.classList.add('hidden');
    const hits=p=>variationMap.queryRenderedFeatures([[p.x-5,p.y-5],[p.x+5,p.y+5]],{layers:mapData.availableYears.map(y=>`contour-${y}`)});
    variationMap.on('mousemove',e=>{variationMap.getCanvas().style.cursor=hits(e.point).length?'pointer':'';});
    variationMap.on('click',e=>{const found=[...new Set(hits(e.point).map(f=>f.properties.year))];if(found.length){inspectContour(found[0],e.lngLat);if(found.length>1)el('#contour-detail').textContent+=` Contornos cercanos: ${found.join(', ')}. Usa «Consultar año» para elegir.`;}});
    window.mochoVariationReady=true;
  });
}
function syncContours(){
  for(const input of el('#contour-controls').querySelectorAll('input[data-year]')){
    const year=+input.dataset.year;input.checked=selectedContours.has(year);
    if(variationMap?.getLayer(`contour-${year}`))variationMap.setLayoutProperty(`contour-${year}`,'visibility',input.checked?'visible':'none');
  }
}
function inspectContour(year,coordinates){
  const f=mapData.features.find(f=>f.properties.year===year);if(!f)return;
  selectedContours.add(year);syncContours();el('#contour-select').value=year;
  const p=f.properties,description=p.area===null?'Sin superficie publicada para este año en la Figura 4.':`Superficie publicada: ${fmt(p.area)} ± ${fmt(p.error)} km². Figura 4 · Anexo 2.`;
  el('#contour-detail').textContent=`${year} · ${description} Archivo: ${p.source.split('/').at(-1)} · ${p.sourceCrs}.`;
  if(coordinates)showPopup(variationMap,{name:`Capa de hielo · ${year}`,category:'Delimitación histórica',description,source:`Archivo: ${p.source.split('/').at(-1)} · ${p.sourceCrs}`},coordinates);
}
function setupVariationChart() {
  const chart=el('#variation-chart'),start=el('#variation-start'),end=el('#variation-end'),errors=el('#variation-errors');
  const series=[variationData.glacier,variationData.icecap],names=['Glaciar Mocho','Capa de hielo Mocho–Choshuenco'];
  const years=[...new Set(series.flat().map(r=>r.year))].sort((a,b)=>a-b);
  for(const y of years){start.add(new Option(y,y));end.add(new Option(y,y));}
  start.value=years[0];end.value=years.at(-1);
  const link=document.createElement('button');link.id='chart-show-contour';link.textContent='Ver contorno en el mapa';link.hidden=true;el('.variation-readout').append(link);
  function inspect(r,i){
    el('#variation-readout-title').textContent=`${r.year} · ${names[i]}`;
    el('#variation-readout-body').textContent=`${fmt(r.area)} ± ${fmt(r.error)} km² · tasa ${r.rate===null?'no indicada':`${fmt(r.rate)} km²/año respecto a la observación anterior`}`;
    link.hidden=i!==1;link.disabled=!mapData?.availableYears.includes(r.year);
    link.onclick=()=>{inspectContour(r.year);el('.variation-map-card').scrollIntoView({behavior:reduced?'auto':'smooth'});};
  }
  function render(){
    const lo=+start.value,hi=+end.value,rows=series.map(s=>s.filter(r=>r.year>=lo&&r.year<=hi));
    const w=1000,left=65,right=960;chart.setAttribute('viewBox',`0 0 ${w} 650`);chart.replaceChildren();
    const x=y=>lo===hi?(left+right)/2:left+(y-lo)/(hi-lo)*(right-left);
    rows.forEach((s,i)=>{
      const top=i*320+45,bottom=top+215,min=i?10:4.5,max=i?33:7,Y=v=>bottom-(v-min)/(max-min)*(bottom-top);
      chart.append(svg('text',{x:left,y:top-20,class:'variation-panel-title'},`${i?'b':'a'}) ${names[i]} · km²`));
      for(let tick=0;tick<=4;tick++){const t=min+(max-min)*tick/4;chart.append(svg('line',{x1:left,x2:right,y1:Y(t),y2:Y(t),class:'variation-grid'}));chart.append(svg('text',{x:left-10,y:Y(t)+4,'text-anchor':'end',class:'variation-tick'},fmt(t)));}
      const ticks=lo===hi?[lo]:[lo,...Array.from({length:Math.floor((hi-lo)/10)+1},(_,j)=>Math.ceil((lo+1)/10)*10+j*10).filter(y=>y<hi),hi];
      for(const year of ticks)chart.append(svg('text',{x:x(year),y:bottom+22,'text-anchor':'middle',class:'variation-tick'},year));
      if(!s.length){chart.append(svg('text',{x:left+20,y:top+90,class:'variation-panel-title'},'Sin observaciones en este intervalo'));return;}
      if(errors.checked&&s.length>1){const upper=s.map(r=>`${x(r.year)},${Y(r.area+r.error)}`),lower=[...s].reverse().map(r=>`${x(r.year)},${Y(r.area-r.error)}`);chart.append(svg('path',{d:`M${upper.join(' L')} L${lower.join(' L')} Z`,class:`variation-band band-${i}`}));}
      chart.append(svg('path',{d:s.map((r,j)=>`${j?'L':'M'}${x(r.year)},${Y(r.area)}`).join(' '),class:`variation-line line-${i}`}));
      const marks=[];
      s.forEach((r,j)=>{
        const g=svg('g',{tabindex:0,role:'button','data-year':r.year,'data-series':r.series,'aria-label':`${names[i]}, ${r.year}: ${fmt(r.area)} km²`});
        g.append(svg('circle',{cx:x(r.year),cy:Y(r.area),r:11,class:'variation-hit'}));
        if(errors.checked)g.append(svg('path',{d:`M${x(r.year)} ${Y(r.area+r.error)}V${Y(r.area-r.error)}`,class:'variation-error'}));
        g.append(svg('circle',{cx:x(r.year),cy:Y(r.area),r:4,class:`variation-point point-${i}`}));
        g.onpointerenter=g.onclick=g.onfocus=()=>inspect(r,i);
        g.onkeydown=e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();marks[e.key==='Home'?0:e.key==='End'?marks.length-1:Math.max(0,Math.min(marks.length-1,j+(e.key==='ArrowRight'?1:-1)))].focus();}else if(e.key==='Enter'||e.key===' '){e.preventDefault();inspect(r,i);}};
        marks.push(g);chart.append(g);
      });
    });
    const table=document.createElement('table');table.innerHTML='<caption>Superficies del intervalo seleccionado</caption><thead><tr><th>Serie</th><th>Año</th><th>Área ± error (km²)</th><th>Tasa (km²/año)</th></tr></thead>';
    const body=document.createElement('tbody');rows.forEach((s,i)=>s.forEach(r=>{const tr=document.createElement('tr');for(const value of [names[i],r.year,`${fmt(r.area)} ± ${fmt(r.error)}`,r.rate===null?'No indicada':fmt(r.rate)]){const td=document.createElement('td');td.textContent=value;tr.append(td);}body.append(tr);}));table.append(body);el('#variation-table').replaceChildren(table);
    const last=rows[1].at(-1)||rows[0].at(-1);if(last)inspect(last,last.series==='icecap'?1:0);
  }
  start.onchange=()=>{if(+start.value>+end.value)end.value=start.value;render();};end.onchange=()=>{if(+end.value<+start.value)start.value=end.value;render();};errors.onchange=render;
  el('#variation-reset').onclick=()=>{start.value=years[0];end.value=years.at(-1);errors.checked=true;render();};
  render();
}
async function json(url){const r=await fetch(url);if(!r.ok)throw new Error(url);return r.json();}
function chapter(n,push=true){
  const two=n===2,page=el('#chapter-two'),first=el('.workspace');
  document.body.classList.toggle('chapter-two',two);page.hidden=!two;first.hidden=two;first.inert=two;page.inert=!two;
  el('#chapter-label').innerHTML=two?'<span>02</span> Variaciones de glaciares':'<span>01</span> Área de estudio';
  const nav=el('.chapter-nav');nav.textContent=two?'← Área de estudio':'Variaciones →';nav.dataset.goChapter=two?'1':'2';nav.href=two?'#capitulo-1':'#capitulo-2';
  document.title=two?'Mocho · Variaciones de glaciares':'Mocho · Atlas del glaciar';
  if(push&&location.hash!==`#capitulo-${n}`)history.pushState(null,'',`#capitulo-${n}`);
  if(two&&!chapterLoading){
    chapterLoading=Promise.allSettled([json('./data/glacier-variations.json'),json('./data/icecap-history.geojson')]).then(([seriesResult,geometryResult])=>{
      if(geometryResult.status==='fulfilled')mapData=geometryResult.value;
      if(seriesResult.status==='fulfilled'){variationData=seriesResult.value;setupVariationChart();}else el('.variation-scroll').textContent='La serie no pudo cargarse. Recarga la página para reintentar.';
      if(seriesResult.status==='fulfilled'&&geometryResult.status==='fulfilled'){try{setupContourMap();}catch{el('#variation-map-message').textContent='No fue posible iniciar el mapa 3D. Recarga la página para reintentar.';}}
      else el('#variation-map-message').textContent='No fue posible cargar los datos del mapa. Recarga la página para reintentar.';
    });
  }
  const target=two?page:first,title=target.querySelector(two?'h1':'h1');title.tabIndex=-1;title.focus({preventScroll:true});
  if(push&&!reduced)target.animate([{transform:`translateX(${two?24:-24}px)`,opacity:.5},{transform:'translateX(0)',opacity:1}],{duration:220});
  window.scrollTo(0,0);requestAnimationFrame(()=>{(two?variationMap:window.mochoMap)?.resize();});
}
function syncChapter(){chapter(location.hash==='#capitulo-2'?2:1,false);}
window.addEventListener('hashchange',syncChapter);window.addEventListener('popstate',syncChapter);document.querySelectorAll('[data-go-chapter]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();chapter(+a.dataset.goChapter);}));syncChapter();
