"""Browser checks for real map rendering, interactions, mobile layout and 2D fallback."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.cache'/'test-deps'))
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
    page.screenshot(path=str(out/'desktop.png'),full_page=True)
    page.get_by_role('button',name='2D',exact=True).click()
    page.wait_for_function('mochoMap.getPitch() < 1')
    assert page.evaluate('mochoMap.getTerrain()') is None
    page.get_by_role('checkbox',name='Mostrar glaciar Mocho',exact=True).uncheck()
    assert page.evaluate("mochoMap.getLayoutProperty('glacier-fill','visibility')")=='none'
    page.get_by_role('checkbox',name='Mostrar glaciar Mocho',exact=True).check()
    assert page.evaluate("mochoMap.getLayoutProperty('glacier-fill','visibility')")=='visible'
    point=page.evaluate('mochoMap.project([-72.00936732,-39.94179041])')
    box=page.locator('#map').bounding_box()
    page.mouse.click(box['x']+point['x'],box['y']+point['y'])
    page.get_by_role('heading',name='Sector AWS-Mocho',exact=True).wait_for()
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
    assert not errors, errors
    fallback=browser.new_page(viewport={'width':900,'height':750})
    fallback.route('https://tiles.mapterhorn.com/**',lambda route:route.abort())
    fallback.goto(url,wait_until='networkidle')
    fallback.wait_for_function('window.mochoReady === true',timeout=30000)
    assert fallback.get_by_role('button',name='3D',exact=True).is_disabled()
    assert fallback.evaluate('mochoMap.getTerrain()') is None
    print(json.dumps({'result':'PASS','terrain':terrain,'checks':['3D elevation','2D toggle','layers','point popup','zoom','sources','mobile','terrain network fallback'],'pageErrors':errors},ensure_ascii=True))
    browser.close()
