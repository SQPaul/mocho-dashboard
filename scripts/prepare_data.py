"""Generate web derivatives without changing original annexes."""
import argparse
import json
from pathlib import Path
import fiona
import numpy as np
import rasterio
from PIL import Image
from pyproj import Transformer
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import shape, mapping
from shapely.ops import transform

def collection(path, name, category, description, source):
    with fiona.open(path) as ds:
        project = Transformer.from_crs(ds.crs, 4326, always_xy=True).transform
        features = []
        for index, feature in enumerate(ds):
            geom = shape(feature['geometry'])
            if not geom.is_valid:
                raise ValueError(f'Invalid geometry in {path}, feature {index}')
            geom = transform(project, geom.simplify(1, preserve_topology=True))
            features.append({'type':'Feature','id':index,'properties':{
                'name':name,'category':category,'description':description,'source':source,'referenceDate':'2025-03-25'
            },'geometry':mapping(geom)})
    return {'type':'FeatureCollection','features':features}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    root=parser.parse_args().source.resolve(strict=True)
    output=Path(__file__).resolve().parents[1]/'data'
    output.mkdir(exist_ok=True)
    glacier_path=next(root.glob('2_*/2_*/2025/*.shp'))
    icecap_path=next(root.glob('2_*/2_*/2025/Surface*.geojson'))
    image_path=next(root.glob('2_*/1_*/2025*False_color.tiff'))
    with rasterio.open(image_path) as src:
        affine,width,height=calculate_default_transform(src.crs,'EPSG:3857',src.width,src.height,*src.bounds)
        target=np.zeros((3,height,width),dtype=np.uint8)
        for band in range(3):
            pixels=src.read(band+1)
            if pixels.dtype!=np.uint8:
                valid=pixels[np.isfinite(pixels)&(pixels!=(src.nodata or 0))]
                low,high=np.percentile(valid,[2,98])
                pixels=np.clip((pixels-low)/max(high-low,1)*255,0,255).astype(np.uint8)
            reproject(pixels,target[band],src_transform=src.transform,src_crs=src.crs,dst_transform=affine,dst_crs='EPSG:3857',resampling=Resampling.bilinear)
        rgba=np.dstack([target.transpose(1,2,0),np.where(target.max(axis=0)>0,255,0).astype(np.uint8)])
        Image.fromarray(rgba).save(output/'satellite-2025.webp',quality=88,method=6)
        west,north=affine*(0,0)
        east,south=affine*(width,height)
        to_geo=Transformer.from_crs(3857,4326,always_xy=True).transform
        corners=[to_geo(west,north),to_geo(east,north),to_geo(east,south),to_geo(west,south)]
    data={
        'report':{'title':'Informe final — Mocho 2025–2026, versión final','section':'1.1','pages':[3,4]},
        'imageCoordinates':corners,'navigationBounds':[[corners[0][0],corners[2][1]],[corners[2][0],corners[0][1]]],
        'glacier':collection(glacier_path,'Glaciar Mocho','Área de estudio · 2025','Vertiente suroriental del complejo Mocho–Choshuenco. Superficie de referencia: 4,94 ± 0,09 km².','Anexo 2; superficie publicada en Tabla 1, DGA (2025).'),
        'icecap':collection(icecap_path,'Capa de hielo Mocho–Choshuenco','Contexto glaciológico · 2025','Conjunto de cuerpos de hielo del complejo volcánico. El glaciar Mocho ocupa su vertiente suroriental.','Anexo 2, delimitación sobre Sentinel-2 del 25/03/2025.'),
        'points':{'type':'FeatureCollection','features':[
            {'type':'Feature','id':'bmch','geometry':{'type':'Point','coordinates':[-(72+28.08/3600),-(39+55/60+47.7903/3600)]},'properties':{'name':'Base geodésica BMCH','category':'Referencia GNSS','description':'Punto de referencia instalado por la Universidad Austral de Chile. Base de los levantamientos GNSS.','source':'Coordenadas: Tabla 2 del informe, página 30.'}},
            {'type':'Feature','id':'aws-sector','geometry':{'type':'Point','coordinates':[-72.00936732,-39.94179041]},'properties':{'name':'Sector AWS-Mocho','category':'Referencia de sector · B15','description':'AWS estival a aproximadamente 1.920 m s.n.m. El marcador corresponde a B15, cercana a la estación; no indica su coordenada exacta.','source':'Anexo 3, B15, levantamiento de noviembre de 2025; informe, sección 8.2.1.'}}
        ]},
        'provenance':{'glacier':str(glacier_path.relative_to(root)),'icecap':str(icecap_path.relative_to(root)),'satellite':str(image_path.relative_to(root)),'outputCrs':'EPSG:4326','imageCrs':'EPSG:3857'}
    }
    (output/'study-area.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f'Created {len(data["glacier"]["features"])} glacier polygons, {len(data["icecap"]["features"])} ice-cap polygons and 2 points.')
    print(f'Image: {width} x {height}; {(output/"satellite-2025.webp").stat().st_size/1e6:.2f} MB')

if __name__=='__main__':
    main()
