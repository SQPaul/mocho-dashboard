import {createTerrainMap,bindMapControls,showPopup} from './map-common.js';
const $=s=>document.querySelector(s),message=$('#map-message');
let map;
const groups={glacier:['glacier-fill','glacier-line'],icecap:['icecap-fill','icecap-line'],stations:['station-halo','station-dot'],summits:['summit-symbol']};
const dialog=$('#sources-dialog');
$('#open-sources').onclick=()=>dialog.showModal();$('#close-sources').onclick=()=>dialog.close();
dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
function notice(text){message.textContent=text;message.classList.add('notice');message.classList.remove('hidden');}
function fallback(error){console.error('No se pudo iniciar el mapa:',error);$('#fallback').classList.remove('hidden');message.classList.add('hidden');}
const popup=(p,c)=>showPopup(map,p,c);
const coordinatePopup=(feature,category)=>popup({name:feature.properties.name,category,
  description:`Latitud ${feature.properties.lat}° · Longitud ${feature.properties.lon}°`},feature.geometry.coordinates.slice(0,2));
async function addStakes(){
  const response=await fetch('./data/stakes.geojson');if(!response.ok)throw new Error('Balizas no disponibles');
  const data=await response.json();map.addSource('stakes',{type:'geojson',data});
  // Native points follow the same terrain as glacier boundaries: no DOM offsets.
  map.addLayer({id:'stake-dot',type:'circle',source:'stakes',paint:{'circle-radius':5,'circle-color':'#f0f3c3','circle-stroke-color':'#173b3c','circle-stroke-width':1.5}});
  for(const f of data.features){
    const canvas=document.createElement('canvas');canvas.width=100;canvas.height=44;
    const ctx=canvas.getContext('2d');ctx.font='bold 22px sans-serif';ctx.lineWidth=5;ctx.strokeStyle='#173b3c';ctx.fillStyle='#f8f8e4';
    ctx.strokeText(f.properties.name,6,30);ctx.fillText(f.properties.name,6,30);
    map.addImage(f.id,ctx.getImageData(0,0,100,44),{pixelRatio:2});
  }
  map.addLayer({id:'stake-label',type:'symbol',source:'stakes',layout:{'icon-image':['get','name'],'icon-anchor':'left','icon-offset':[8,-8],'icon-allow-overlap':false,'icon-ignore-placement':true}});
  const select=$('#stake-select');for(const f of data.features)select.add(new Option(f.properties.name,f.id));
  const inspect=f=>{const p=f.properties,c=f.geometry.coordinates;popup({name:`Baliza ${p.name}`,category:'Coordenadas WGS84',description:`Latitud ${c[1].toFixed(6)}° · Longitud ${c[0].toFixed(6)}°`},c);};
  select.onchange=()=>{const f=data.features.find(f=>f.id===select.value);if(f)inspect(f);};
  map.on('click',e=>{const hit=map.queryRenderedFeatures(e.point,{layers:['stake-dot','stake-label']})[0];const f=hit&&data.features.find(row=>row.properties.name===hit.properties.name);if(f)inspect(f);});
  const sync=()=>{const visible=$('#show-stakes').checked;for(const id of ['stake-dot','stake-label'])map.setLayoutProperty(id,'visibility',visible?'visible':'none');select.disabled=!visible;};
  $('#show-stakes').onchange=sync;sync();window.mochoStakesReady=true;
}
async function init(){
  const response=await fetch('./data/study-area.json');if(!response.ok)throw new Error('No se pudieron cargar los datos');
  const data=await response.json();map=createTerrainMap('map',data,'./data/satellite-2026.webp');
  const controls=bindMapControls(map,$('#map').parentElement,'',notice,fallback);
  const timer=setTimeout(()=>notice('El mapa está tardando en cargar. Comprueba tu conexión.'),15000);
  map.on('load',()=>{
    clearTimeout(timer);if(!controls.terrainFailed)message.classList.add('hidden');
    for(const name of ['glacier','icecap','stations','summits'])map.addSource(name,{type:'geojson',data:data[name]});
    map.addLayer({id:'icecap-fill',type:'fill',source:'icecap',paint:{'fill-color':'#eff0c6','fill-opacity':.05}});
    map.addLayer({id:'icecap-line',type:'line',source:'icecap',paint:{'line-color':'#f5efce','line-width':1.2,'line-opacity':.85,'line-dasharray':[3,3]}});
    map.addLayer({id:'glacier-fill',type:'fill',source:'glacier',paint:{'fill-color':'#72d5c6','fill-opacity':.17}});
    map.addLayer({id:'glacier-line',type:'line',source:'glacier',paint:{'line-color':'#adffdc','line-width':2.3}});
    map.addLayer({id:'station-halo',type:'circle',source:'stations',paint:{'circle-radius':12,'circle-color':'#397bb3','circle-opacity':.24}});
    map.addLayer({id:'station-dot',type:'circle',source:'stations',paint:{'circle-radius':5,'circle-color':'#397bb3','circle-stroke-color':'#fff','circle-stroke-width':1.6}});
    const summit=document.createElement('canvas');summit.width=36;summit.height=32;
    const summitContext=summit.getContext('2d');summitContext.beginPath();summitContext.moveTo(18,3);summitContext.lineTo(33,28);summitContext.lineTo(3,28);summitContext.closePath();
    summitContext.fillStyle='#f3c84b';summitContext.fill();summitContext.strokeStyle='#173b3c';summitContext.lineWidth=4;summitContext.lineJoin='round';summitContext.stroke();
    map.addImage('summit-triangle',summitContext.getImageData(0,0,36,32),{pixelRatio:2});
    map.addLayer({id:'summit-symbol',type:'symbol',source:'summits',layout:{'icon-image':'summit-triangle','icon-allow-overlap':true}});
    for(const input of document.querySelectorAll('[data-layer]')){const sync=()=>{for(const layer of groups[input.dataset.layer])map.setLayoutProperty(layer,'visibility',input.checked?'visible':'none');};sync();input.onchange=sync;}
    const hitLayers=()=>['stake-dot','stake-label','station-dot','station-halo','summit-symbol','glacier-fill','icecap-fill'].filter(id=>map.getLayer(id));
    map.on('click',e=>{const features=map.queryRenderedFeatures(e.point,{layers:hitLayers()});if(!features.length||features.some(f=>f.source==='stakes'))return;
      const f=features.find(f=>f.source==='stations')||features.find(f=>f.source==='summits')||features.find(f=>f.source==='glacier')||features[0];
      if(f.source==='stations')coordinatePopup(f);else if(f.source==='summits')coordinatePopup(f,'Cumbre');else popup(f.properties,e.lngLat);
    });
    map.on('mousemove',e=>{map.getCanvas().style.cursor=map.queryRenderedFeatures(e.point,{layers:hitLayers()}).length?'pointer':'';});
    addStakes().catch(()=>{$('#stakes-status').textContent='No fue posible cargar las balizas. Recarga la página para reintentar.';$('#show-stakes').disabled=true;});window.mochoReady=true;
  });window.mochoMap=map;
}
init().catch(fallback);
