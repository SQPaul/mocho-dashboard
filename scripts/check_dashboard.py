"""Browser checks for real map rendering, interactions, mobile layout and 2D fallback."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.cache'/'browser-deps'))
from playwright.sync_api import sync_playwright

url=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8000'
out=ROOT/'test-results'
out.mkdir(exist_ok=True)
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True,args=['--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(url,wait_until='networkidle',timeout=60000)
    page.wait_for_function('window.mochoReady === true',timeout=45000)
    page.wait_for_function('window.mochoMap.isStyleLoaded()')
    page.wait_for_timeout(1600)
    assert page.locator('#fallback').is_hidden()
    assert page.locator('.monitoring').count()==0
    assert page.locator('a[href*="github.com"]').count()==0
    assert page.locator('.author-name').inner_text()=='Paul Sandoval-Quilodrán'
    terrain=page.evaluate('({pitch:mochoMap.getPitch(),terrain:mochoMap.getTerrain(),elevation:mochoMap.queryTerrainElevation([-72.025,-39.933])})')
    assert terrain['terrain'] is not None, terrain
    assert terrain['elevation'] and terrain['elevation']>1000, terrain
    page.wait_for_function('window.mochoStakesReady === true')
    study=page.evaluate("""fetch('./data/study-area.json').then(r=>r.json()).then(d=>({
      imageDate:d.imageDate,
      glacierDate:d.glacier.features[0].properties.referenceDate,
      icecapDate:d.icecap.features[0].properties.referenceDate,
      stationNames:d.stations.features.map(f=>f.properties.name),
      stationKeys:d.stations.features.map(f=>Object.keys(f.properties)),
      summitNames:d.summits.features.map(f=>f.properties.name),
      emam:d.stations.features.find(f=>f.properties.name==='EMAM-Mocho')
    }))""")
    assert study['imageDate']=='2026-03-10' and study['glacierDate']=='2026-03-10' and study['icecapDate']=='2026-03-10',study
    assert study['stationNames']==['AWS Mocho1','AWS Mocho2','AWS DGA','EMAM-Mocho'],study
    assert all(keys==['name','lat','lon'] for keys in study['stationKeys']),study
    assert study['summitNames']==['Mocho','Choshuenco'],study
    assert study['emam']['properties']=={'name':'EMAM-Mocho','lat':-39.94179041,'lon':-72.00936732},study
    assert study['emam']['geometry']['coordinates']==[-72.00936732,-39.94179041],study
    landmark_style=page.evaluate("""({
      stationColor:mochoMap.getPaintProperty('station-dot','circle-color'),
      summitIcon:mochoMap.hasImage('summit-triangle'),
      stationsVisible:mochoMap.getLayoutProperty('station-dot','visibility')!=='none',
      summitsVisible:mochoMap.getLayoutProperty('summit-symbol','visibility')!=='none'
    })""")
    assert landmark_style=={'stationColor':'#397bb3','summitIcon':True,'stationsVisible':True,'summitsVisible':True},landmark_style
    assert page.locator('#stake-select option').count() == 11
    assert page.locator('.stake-marker').count() == 0
    page.locator('#stake-select').select_option('B15')
    assert page.get_by_role('heading',name='Baliza B15',exact=True).is_visible()
    popup_text=page.locator('.maplibregl-popup-content').inner_text()
    assert 'Latitud -39.941790° · Longitud -72.009367°' in popup_text,popup_text
    assert 'Medición:' not in popup_text and 'Anexo 3' not in popup_text,popup_text
    page.locator('.maplibregl-popup-close-button').click()
    # Native marker placement must match the terrain-projected GNSS point.
    placement=page.evaluate('''async () => {
      const data=await (await fetch('./data/stakes.geojson')).json();
      return data.features.map(f=>{
        const p=mochoMap.project(f.geometry.coordinates);
        return {id:f.id,x:p.x,y:p.y,hits:mochoMap.queryRenderedFeatures([[p.x-8,p.y-8],[p.x+8,p.y+8]],{layers:['stake-dot']}).map(h=>h.properties.name),hit:mochoMap.queryRenderedFeatures([[p.x-8,p.y-8],[p.x+8,p.y+8]],{layers:['stake-dot']}).some(h=>h.properties.name===f.id)};
      });
    }''')
    assert all(p['hit'] for p in placement), placement
    page.wait_for_selector('#history-content:not([hidden])')
    assert page.locator('#history-chart [data-year]').count()==23
    assert page.locator('.history-jump').is_visible()
    page.locator('.history-jump').click()
    page.wait_for_function("document.querySelector('#history-title').getBoundingClientRect().top < innerHeight")
    assert page.locator('#history-chart').is_visible()
    assert page.locator('#history-table').count()==0
    assert page.locator('#history-download').count()==0
    assert page.locator('.history-source').count()==0
    assert page.locator('#balance-historico .eyebrow').inner_text()=='MEMORIA DEL HIELO'
    assert page.locator('.history-heading .history-index').count()==0
    colors=page.evaluate("""({
      gain:getComputedStyle(document.querySelector('.positive .balance-bar')).fill,
      loss:getComputedStyle(document.querySelector('.negative .balance-bar')).fill
    })""")
    assert colors=={'gain':'rgb(57, 123, 179)','loss':'rgb(197, 83, 77)'},colors
    page.locator('#history-chart [data-year="2025"]').focus()
    assert page.locator('#history-year').inner_text()=='2025-2026'
    assert page.locator('#history-value').inner_text()=='-3,38 m eq.a.'
    assert '± 0,14 m eq.a.' in page.locator('#history-detail').inner_text()
    page.locator('#history-start').select_option('2022')
    assert page.locator('#history-chart [data-year]').count()==4
    page.locator('#history-uncertainty').check()
    assert page.locator('#history-chart .uncertainty-line').count()==4
    page.locator('#history-reset').click()
    page.screenshot(path=str(out/'desktop.png'),full_page=True)
    # Chapter 2: hash navigation, interactive Figure 7/4 and return path.
    page.goto(url + '#capitulo-2', wait_until='networkidle', timeout=60000)
    page.wait_for_function('window.mochoVariationReady === true',timeout=45000)
    page.wait_for_function('mochoVariationMap.isStyleLoaded()')
    page.wait_for_selector('#variation-chart .variation-line', timeout=30000)
    assert 'todos cambiamos.' in page.locator('#variation-title').inner_text()
    assert page.evaluate('mochoVariationMap.getTerrain()') is not None
    assert page.evaluate('mochoVariationMap.getPitch()') > 40
    assert page.locator('#variation-map canvas').is_visible()
    assert page.locator('#variation-map .contour-svg').count()==0
    assert page.locator('#chapter-two .variation-map-card .eyebrow').inner_text()=='DELIMITACIONES SOBRE EL RELIEVE'
    assert page.locator('#chapter-two .variation-chart-card .eyebrow').inner_text()=='SERIE HISTÓRICA'
    assert page.locator('.variation-source').count()==0
    assert page.locator('#variation-table').count()==0
    assert page.locator('#contour-controls input:not(:disabled)').count()==12
    assert page.locator('#contour-controls input:disabled').count()==0
    assert page.get_by_role('checkbox',name='Mostrar contorno 1976',exact=True).is_checked()
    assert page.get_by_role('checkbox',name='Mostrar contorno 2026',exact=True).is_checked()
    page.get_by_role('checkbox',name='Mostrar contorno 2005',exact=True).check()
    page.wait_for_timeout(800)
    assert page.evaluate("mochoVariationMap.queryRenderedFeatures({layers:['contour-2005']}).length")>0
    page.locator('#variation-view-2d').click()
    page.wait_for_function('mochoVariationMap.getPitch()<1')
    assert page.evaluate('mochoVariationMap.getTerrain()') is None
    page.get_by_role('checkbox',name='Mostrar contorno 2005',exact=True).uncheck()
    assert page.evaluate("mochoVariationMap.getLayoutProperty('contour-2005','visibility')")=='none'
    page.locator('#contour-select').select_option('1976')
    assert page.locator('#contour-detail').inner_text()=='1976 · Área 28,175 km² · Incertidumbre ± 3,481 km².'
    page.locator('#contour-select').select_option('1986')
    assert page.locator('#contour-detail').inner_text()=='1986 · Área 22,394 km² · Incertidumbre ± 1,279 km².'
    page.locator('#contour-select').select_option('2015')
    assert page.locator('#contour-detail').inner_text()=='2015 · Área 15,253 km² · Incertidumbre ± 0,697 km².'
    assert 'Archivo:' not in page.locator('#contour-detail').inner_text() and 'EPSG:' not in page.locator('#contour-detail').inner_text()
    page.locator('#variation-view-3d').click()
    page.wait_for_function('mochoVariationMap.getPitch()>50')
    page.locator('#variation-start').select_option('2026')
    assert page.locator('#variation-chart g[data-year]').count()==2
    page.locator('#variation-chart g[data-series="icecap"]').focus()
    assert not page.locator('#chart-show-contour').is_disabled()
    page.locator('#chart-show-contour').click()
    assert page.locator('#contour-select').input_value()=='2026'
    assert page.locator('#variation-download').count()==0
    assert page.locator('body.chapter-two').count() == 1
    page.get_by_role('button', name='Restablecer',exact=True).click()
    assert page.locator('#variation-chart g[data-year]').count()==29
    page.locator('#variation-chart g[data-series="icecap"]').first.focus()
    page.keyboard.press('ArrowRight')
    assert '1986' in page.locator('#variation-readout-title').inner_text()
    assert not page.locator('#chart-show-contour').is_disabled()
    page.locator('#chapter-two .variation-map-card').screenshot(path=str(out/'variations-3d.png'))
    page.locator('#chapter-two .variation-chart-card').screenshot(path=str(out/'variations-chart.png'))
    # Chapter 3: one GPR campaign at a time over the shared 3D terrain.
    page.locator('.chapter-nav').click()
    page.wait_for_function('window.mochoSnowReady === true',timeout=45000)
    page.wait_for_function('mochoSnowMap.isStyleLoaded()')
    page.wait_for_timeout(1200)
    assert page.locator('body.chapter-three').count()==1
    assert page.locator('#chapter-label').inner_text()=='03 Caracterización del manto nival'
    assert page.locator('#snow-title').inner_text()=='Midiendo lo invisible\nla nieve bajo nuestros pies'
    assert page.locator('#chapter-three').is_visible() and page.locator('#chapter-two').is_hidden()
    assert page.evaluate('mochoSnowMap.getTerrain()') is not None
    assert page.evaluate('mochoSnowMap.getPitch()')>40
    assert page.locator('#snow-map canvas').is_visible()
    assert page.locator('#snow-campaign-controls input').count()==5
    assert page.get_by_role('radio',name='Mostrar campaña GPR 19 OCT 2025',exact=True).is_checked()
    snow_manifest=page.evaluate("fetch('./data/gpr-campaigns.json').then(r=>r.json())")
    assert [row['year'] for row in snow_manifest['campaigns']]==[2021,2022,2023,2024,2025],snow_manifest
    assert snow_manifest['colorScale']['min']==0 and snow_manifest['colorScale']['max']==17,snow_manifest
    assert snow_manifest['colorScale']['ticks']==[0,3,6,9,12,15,17],snow_manifest
    assert all(len(row['imageCoordinates'])==4 for row in snow_manifest['campaigns']),snow_manifest
    assert all(set(row['stakeThickness'])=={'B8','B10','B11','B12','B13','B14','B15','B17','B18','B19'} for row in snow_manifest['campaigns']),snow_manifest
    assert all(all(isinstance(value,(int,float)) for value in row['stakeThickness'].values()) for row in snow_manifest['campaigns']),snow_manifest
    assert page.locator('#snow-scale-ticks').inner_text().split()==['0','3','6','9','12','15','17']
    assert 'linear-gradient' in page.locator('#snow-colorbar').evaluate("node=>getComputedStyle(node).backgroundImage")
    visibility=page.evaluate("""Object.fromEntries([2021,2022,2023,2024,2025].map(year=>[year,mochoSnowMap.getLayoutProperty(`gpr-${year}`,'visibility')]))""")
    assert visibility=={'2021':'none','2022':'none','2023':'none','2024':'none','2025':'visible'},visibility
    page.get_by_role('radio',name='Mostrar campaña GPR 19 OCT 2024',exact=True).check()
    assert page.evaluate("mochoSnowMap.getLayoutProperty('gpr-2024','visibility')")=='visible'
    assert page.evaluate("mochoSnowMap.getLayoutProperty('gpr-2025','visibility')")=='none'
    assert '19 OCT 2024' in page.locator('#snow-selection').inner_text()
    page.wait_for_function('window.mochoSnowStakesReady === true')
    snow_stake_placement=page.evaluate('''async () => {
      const data=await (await fetch('./data/stakes.geojson')).json();
      return data.features.map(f=>{
        const p=mochoSnowMap.project(f.geometry.coordinates);
        return {id:f.id,x:p.x,y:p.y,hit:mochoSnowMap.queryRenderedFeatures([[p.x-8,p.y-8],[p.x+8,p.y+8]],{layers:['snow-stake-dot']}).some(h=>h.properties.name===f.id)};
      });
    }''')
    assert all(point['hit'] for point in snow_stake_placement),snow_stake_placement
    b15=next(point for point in snow_stake_placement if point['id']=='B15')
    snow_box=page.locator('#snow-map').bounding_box()
    page.mouse.click(snow_box['x']+b15['x'],snow_box['y']+b15['y'])
    page.get_by_role('heading',name='Baliza B15',exact=True).wait_for()
    for year,label,value in [(2021,'08 OCT 2021','4,46'),(2022,'14 OCT 2022','6,35'),(2023,'17 OCT 2023','3,19'),(2024,'19 OCT 2024','4,24'),(2025,'19 OCT 2025','2,42')]:
        page.locator(f'#snow-campaign-controls input[value="{year}"]').check()
        popup=page.locator('.maplibregl-popup-content').inner_text()
        assert f'GPR · {label}' in popup,popup
        assert f'Espesor del manto nival · {value} m' in popup,popup
    page.locator('#chapter-three .variation-map-card').screenshot(path=str(out/'snow-stake-popup.png'))
    page.locator('.maplibregl-popup-close-button').click()
    assert page.locator('#snow-table-body tr').count()==5
    table_rows=page.locator('#snow-table-body tr').all_inner_texts()
    assert table_rows[0].split()==['Oct','2021','14.295','7,30','5,02','0,73','3,08','7,18'],table_rows
    assert table_rows[-1].split()==['Oct','2025','19.467','9,90','5,05','0,89','3,14','8,77'],table_rows
    page.locator('#snow-view-2d').click()
    page.wait_for_function('mochoSnowMap.getPitch()<1')
    assert page.evaluate('mochoSnowMap.getTerrain()') is None
    page.locator('#snow-view-3d').click()
    page.wait_for_function('mochoSnowMap.getPitch()>50')
    page.locator('#chapter-three .variation-map-card').screenshot(path=str(out/'snow-3d.png'))
    page.locator('#chapter-three .snow-table-card').screenshot(path=str(out/'snow-table.png'))
    page.screenshot(path=str(out/'snow-desktop.png'),full_page=True)
    # Chapter 4: rainbow velocity raster with the ten velocity stakes above it.
    page.locator('.chapter-nav').click()
    page.wait_for_function('window.mochoVelocityReady === true',timeout=45000)
    page.wait_for_function('mochoVelocityMap.isStyleLoaded()')
    page.wait_for_function('window.mochoVelocityStakesReady === true',timeout=30000)
    page.wait_for_timeout(1200)
    assert page.locator('body.chapter-four').count()==1
    assert page.locator('#chapter-label').inner_text()=='04 Cinemática glaciar'
    assert page.locator('#velocity-title').inner_text()=='El hielo avanza\nfluyamos con él'
    assert page.locator('#chapter-four').is_visible() and page.locator('#chapter-three').is_hidden()
    assert page.evaluate('mochoVelocityMap.getTerrain()') is not None
    assert page.evaluate('mochoVelocityMap.getPitch()')>40
    assert page.locator('#velocity-map canvas').is_visible()
    velocity_manifest=page.evaluate("fetch('./data/velocity-2025-2026.json').then(r=>r.json())")
    assert velocity_manifest['period']['label']=='OCT 2025–ABR 2026',velocity_manifest
    assert velocity_manifest['unit']=='m/a' and velocity_manifest['palette']=='rainbow',velocity_manifest
    assert velocity_manifest['colorScale']=={
        'min':0.0,'max':30.0,'ticks':[0,5,10,15,20,25,30],
        'stops':velocity_manifest['colorScale']['stops']
    },velocity_manifest
    assert 0.89<velocity_manifest['image']['rasterMin']<0.90,velocity_manifest
    assert 28.57<velocity_manifest['image']['rasterMax']<28.58,velocity_manifest
    assert len(velocity_manifest['image']['imageCoordinates'])==4,velocity_manifest
    assert len(velocity_manifest['stakes']['features'])==10,velocity_manifest
    assert {f['properties']['name'] for f in velocity_manifest['stakes']['features']}=={'B8','B10','B11','B12','B13','B14','B15','B17','B18','B19'},velocity_manifest
    b11_feature=next(f for f in velocity_manifest['stakes']['features'] if f['properties']['name']=='B11')
    assert b11_feature['properties']=={'name':'B11','sourceName':'B11_2024-2025','period':'2024–2025','velocityMPerYear':0.8899},b11_feature
    assert page.locator('#velocity-scale-ticks').inner_text().split()==['0','5','10','15','20','25','30']
    assert 'linear-gradient' in page.locator('#velocity-colorbar').evaluate("node=>getComputedStyle(node).backgroundImage")
    assert page.evaluate("mochoVelocityMap.getLayer('velocity-raster').type")=='raster'
    velocity_layer_order=page.evaluate("mochoVelocityMap.getStyle().layers.map(layer=>layer.id)")
    assert velocity_layer_order.index('satellite')<velocity_layer_order.index('velocity-raster')<velocity_layer_order.index('velocity-stake-dot'),velocity_layer_order
    velocity_stake_placement=page.evaluate('''async () => {
      const data=await (await fetch('./data/velocity-2025-2026.json')).json();
      return data.stakes.features.map(f=>{
        const p=mochoVelocityMap.project(f.geometry.coordinates);
        return {id:f.id,x:p.x,y:p.y,hit:mochoVelocityMap.queryRenderedFeatures([[p.x-8,p.y-8],[p.x+8,p.y+8]],{layers:['velocity-stake-dot']}).some(h=>h.properties.name===f.id)};
      });
    }''')
    assert all(point['hit'] for point in velocity_stake_placement),velocity_stake_placement
    b13=next(point for point in velocity_stake_placement if point['id']=='B13')
    velocity_box=page.locator('#velocity-map').bounding_box()
    page.mouse.click(velocity_box['x']+b13['x'],velocity_box['y']+b13['y'])
    page.get_by_role('heading',name='Baliza B13',exact=True).wait_for()
    velocity_popup=page.locator('.maplibregl-popup-content').inner_text()
    assert 'VELOCIDAD ANUAL · 2025–2026' in velocity_popup,velocity_popup
    assert '28,57 m/a' in velocity_popup,velocity_popup
    assert 'GNSS · DGA–UACh' in velocity_popup,velocity_popup
    page.locator('.maplibregl-popup-close-button').click()
    b11=next(point for point in velocity_stake_placement if point['id']=='B11')
    page.mouse.click(velocity_box['x']+b11['x'],velocity_box['y']+b11['y'])
    page.get_by_role('heading',name='Baliza B11',exact=True).wait_for()
    velocity_popup=page.locator('.maplibregl-popup-content').inner_text()
    assert 'VELOCIDAD ANUAL · 2024–2025' in velocity_popup,velocity_popup
    assert '0,89 m/a' in velocity_popup,velocity_popup
    page.locator('#chapter-four .variation-map-card').screenshot(path=str(out/'velocity-stake-popup.png'))
    page.locator('.maplibregl-popup-close-button').click()
    page.locator('#velocity-view-2d').click()
    page.wait_for_function('mochoVelocityMap.getPitch()<1')
    assert page.evaluate('mochoVelocityMap.getTerrain()') is None
    page.locator('#velocity-view-3d').click()
    page.wait_for_function('mochoVelocityMap.getPitch()>50')
    page.locator('#chapter-four .variation-map-card').screenshot(path=str(out/'velocity-3d.png'))
    page.screenshot(path=str(out/'velocity-desktop.png'),full_page=True)
    page.locator('#chapter-four .back-link').click()
    page.wait_for_function("document.body.classList.contains('chapter-three')")
    assert page.locator('#snow-map canvas').is_visible()
    page.locator('#chapter-three .back-link').click()
    page.wait_for_function("document.body.classList.contains('chapter-two')")
    assert page.locator('#variation-map canvas').is_visible()
    page.locator('#chapter-two .back-link').click()
    page.wait_for_function("!document.body.classList.contains('chapter-two')")
    assert page.locator('#map').is_visible()
    page.get_by_role('button',name='2D',exact=True).click()
    page.wait_for_function('mochoMap.getPitch() < 1')
    assert page.evaluate('mochoMap.getTerrain()') is None
    page.get_by_role('checkbox',name='Mostrar balizas GNSS',exact=True).uncheck()
    assert page.evaluate("mochoMap.getLayoutProperty('stake-dot','visibility')")=='none'
    page.get_by_role('checkbox',name='Mostrar estaciones meteorológicas',exact=True).uncheck()
    assert page.evaluate("mochoMap.getLayoutProperty('station-dot','visibility')")=='none'
    page.get_by_role('checkbox',name='Mostrar estaciones meteorológicas',exact=True).check()
    page.get_by_role('checkbox',name='Mostrar cumbres',exact=True).uncheck()
    assert page.evaluate("mochoMap.getLayoutProperty('summit-symbol','visibility')")=='none'
    page.get_by_role('checkbox',name='Mostrar cumbres',exact=True).check()
    page.get_by_role('checkbox',name='Mostrar glaciar Mocho',exact=True).uncheck()
    assert page.evaluate("mochoMap.getLayoutProperty('glacier-fill','visibility')")=='none'
    page.get_by_role('checkbox',name='Mostrar glaciar Mocho',exact=True).check()
    assert page.evaluate("mochoMap.getLayoutProperty('glacier-fill','visibility')")=='visible'
    polygon_points=page.evaluate("""()=>{
      const canvas=mochoMap.getCanvas(),found={};
      for(let y=80;y<canvas.clientHeight-80;y+=12)for(let x=80;x<canvas.clientWidth-80;x+=12){
        const glacier=mochoMap.queryRenderedFeatures([x,y],{layers:['glacier-fill']}).length>0;
        const icecap=mochoMap.queryRenderedFeatures([x,y],{layers:['icecap-fill']}).length>0;
        const marker=mochoMap.queryRenderedFeatures([x,y],{layers:['stake-dot','stake-label','station-dot','station-halo','summit-symbol']}).length>0;
        if(glacier&&!marker&&!found.glacier)found.glacier={x,y};
        if(icecap&&!glacier&&!marker&&!found.icecap)found.icecap={x,y};
        if(found.glacier&&found.icecap)return found;
      }
      return found;
    }""")
    assert polygon_points.get('glacier') and polygon_points.get('icecap'),polygon_points
    box=page.locator('#map').bounding_box()
    page.mouse.click(box['x']+polygon_points['glacier']['x'],box['y']+polygon_points['glacier']['y'])
    page.get_by_role('heading',name='Glaciar Mocho',exact=True).wait_for()
    assert page.locator('.maplibregl-popup-content p,.maplibregl-popup-content .popup-tag').count()==0
    page.locator('.maplibregl-popup-close-button').click()
    page.mouse.click(box['x']+polygon_points['icecap']['x'],box['y']+polygon_points['icecap']['y'])
    page.get_by_role('heading',name='Capa de hielo Mocho–Choshuenco',exact=True).wait_for()
    assert page.locator('.maplibregl-popup-content p,.maplibregl-popup-content .popup-tag').count()==0
    page.locator('.maplibregl-popup-close-button').click()
    point=page.evaluate('mochoMap.project([-72.00936732,-39.94179041])')
    page.mouse.click(box['x']+point['x'],box['y']+point['y'])
    page.get_by_role('heading',name='EMAM-Mocho',exact=True).wait_for()
    assert 'Latitud -39.94179041° · Longitud -72.00936732°' in page.locator('.maplibregl-popup-content').inner_text()
    page.locator('.maplibregl-popup-close-button').click()
    page.get_by_role('checkbox',name='Mostrar balizas GNSS',exact=True).check()
    page.wait_for_timeout(300)
    page.mouse.click(box['x']+point['x'],box['y']+point['y'])
    page.get_by_role('heading',name='Baliza B15',exact=True).wait_for()
    page.locator('.maplibregl-popup-close-button').click()
    summit_point=page.evaluate("""async()=>{const d=await (await fetch('./data/study-area.json')).json();return mochoMap.project(d.summits.features.find(f=>f.properties.name==='Mocho').geometry.coordinates)}""")
    page.mouse.click(box['x']+summit_point['x'],box['y']+summit_point['y'])
    page.get_by_role('heading',name='Mocho',exact=True).wait_for()
    assert 'Latitud -39.93162° · Longitud -72.02994°' in page.locator('.maplibregl-popup-content').inner_text()
    page.locator('.maplibregl-popup-close-button').click()
    zoom=page.evaluate('mochoMap.getZoom()')
    page.get_by_role('button',name='Acercar',exact=True).click()
    page.wait_for_function(f'mochoMap.getZoom() > {zoom+0.5}')
    page.get_by_role('button',name='Volver a la vista inicial',exact=True).click()
    page.get_by_role('button',name='Fuentes y notas del mapa').click()
    assert page.locator('#sources-dialog').is_visible()
    page.get_by_role('button',name='Cerrar fuentes').click()
    page.get_by_role('button',name='3D',exact=True).click()
    page.set_viewport_size({'width':390,'height':844})
    page.wait_for_timeout(1400)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile overflow'
    assert page.locator('#map').bounding_box()['height'] >= 390
    page.screenshot(path=str(out/'mobile.png'),full_page=True)
    page.locator('.chapter-nav').click()
    page.wait_for_timeout(600)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Chapter 2 mobile overflow'
    assert page.locator('#variation-map').bounding_box()['height']>=390
    page.locator('#chapter-two .variation-map-card').screenshot(path=str(out/'variations-mobile.png'))
    page.locator('.chapter-nav').click()
    page.wait_for_function('window.mochoSnowReady === true',timeout=30000)
    page.wait_for_timeout(600)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Chapter 3 mobile overflow'
    assert page.locator('#snow-map').bounding_box()['height']>=390
    page.locator('#chapter-three .variation-map-card').screenshot(path=str(out/'snow-mobile.png'))
    page.locator('.chapter-nav').click()
    page.wait_for_function('window.mochoVelocityReady === true',timeout=30000)
    page.wait_for_timeout(600)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Chapter 4 mobile overflow'
    assert page.locator('#velocity-map').bounding_box()['height']>=390
    page.locator('#chapter-four .variation-map-card').screenshot(path=str(out/'velocity-mobile.png'))
    page.locator('#chapter-four .back-link').click()
    page.locator('#chapter-three .back-link').click()
    page.locator('#chapter-two .back-link').click()
    assert not errors, errors
    fallback=browser.new_page(viewport={'width':900,'height':750})
    fallback.route('https://tiles.mapterhorn.com/**',lambda route:route.abort())
    fallback.goto(url,wait_until='networkidle')
    fallback.wait_for_function('window.mochoReady === true',timeout=30000)
    assert fallback.get_by_role('button',name='3D',exact=True).is_disabled()
    assert fallback.evaluate('mochoMap.getTerrain()') is None
    fallback.locator('.chapter-nav').click()
    fallback.wait_for_function('window.mochoVariationReady === true',timeout=30000)
    assert fallback.locator('#variation-view-3d').is_disabled()
    assert fallback.evaluate('mochoVariationMap.getTerrain()') is None
    fallback.wait_for_function('mochoVariationMap.isStyleLoaded()')
    fallback.locator('.chapter-nav').click()
    fallback.wait_for_function('window.mochoSnowReady === true',timeout=30000)
    assert fallback.locator('#snow-view-3d').is_disabled()
    assert fallback.evaluate('mochoSnowMap.getTerrain()') is None
    fallback.wait_for_function('mochoSnowMap.isStyleLoaded()')
    fallback.locator('.chapter-nav').click()
    fallback.wait_for_function('window.mochoVelocityReady === true',timeout=30000)
    assert fallback.locator('#velocity-view-3d').is_disabled()
    assert fallback.evaluate('mochoVelocityMap.getTerrain()') is None
    fallback.wait_for_function('mochoVelocityMap.isStyleLoaded()')
    # Failed chapter 2 assets must report their failure and preserve chapter 1.
    for asset,selector,expected in [
        ('icecap-history.geojson','#variation-map-message','datos del mapa'),
        ('glacier-variations.json','.variation-scroll','serie no pudo cargarse'),
        ('satellite-2026.webp','#variation-map-message','imagen de 2026')
    ]:
        broken=browser.new_page()
        broken.on('pageerror',lambda e:errors.append(str(e)))
        broken.route('**/data/'+asset,lambda route:route.abort())
        broken.goto(url+'#capitulo-2',wait_until='networkidle')
        broken.wait_for_function('(a)=>document.querySelector(a[0]).textContent.includes(a[1])',arg=[selector,expected])
        assert broken.locator(selector).is_visible()
        if asset!='glacier-variations.json':
            assert broken.locator('#variation-chart g[data-year]').count()==29
        broken.locator('#chapter-two .back-link').click()
        broken.wait_for_function('window.mochoReady===true')
        assert broken.locator('#map canvas').is_visible()
        broken.close()
    # Failed GPR assets must remain isolated to chapter 3.
    broken=browser.new_page()
    broken.on('pageerror',lambda e:errors.append(str(e)))
    broken.route('**/data/gpr-campaigns.json',lambda route:route.abort())
    broken.goto(url+'#capitulo-3',wait_until='networkidle')
    broken.wait_for_function("document.querySelector('#snow-map-message').textContent.includes('campañas GPR')")
    assert 'resumen GPR' in broken.locator('#snow-table-loading').inner_text()
    broken.locator('#chapter-three .back-link').click()
    broken.wait_for_function('window.mochoVariationReady===true')
    assert broken.locator('#variation-map canvas').is_visible()
    broken.close()
    broken=browser.new_page()
    broken.on('pageerror',lambda e:errors.append(str(e)))
    broken.route('**/data/gpr-2025.webp',lambda route:route.abort())
    broken.goto(url+'#capitulo-3',wait_until='networkidle')
    broken.wait_for_function("document.querySelector('#snow-map-message').textContent.includes('GPR 2025')")
    assert broken.get_by_role('radio',name='Mostrar campaña GPR 19 OCT 2025',exact=True).is_disabled()
    broken.get_by_role('radio',name='Mostrar campaña GPR 19 OCT 2024',exact=True).check()
    assert broken.evaluate("mochoSnowMap.getLayoutProperty('gpr-2024','visibility')")=='visible'
    broken.close()
    # Failed velocity assets must preserve the chapter shell and the earlier chapters.
    broken=browser.new_page()
    broken.on('pageerror',lambda e:errors.append(str(e)))
    broken.route('**/data/velocity-2025-2026.json',lambda route:route.abort())
    broken.goto(url+'#capitulo-4',wait_until='networkidle')
    broken.wait_for_function("document.querySelector('#velocity-map-message').textContent.includes('datos de velocidad')")
    assert broken.locator('#velocity-map canvas').is_visible()
    broken.locator('#chapter-four .back-link').click()
    broken.wait_for_function('window.mochoSnowReady===true')
    assert broken.locator('#snow-map canvas').is_visible()
    broken.close()
    broken=browser.new_page()
    broken.on('pageerror',lambda e:errors.append(str(e)))
    broken.route('**/data/velocity-202510-202604.webp',lambda route:route.abort())
    broken.goto(url+'#capitulo-4',wait_until='networkidle')
    broken.wait_for_function("document.querySelector('#velocity-map-message').textContent.includes('raster de velocidad')")
    broken.wait_for_function('window.mochoVelocityStakesReady===true')
    assert broken.evaluate("mochoVelocityMap.getLayer('velocity-stake-dot').type")=='circle'
    broken.close()
    assert not errors, errors
    fallback.wait_for_timeout(500)
    for context in browser.contexts:
        context.close()
    browser.close()
    print(json.dumps({'result':'PASS','terrain':terrain,'study':study,'landmarkStyle':landmark_style,'historyColors':colors,'checks':['2026 study image and geometries','four coordinate-only stations','B15 priority over EMAM-Mocho','yellow summit symbols','coordinate-only stake popup','2025-2026 mass balance','gain/loss colors','titles without figure numbers','no data tables or source-note accordions','no CSV downloads','no public GitHub links','minimal glacier and ice-cap popups','minimal contour year details','3D elevation','GNSS screen placement','2D toggle','layers','summit popup','zoom','map sources','mobile','terrain network fallback','chapter 2 hash navigation','historical area SVG series','3D contour map','chapter 3 hash navigation','five exclusive GPR campaigns','shared Blues scale 0-17 m','ten GPR stake markers','stake thickness for every campaign','GPR summary table','GPR asset fallback','chapter 4 hash navigation','rainbow velocity scale 0-30 m/a','ten velocity stake markers','B11 2024-2025 period','velocity asset fallback'],'pageErrors':errors},ensure_ascii=True))
