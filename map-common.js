import * as maplibregl from './vendor/maplibre-gl.mjs';
export const camera = {center:[-72.028,-39.939],zoom:12.5,pitch:56,bearing:-23};
export const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
export {maplibregl};
// One georeferenced image/terrain configuration for both chapters.
export function createTerrainMap(container,data,image){
  const map=new maplibregl.Map({container,...camera,attributionControl:false,minZoom:10.5,maxZoom:15.5,maxPitch:70,maxBounds:data.navigationBounds,
    style:{version:8,sources:{
      terrain:{type:'raster-dem',tiles:['https://tiles.mapterhorn.com/{z}/{x}/{y}.webp'],tileSize:512,encoding:'terrarium',maxzoom:12,attribution:'<a href="https://mapterhorn.com/attribution/" target="_blank" rel="noopener">Relieve © Mapterhorn</a>'},
      satellite:{type:'image',url:image,coordinates:data.imageCoordinates}
    },layers:[{id:'background',type:'background',paint:{'background-color':'#233d3b'}},
      {id:'satellite',type:'raster',source:'satellite',paint:{'raster-fade-duration':0,'raster-saturation':-.18,'raster-contrast':.06}}],terrain:{source:'terrain',exaggeration:1}}});
  map.addControl(new maplibregl.AttributionControl({compact:true,customAttribution:'Sentinel-2 / Copernicus · DGA–UACh'}),'bottom-right');
  map.addControl(new maplibregl.ScaleControl({unit:'metric',maxWidth:90}),'bottom-left');
  return map;
}
export function bindMapControls(map,panel,prefix,onNotice,onImageError){
  const get=key=>document.getElementById(prefix+key);
  let mode3D=true,terrainFailed=false;
  const setMode=value=>{
    mode3D=value&&!terrainFailed;map.setTerrain(mode3D?{source:'terrain',exaggeration:1}:null);
    map.easeTo({pitch:mode3D?camera.pitch:0,bearing:mode3D?camera.bearing:0,duration:reduced?0:600});
    for(const [key,active] of [['view-3d',mode3D],['view-2d',!mode3D]]){get(key).classList.toggle('active',active);get(key).setAttribute('aria-pressed',String(active));}
    get('view-label').textContent=mode3D?'Relieve 3D · escala vertical 1×':'Vista cartográfica 2D';
  };
  map.on('error',e=>{if(e.sourceId==='terrain'&&!terrainFailed){terrainFailed=true;setMode(false);get('view-3d').disabled=true;onNotice('El relieve no está disponible. Puedes explorar el mapa en 2D.');}else if(e.sourceId==='satellite')onImageError(e.error);});
  get('view-3d').onclick=()=>setMode(true);get('view-2d').onclick=()=>setMode(false);
  get('reset-view').onclick=()=>map.easeTo({...camera,pitch:mode3D?camera.pitch:0,bearing:mode3D?camera.bearing:0,duration:reduced?0:700});
  get('zoom-in').onclick=()=>map.zoomIn({duration:reduced?0:250});get('zoom-out').onclick=()=>map.zoomOut({duration:reduced?0:250});
  get('rotate-view').onclick=()=>map.easeTo({bearing:map.getBearing()+45,duration:reduced?0:500});
  get('fullscreen').onclick=async()=>{if(document.fullscreenElement)await document.exitFullscreen();else if(panel.requestFullscreen){try{await panel.requestFullscreen();}catch{panel.classList.toggle('map-expanded');}}else panel.classList.toggle('map-expanded');map.resize();};
  document.addEventListener('fullscreenchange',()=>map.resize());
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){panel.classList.remove('map-expanded');map.resize();}});
  new ResizeObserver(()=>{if(panel.clientWidth&&panel.clientHeight)map.resize();}).observe(panel);
  return {get terrainFailed(){return terrainFailed;}};
}
export function showPopup(map,properties,coordinates){
  const root=document.createElement('div');
  for(const [tag,key] of [['span','category'],['h3','name'],['p','description'],['p','source']]){if(!properties[key])continue;const node=document.createElement(tag);node.textContent=properties[key];if(tag==='span')node.className='popup-tag';root.append(node);}
  return new maplibregl.Popup({maxWidth:'310px',offset:12}).setLngLat(coordinates).setDOMContent(root).addTo(map);
}
