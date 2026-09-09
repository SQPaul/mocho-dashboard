import {createTerrainMap,bindMapControls,showPopup,addStakeLayers} from './map-common.js';

const el = selector => document.querySelector(selector);
const number = value => Number(value).toLocaleString('es-CL', {minimumFractionDigits:2, maximumFractionDigits:2});
let velocityMap;
let velocityLoading;
let velocityData;
let stakePopup;

const json = async url => {
  const response = await fetch(url);
  if (!response.ok) throw new Error(url);
  return response.json();
};

function renderLegend(scale){
  el('#velocity-colorbar').style.background=`linear-gradient(90deg,${scale.stops.join(',')})`;
  const ticks=el('#velocity-scale-ticks');ticks.replaceChildren();
  scale.ticks.forEach(value=>{const span=document.createElement('span');span.textContent=value;ticks.append(span);});
}

function inspectStake(feature){
  const properties=feature.properties;
  if(stakePopup){const previous=stakePopup;stakePopup=null;previous.remove();}
  const current=showPopup(velocityMap,{
    name:`Baliza ${properties.name}`,
    category:`Velocidad anual · ${properties.period}`,
    description:`${number(properties.velocityMPerYear)} m/a`,
    source:'GNSS · DGA–UACh',
  },feature.geometry.coordinates);
  stakePopup=current;
  current.on('close',()=>{if(stakePopup===current)stakePopup=null;});
}

function setupMap(study,data){
  const message=el('#velocity-map-message');
  const notice=text=>{message.textContent=text;message.classList.remove('hidden');message.classList.add('notice');};
  velocityMap=createTerrainMap('velocity-map',study,'./data/satellite-2026.webp');
  window.mochoVelocityMap=velocityMap;
  const navigation=bindMapControls(velocityMap,el('.velocity-map-panel'),'velocity-',notice,()=>notice('No fue posible cargar la imagen de contexto. La velocidad y las balizas siguen disponibles.'));
  velocityMap.on('error',event=>{
    if(event.sourceId==='velocity-raster')notice('No fue posible cargar el raster de velocidad. Las balizas siguen disponibles.');
  });
  velocityMap.on('load',()=>{
    if(data){
      velocityMap.addSource('velocity-raster',{type:'image',url:`./data/${data.image.file}`,coordinates:data.image.imageCoordinates});
      velocityMap.addLayer({id:'velocity-raster',type:'raster',source:'velocity-raster',paint:{'raster-opacity':.82,'raster-fade-duration':0,'raster-resampling':'linear'}});
      addStakeLayers(velocityMap,data.stakes,{sourceId:'velocity-stakes',layerPrefix:'velocity-stake'});
      const stakeLayers=['velocity-stake-dot','velocity-stake-label'];
      velocityMap.on('click',event=>{
        const hit=velocityMap.queryRenderedFeatures(event.point,{layers:stakeLayers})[0];
        const feature=hit&&data.stakes.features.find(item=>item.properties.name===hit.properties.name);
        if(feature)inspectStake(feature);
      });
      velocityMap.on('mousemove',event=>{velocityMap.getCanvas().style.cursor=velocityMap.queryRenderedFeatures(event.point,{layers:stakeLayers}).length?'pointer':'';});
      window.mochoVelocityStakesReady=true;
      if(!navigation.terrainFailed&&!message.classList.contains('notice'))message.classList.add('hidden');
    }else notice('No fue posible cargar los datos de velocidad. Recarga la página para reintentar.');
    window.mochoVelocityReady=true;
  });
}

export function initVelocityChapter(){
  if(velocityLoading)return velocityLoading;
  window.mochoVelocityReady=false;
  window.mochoVelocityStakesReady=false;
  velocityLoading=Promise.allSettled([json('./data/study-area.json'),json('./data/velocity-2025-2026.json')]).then(([studyResult,dataResult])=>{
    if(dataResult.status==='fulfilled'){
      velocityData=dataResult.value;
      renderLegend(velocityData.colorScale);
      el('#velocity-selection').textContent=`${velocityData.period.label} · Selecciona una baliza para consultar su velocidad.`;
    }
    if(studyResult.status==='fulfilled'){
      try{setupMap(studyResult.value,dataResult.status==='fulfilled'?velocityData:null);}catch{el('#velocity-map-message').textContent='No fue posible iniciar el mapa 3D. Recarga la página para reintentar.';}
    }else el('#velocity-map-message').textContent='No fue posible cargar el mapa base. Recarga la página para reintentar.';
  });
  return velocityLoading;
}

export function getVelocityMap(){return velocityMap;}
