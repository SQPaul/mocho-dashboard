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
    terrain=page.evaluate('({pitch:mochoMap.getPitch(),terrain:mochoMap.getTerrain(),elevation:mochoMap.queryTerrainElevation([-72.025,-39.933])})')
    assert terrain['terrain'] is not None, terrain
    assert terrain['elevation'] and terrain['elevation']>1000, terrain
    page.wait_for_function('window.mochoStakesReady === true')
    study=page.evaluate("""fetch('./data/study-area.json').then(r=>r.json()).then(d=>({
      imageDate:d.imageDate,
      glacierDate:d.glacier.features[0].properties.referenceDate,
      icecapDate:d.icecap.features[0].properties.referenceDate
    }))""")
    assert study=={'imageDate':'2026-03-10','glacierDate':'2026-03-10','icecapDate':'2026-03-10'},study
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
    assert page.locator('#history-chart [data-year]').count()==22
    assert page.locator('.history-jump').is_visible()
    page.locator('.history-jump').click()
    page.wait_for_function("document.querySelector('#history-title').getBoundingClientRect().top < innerHeight")
    assert page.locator('#history-chart').is_visible()
    assert page.locator('#history-table').count()==0
    assert page.locator('#history-download').is_visible()
    colors=page.evaluate("""({
      gain:getComputedStyle(document.querySelector('.positive .balance-bar')).fill,
      loss:getComputedStyle(document.querySelector('.negative .balance-bar')).fill
    })""")
    assert colors=={'gain':'rgb(57, 123, 179)','loss':'rgb(197, 83, 77)'},colors
    page.locator('#history-start').select_option('2022')
    assert page.locator('#history-chart [data-year]').count()==3
    page.locator('#history-uncertainty').check()
    assert page.locator('#history-chart .uncertainty-line').count()==3
    page.locator('#history-reset').click()
    page.screenshot(path=str(out/'desktop.png'),full_page=True)
    # Chapter 2: hash navigation, interactive Figure 7/4 and return path.
    page.goto(url + '#capitulo-2', wait_until='networkidle', timeout=60000)
    page.wait_for_function('window.mochoVariationReady === true',timeout=45000)
    page.wait_for_function('mochoVariationMap.isStyleLoaded()')
    page.wait_for_selector('#variation-chart .variation-line', timeout=30000)
    assert page.evaluate('mochoVariationMap.getTerrain()') is not None
    assert page.evaluate('mochoVariationMap.getPitch()') > 40
    assert page.locator('#variation-map canvas').is_visible()
    assert page.locator('#variation-map .contour-svg').count()==0
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
    assert 'Surface1976_v2024.shp' in page.locator('#contour-detail').inner_text()
    page.locator('#contour-select').select_option('1986')
    assert 'Surface_1986.shp' in page.locator('#contour-detail').inner_text()
    page.locator('#contour-select').select_option('2015')
    assert 'Mocho 20150411.shp' in page.locator('#contour-detail').inner_text()
    page.locator('#variation-view-3d').click()
    page.wait_for_function('mochoVariationMap.getPitch()>50')
    page.locator('#variation-start').select_option('2026')
    assert page.locator('#variation-chart g[data-year]').count()==2
    assert page.locator('#variation-table tbody tr').count()==2
    page.locator('#variation-chart g[data-series="icecap"]').focus()
    assert not page.locator('#chart-show-contour').is_disabled()
    page.locator('#chart-show-contour').click()
    assert page.locator('#contour-select').input_value()=='2026'
    with page.expect_download() as download:
        page.locator('#variation-download').click()
    assert download.value.suggested_filename.endswith('.csv')
    assert page.locator('body.chapter-two').count() == 1
    page.get_by_role('button', name='Restablecer',exact=True).click()
    assert page.locator('#variation-chart g[data-year]').count()==29
    page.locator('#variation-chart g[data-series="icecap"]').first.focus()
    page.keyboard.press('ArrowRight')
    assert '1986' in page.locator('#variation-readout-title').inner_text()
    assert not page.locator('#chart-show-contour').is_disabled()
    page.locator('.variation-map-card').screenshot(path=str(out/'variations-3d.png'))
    page.locator('.variation-chart-card').screenshot(path=str(out/'variations-chart.png'))
    page.locator('#chapter-two .back-link').click()
    page.wait_for_function("!document.body.classList.contains('chapter-two')")
    assert page.locator('#map').is_visible()
    page.get_by_role('button',name='2D',exact=True).click()
    page.wait_for_function('mochoMap.getPitch() < 1')
    assert page.evaluate('mochoMap.getTerrain()') is None
    page.get_by_role('checkbox',name='Mostrar balizas GNSS',exact=True).uncheck()
    assert page.evaluate("mochoMap.getLayoutProperty('stake-dot','visibility')")=='none'
    page.get_by_role('checkbox',name='Mostrar glaciar Mocho',exact=True).uncheck()
    assert page.evaluate("mochoMap.getLayoutProperty('glacier-fill','visibility')")=='none'
    page.get_by_role('checkbox',name='Mostrar glaciar Mocho',exact=True).check()
    assert page.evaluate("mochoMap.getLayoutProperty('glacier-fill','visibility')")=='visible'
    point=page.evaluate('mochoMap.project([-72.00936732,-39.94179041])')
    box=page.locator('#map').bounding_box()
    page.mouse.click(box['x']+point['x'],box['y']+point['y'])
    page.get_by_role('heading',name='Sector AWS-Mocho',exact=True).wait_for()
    page.locator('.maplibregl-popup-close-button').click()
    page.get_by_role('checkbox',name='Mostrar balizas GNSS',exact=True).check()
    page.wait_for_timeout(300)
    page.mouse.click(box['x']+point['x'],box['y']+point['y'])
    page.get_by_role('heading',name='Baliza B15',exact=True).wait_for()
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
    page.locator('.variation-map-card').screenshot(path=str(out/'variations-mobile.png'))
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
    assert not errors, errors
    fallback.wait_for_timeout(500)
    for context in browser.contexts:
        context.close()
    browser.close()
    print(json.dumps({'result':'PASS','terrain':terrain,'study':study,'historyColors':colors,'checks':['2026 study image and geometries','coordinate-only stake popup','Figure 2 gain/loss colors','Figure 2 without data table','3D elevation','GNSS screen placement','2D toggle','layers','point popup','zoom','sources','mobile','terrain network fallback','chapter 2 hash navigation','Figure 4 SVG series','Figure 7 3D contour map'],'pageErrors':errors},ensure_ascii=True))
