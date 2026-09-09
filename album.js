const el = selector => document.querySelector(selector);
let albumLoading;
let albumItems=[];
let frame;

const clamp = value => Math.max(0,Math.min(1,value));

function updateFocus(){
  frame=undefined;
  if(!albumItems.length||el('#chapter-five').hidden)return;
  const viewportCenter=innerHeight/2;
  let active;
  let nearest=Infinity;
  for(const item of albumItems){
    const box=item.getBoundingClientRect();
    const distance=Math.abs(box.top+box.height/2-viewportCenter);
    const focus=clamp(1-distance/(innerHeight*.78));
    item.style.setProperty('--focus',focus.toFixed(3));
    if(distance<nearest){nearest=distance;active=item;}
  }
  for(const item of albumItems)item.classList.toggle('is-active',item===active);
}

function scheduleFocus(){
  if(frame===undefined)frame=requestAnimationFrame(updateFocus);
}

function renderAlbum(data){
  const list=el('#album-list');
  const fragment=document.createDocumentFragment();
  data.photographs.forEach((photograph,index)=>{
    const figure=document.createElement('figure');
    const image=document.createElement('img');
    figure.className='album-item';
    figure.dataset.order=photograph.order;
    image.src=`./data/${photograph.src}`;
    image.width=photograph.width;
    image.height=photograph.height;
    image.alt=`Fotografía ${photograph.order} del álbum del equipo`;
    image.decoding='async';
    image.loading=index<2?'eager':'lazy';
    image.addEventListener('load',scheduleFocus,{once:true});
    figure.append(image);fragment.append(figure);
  });
  list.replaceChildren(fragment);
  albumItems=[...list.querySelectorAll('.album-item')];
  const observer=new IntersectionObserver(scheduleFocus,{rootMargin:'35% 0px',threshold:[0,.25,.5,.75,1]});
  albumItems.forEach(item=>observer.observe(item));
  addEventListener('scroll',scheduleFocus,{passive:true});
  addEventListener('resize',scheduleFocus,{passive:true});
  scheduleFocus();
  window.mochoAlbumReady=true;
}

export function initAlbumChapter(){
  if(albumLoading)return albumLoading;
  window.mochoAlbumReady=false;
  albumLoading=fetch('./data/album.json').then(response=>{
    if(!response.ok)throw new Error('album.json');
    return response.json();
  }).then(renderAlbum).catch(()=>{
    el('#album-loading').textContent='No fue posible cargar el álbum. Recarga la página para reintentar.';
  });
  return albumLoading;
}

export function refreshAlbumFocus(){scheduleFocus();}
