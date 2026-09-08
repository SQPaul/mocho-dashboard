const el = s => document.querySelector(s);
const svgNS = 'http://www.w3.org/2000/svg';
const fmt = n => n.toLocaleString('es-CL', {minimumFractionDigits:2, maximumFractionDigits:3});
const svg = (tag, attrs, content='') => { const n=document.createElementNS(svgNS,tag); Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v)); n.textContent=content; return n; };
let variationData, mapData;
function pathForGeometry(geometry, project) {
  const polys = geometry.type === 'GeometryCollection' ? geometry.geometries : [geometry];
  return polys.flatMap(g => g.coordinates).map(ring => ring.map((p,i) => `${i?'L':'M'}${project(p[0],p[1])}`).join(' ')+' Z').join(' ');
}
function setupContourMap() {
  const map = el('#variation-map'), controls = el('#contour-controls');
  const features = mapData.features;
  const allYears = [...new Set([...mapData.availableYears, ...mapData.missingYears])].sort((a,b)=>a-b);
  const bounds = features.flatMap(f => f.geometry.geometries.flatMap(g => g.coordinates.flat(2))).reduce((b,p)=>[Math.min(b[0],p[0]),Math.min(b[1],p[1]),Math.max(b[2],p[0]),Math.max(b[3],p[1])],[Infinity,Infinity,-Infinity,-Infinity]);
  const project = (lon,lat) => `${((lon-bounds[0])/(bounds[2]-bounds[0])*1000).toFixed(1)},${(1000-(lat-bounds[1])/(bounds[3]-bounds[1])*1000).toFixed(1)}`;
  const image = document.createElement('img'); image.src='./data/satellite-2026.webp'; image.alt=''; map.append(image);
  const chart = document.createElementNS(svgNS,'svg'); chart.setAttribute('viewBox','0 0 1000 1000'); chart.setAttribute('class','contour-svg'); map.append(chart);
  const selected = new Set([2025,2026]);
  function render() {
    chart.replaceChildren();
    features.forEach(f=>{ if(!selected.has(+f.properties.year)) return; const p=svg('path',{d:pathForGeometry(f.geometry,project),class:`contour contour-${f.properties.year}`,tabindex:0,'data-year':f.properties.year,'aria-label':`Contorno ${f.properties.year}`}); p.onclick=()=>{selected.clear();selected.add(+f.properties.year);render();}; chart.append(p); });
  }
  allYears.forEach(year=>{const label=document.createElement('label'); const input=document.createElement('input'); input.type='checkbox';input.checked=selected.has(year);input.disabled=!mapData.availableYears.includes(year); input.onchange=()=>{input.checked?selected.add(year):selected.delete(year);render();}; label.append(input,document.createTextNode(` ${year}`)); controls.append(label);});
  const all=document.createElement('button'); all.textContent='Todos disponibles'; all.onclick=()=>{mapData.availableYears.forEach(y=>selected.add(y));controls.querySelectorAll('input:not(:disabled)').forEach(i=>i.checked=true);render();}; controls.append(all); render();
}
function setupVariationChart() {
  const chart=el('#variation-chart'), start=el('#variation-start'), end=el('#variation-end'), errors=el('#variation-errors');
  const years=[...new Set([...variationData.glacier,...variationData.icecap].map(r=>r.year))].sort((a,b)=>a-b); years.forEach(y=>{start.add(new Option(y,y));end.add(new Option(y,y));}); start.value=years[0];end.value=years.at(-1);
  function render(){const lo=+start.value,hi=+end.value, rows=[variationData.glacier,variationData.icecap].map((series,si)=>series.filter(r=>r.year>=lo&&r.year<=hi)); const w=Math.max(760,(hi-lo+1)*18+100),h=470,left=58,right=w-20; chart.setAttribute('viewBox',`0 0 ${w} ${h}`);chart.style.minWidth=`${Math.min(w,920)}px`;chart.replaceChildren();
    rows.forEach((series,si)=>{const top=si?260:25,bottom=si?440:210,max=si?30:7,min=si?10:4.5,x=y=>left+(y-lo)/(hi-lo||1)*(right-left),Y=v=>bottom-(v-min)/(max-min)*(bottom-top); chart.append(svg('text',{x:left,y:top+14,class:'variation-panel-title'},si?'b) Capa de hielo Mocho–Choshuenco':'a) Glaciar Mocho')); [min,(min+max)/2,max].forEach(t=>{chart.append(svg('line',{x1:left,x2:right,y1:Y(t),y2:Y(t),class:'variation-grid'}));chart.append(svg('text',{x:left-9,y:Y(t)+4,'text-anchor':'end',class:'variation-tick'},fmt(t)));}); const line=series.map((r,i)=>`${i?'L':'M'}${x(r.year)},${Y(r.area)}`).join(' '); chart.append(svg('path',{d:line,class:`variation-line line-${si}`})); series.forEach(r=>{const g=svg('g',{tabindex:0,role:'button','data-year':r.year}); if(errors.checked){const y1=Y(r.area+r.error),y2=Y(r.area-r.error);g.append(svg('path',{d:`M${x(r.year)},${y1}V${y2}M${x(r.year)-3},${y1}H${x(r.year)+3}M${x(r.year)-3},${y2}H${x(r.year)+3}`,class:'variation-error'}));}g.append(svg('circle',{cx:x(r.year),cy:Y(r.area),r:4,class:`variation-point point-${si}`}));g.append(svg('text',{x:x(r.year),y:bottom+18,transform:`rotate(-55 ${x(r.year)} ${bottom+18})`,'text-anchor':'end',class:'variation-tick'},r.year)); const show=()=>{el('#variation-readout-title').textContent=`${r.year} · ${si?'Capa de hielo':'Glaciar Mocho'}`;el('#variation-readout-body').textContent=`${fmt(r.area)} ± ${fmt(r.error)} km² · tasa anual ${r.rate===null?'no indicada':`${fmt(r.rate)} km²/año`}`;};g.onmouseenter=show;g.onclick=show;g.onfocus=show;chart.append(g);}); }); }
  [start,end,errors].forEach(x=>x.onchange=render);el('#variation-reset').onclick=()=>{start.value=years[0];end.value=years.at(-1);errors.checked=true;render();};el('#variation-download').onclick=()=>{const csv='serie,año,area_km2,error_km2,tasa_km2_año\n'+[...variationData.glacier,...variationData.icecap].filter(r=>r.year>=+start.value&&r.year<=+end.value).map(r=>`${r.series},${r.year},${r.area},${r.error},${r.rate??''}`).join('\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download='mocho-variaciones.csv';a.click();};render();
}
function chapter(n, push=true) { const two=n===2; document.body.classList.toggle('chapter-two',two); const page=el('#chapter-two'); page.hidden=!two; el('#chapter-label').innerHTML=two?'<span>02</span> Variaciones de glaciares':'<span>01</span> Área de estudio'; document.title=two?'Mocho · Variaciones de glaciares':'Mocho · Atlas del glaciar'; if(push && location.hash!==`#capitulo-${n}`) history.pushState(null,'',`#capitulo-${n}`); if(two&&!page.dataset.ready){page.dataset.ready='1'; Promise.all([fetch('./data/glacier-variations.json').then(r=>r.json()),fetch('./data/icecap-history.geojson').then(r=>r.json())]).then(([a,b])=>{variationData=a;mapData=b;setupContourMap();setupVariationChart();});} if(two)el('#variation-title').focus({preventScroll:true}); }
function syncChapter(){chapter(location.hash==='#capitulo-2'?2:1,false);}
window.addEventListener('hashchange',syncChapter);window.addEventListener('popstate',syncChapter);document.querySelectorAll('[data-go-chapter]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();chapter(+a.dataset.goChapter);}));syncChapter();
