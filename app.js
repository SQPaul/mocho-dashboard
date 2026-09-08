import * as maplibregl from './vendor/maplibre-gl.mjs';
const $ = s => document.querySelector(s);
const message = $('#map-message');
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const camera = { center: [-72.028, -39.939], zoom: 12.5, pitch: 56, bearing: -23 };
let map, mode3D = true, terrainFailed = false;
const groups = { glacier: ['glacier-fill','glacier-line'], icecap: ['icecap-fill','icecap-line'], points: ['point-halo','point-dot'] };
const dialog = $('#sources-dialog');
$('#open-sources').onclick = () => dialog.showModal();
$('#close-sources').onclick = () => dialog.close();
dialog.addEventListener('click', e => { if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();} });
function notice(text){message.textContent=text;message.classList.add('notice');message.classList.remove('hidden');}
function fallback(error){console.error('No se pudo iniciar el mapa:',error);$('#fallback').classList.remove('hidden');message.classList.add('hidden');}
function setMode(is3D){
  mode3D=is3D&&!terrainFailed;
  map.setTerrain(mode3D?{source:'terrain',exaggeration:1}:null);
  map.easeTo({pitch:mode3D?camera.pitch:0,bearing:mode3D?camera.bearing:0,duration:reduced?0:800});
  for(const [selector,active] of [['#view-3d',mode3D],['#view-2d',!mode3D]]){$(selector).classList.toggle('active',active);$(selector).setAttribute('aria-pressed',String(active));}
  $('#view-label').textContent=mode3D?'Relieve 3D · escala vertical 1×':'Vista cartográfica 2D';
}
function popup(properties,coordinates){
  const root=document.createElement('div');
  for(const [tag,key] of [['span','category'],['h3','name'],['p','description'],['p','source']]){const el=document.createElement(tag);el.textContent=properties[key];if(tag==='span')el.className='popup-tag';root.append(el);}
  new maplibregl.Popup({maxWidth:'290px',offset:12}).setLngLat(coordinates).setDOMContent(root).addTo(map);
}
async function init(){
  const response=await fetch('./data/study-area.json');
  if(!response.ok)throw new Error('No se pudieron cargar los datos');
  const data=await response.json();
  map=new maplibregl.Map({
    container:'map',...camera,attributionControl:false,minZoom:10.5,maxZoom:15.5,maxPitch:70,maxBounds:data.navigationBounds,
    style:{version:8,sources:{
      terrain:{type:'raster-dem',tiles:['https://tiles.mapterhorn.com/{z}/{x}/{y}.webp'],tileSize:512,encoding:'terrarium',maxzoom:12,attribution:'<a href="https://mapterhorn.com/attribution/" target="_blank" rel="noopener">Relieve © Mapterhorn</a>'},
      satellite:{type:'image',url:'./data/satellite-2025.webp',coordinates:data.imageCoordinates}
    },layers:[
      {id:'background',type:'background',paint:{'background-color':'#233d3b'}},
      {id:'satellite',type:'raster',source:'satellite',paint:{'raster-fade-duration':0,'raster-saturation':-.18,'raster-contrast':.06}}
    ],terrain:{source:'terrain',exaggeration:1}}
  });
  map.addControl(new maplibregl.AttributionControl({compact:true,customAttribution:'Sentinel-2 / Copernicus · DGA–UACh'}),'bottom-right');
  map.addControl(new maplibregl.ScaleControl({unit:'metric',maxWidth:90}),'bottom-left');
  map.on('error',e=>{
    if(e.sourceId==='terrain'&&!terrainFailed){terrainFailed=true;setMode(false);$('#view-3d').disabled=true;notice('El relieve no está disponible. Puedes explorar el mapa en 2D.');}
    else if(e.sourceId==='satellite')fallback(e.error);
    else console.error('Error cartográfico:',e.error);
  });
  const timer=setTimeout(()=>notice('El mapa está tardando en cargar. Comprueba tu conexión.'),15000);
  map.on('load',()=>{
    clearTimeout(timer);if(!terrainFailed)message.classList.add('hidden');
    for(const name of ['glacier','icecap','points'])map.addSource(name,{type:'geojson',data:data[name]});
    map.addLayer({id:'icecap-fill',type:'fill',source:'icecap',paint:{'fill-color':'#eff0c6','fill-opacity':.05}});
    map.addLayer({id:'icecap-line',type:'line',source:'icecap',paint:{'line-color':'#f5efce','line-width':1.2,'line-opacity':.85,'line-dasharray':[3,3]}});
    map.addLayer({id:'glacier-fill',type:'fill',source:'glacier',paint:{'fill-color':'#72d5c6','fill-opacity':.17}});
    map.addLayer({id:'glacier-line',type:'line',source:'glacier',paint:{'line-color':'#adffdc','line-width':2.3}});
    map.addLayer({id:'point-halo',type:'circle',source:'points',paint:{'circle-radius':12,'circle-color':'#eebd7f','circle-opacity':.24}});
    map.addLayer({id:'point-dot',type:'circle',source:'points',paint:{'circle-radius':5,'circle-color':'#eac18e','circle-stroke-color':'#fff8e6','circle-stroke-width':1.6}});
    for(const input of document.querySelectorAll('[data-layer]')){const sync=()=>{for(const layer of groups[input.dataset.layer])map.setLayoutProperty(layer,'visibility',input.checked?'visible':'none');};sync();input.onchange=sync;}
    const hitLayers=['point-dot','point-halo','glacier-fill','icecap-fill'];
    map.on('click',e=>{const features=map.queryRenderedFeatures(e.point,{layers:hitLayers});if(!features.length)return;const f=features.find(f=>f.source==='points')||features.find(f=>f.source==='glacier')||features[0];popup(f.properties,f.geometry.type==='Point'?f.geometry.coordinates.slice(0,2):e.lngLat);});
    map.on('mousemove',e=>{map.getCanvas().style.cursor=map.queryRenderedFeatures(e.point,{layers:hitLayers}).length?'pointer':'';});
    setMode(mode3D);
    window.mochoReady=true;
  });
  $('#view-3d').onclick=()=>setMode(true);$('#view-2d').onclick=()=>setMode(false);
  $('#reset-view').onclick=()=>map.easeTo({...camera,pitch:mode3D?camera.pitch:0,bearing:mode3D?camera.bearing:0,duration:reduced?0:1000});
  $('#zoom-in').onclick=()=>map.zoomIn({duration:reduced?0:250});$('#zoom-out').onclick=()=>map.zoomOut({duration:reduced?0:250});
  $('#rotate-view').onclick=()=>map.easeTo({bearing:map.getBearing()+45,duration:reduced?0:500});
  $('#fullscreen').onclick=async()=>{const panel=$('.map-panel');if(document.fullscreenElement)await document.exitFullscreen();else if(panel.requestFullscreen){try{await panel.requestFullscreen();}catch{panel.classList.toggle('map-expanded');}}else panel.classList.toggle('map-expanded');map.resize();};
  document.addEventListener('fullscreenchange',()=>map.resize());
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){$('.map-panel').classList.remove('map-expanded');map.resize();}});
  new ResizeObserver(()=>map.resize()).observe($('.map-panel'));
  window.mochoMap=map;
}
init().catch(fallback);
