import {createTerrainMap,bindMapControls} from './map-common.js';

const el = selector => document.querySelector(selector);
let snowMap;
let snowLoading;
let snowData;
let activeYear;

const json = async url => {
  const response = await fetch(url);
  if (!response.ok) throw new Error(url);
  return response.json();
};

const number = (value, digits=2) => value.toLocaleString('es-CL', {minimumFractionDigits:digits, maximumFractionDigits:digits});

function renderTable(rows) {
  const body=el('#snow-table-body');
  body.replaceChildren();
  for(const row of rows){
    const tr=document.createElement('tr');
    const values=[row.label,row.n.toLocaleString('es-CL'),number(row.distanceKm),number(row.meanM),number(row.stdM),number(row.minM),number(row.maxM)];
    values.forEach((value,index)=>{const cell=document.createElement(index?'td':'th');cell.textContent=value;if(!index)cell.scope='row';tr.append(cell);});
    body.append(tr);
  }
  el('#snow-table-loading').hidden=true;
  el('#snow-table-wrap').hidden=false;
}

function renderScale(scale){
  el('#snow-colorbar').style.background=`linear-gradient(90deg,${scale.stops.join(',')})`;
  const ticks=el('#snow-scale-ticks');ticks.replaceChildren();
  scale.ticks.forEach(value=>{const span=document.createElement('span');span.textContent=value;ticks.append(span);});
}

function selectCampaign(year){
  activeYear=year;
  for(const input of document.querySelectorAll('#snow-campaign-controls input'))input.checked=+input.value===year;
  for(const campaign of snowData.campaigns){
    const layer=`gpr-${campaign.year}`;
    if(snowMap?.getLayer(layer))snowMap.setLayoutProperty(layer,'visibility',campaign.year===year?'visible':'none');
  }
  const selected=snowData.campaigns.find(campaign=>campaign.year===year);
  if(selected)el('#snow-selection').textContent=`Campaña seleccionada · ${selected.label}`;
}

function renderCampaigns(data){
  const controls=el('#snow-campaign-controls');controls.replaceChildren();
  data.campaigns.forEach(campaign=>{
    const label=document.createElement('label'),input=document.createElement('input');
    input.type='radio';input.name='snow-campaign';input.value=campaign.year;input.checked=campaign.year===data.defaultYear;
    input.setAttribute('aria-label',`Mostrar campaña GPR ${campaign.label}`);
    input.onchange=()=>selectCampaign(campaign.year);
    label.append(input,document.createTextNode(String(campaign.year)));controls.append(label);
  });
  selectCampaign(data.defaultYear);
}

function setupMap(study,data){
  const message=el('#snow-map-message');
  const notice=text=>{message.textContent=text;message.classList.remove('hidden');message.classList.add('notice');};
  snowMap=createTerrainMap('snow-map',study,'./data/satellite-2026.webp');
  window.mochoSnowMap=snowMap;
  const navigation=bindMapControls(snowMap,el('.snow-map-panel'),'snow-',notice,()=>notice('No fue posible cargar la imagen de 2026. Las campañas GPR siguen disponibles.'));
  snowMap.on('error',event=>{
    if(event.sourceId?.startsWith('gpr-')){
      const year=Number(event.sourceId.slice(4));
      const input=el(`#snow-campaign-controls input[value="${year}"]`);
      if(input)input.disabled=true;
      if(activeYear===year)notice(`No fue posible cargar la campaña GPR ${year}. Selecciona otro año.`);
    }
  });
  snowMap.on('load',()=>{
    data.campaigns.forEach(campaign=>{
      const id=`gpr-${campaign.year}`;
      snowMap.addSource(id,{type:'image',url:`./data/${campaign.image}`,coordinates:campaign.imageCoordinates});
      snowMap.addLayer({id,type:'raster',source:id,layout:{visibility:campaign.year===activeYear?'visible':'none'},paint:{'raster-opacity':.82,'raster-fade-duration':0,'raster-resampling':'linear'}});
    });
    selectCampaign(activeYear);
    if(!navigation.terrainFailed&&!message.classList.contains('notice'))message.classList.add('hidden');
    window.mochoSnowReady=true;
  });
}

export function initSnowChapter(){
  if(snowLoading)return snowLoading;
  window.mochoSnowReady=false;
  snowLoading=Promise.allSettled([json('./data/study-area.json'),json('./data/gpr-campaigns.json')]).then(([studyResult,dataResult])=>{
    if(dataResult.status==='fulfilled'){
      snowData=dataResult.value;renderCampaigns(snowData);renderScale(snowData.colorScale);renderTable(snowData.summary);
    }else{
      el('#snow-map-message').textContent='No fue posible cargar las campañas GPR. Recarga la página para reintentar.';
      el('#snow-table-loading').textContent='No fue posible cargar el resumen GPR.';
    }
    if(studyResult.status==='fulfilled'&&dataResult.status==='fulfilled'){
      try{setupMap(studyResult.value,snowData);}catch{el('#snow-map-message').textContent='No fue posible iniciar el mapa 3D. Recarga la página para reintentar.';}
    }else if(studyResult.status==='rejected')el('#snow-map-message').textContent='No fue posible cargar el mapa base. Recarga la página para reintentar.';
  });
  return snowLoading;
}

export function getSnowMap(){return snowMap;}
