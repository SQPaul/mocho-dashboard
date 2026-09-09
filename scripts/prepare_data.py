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

def collection(path, name, category, description, source, reference_date):
    with fiona.open(path) as ds:
        project = Transformer.from_crs(ds.crs, 4326, always_xy=True).transform
        features = []
        for index, feature in enumerate(ds):
            geom = shape(feature['geometry'])
            if not geom.is_valid:
                raise ValueError(f'Invalid geometry in {path}, feature {index}')
            geom = transform(project, geom.simplify(1, preserve_topology=True))
            features.append({'type':'Feature','id':index,'properties':{
                'name':name,'category':category,'description':description,'source':source,'referenceDate':reference_date
            },'geometry':mapping(geom)})
    return {'type':'FeatureCollection','features':features}

def point_collection(path, prefix):
    with fiona.open(path) as ds:
        project = Transformer.from_crs(ds.crs, 4326, always_xy=True)
        features = []
        for index, feature in enumerate(ds):
            properties = feature['properties']
            coordinates = feature['geometry']['coordinates']
            lon, lat = project.transform(coordinates[0], coordinates[1])
            name = properties['Name'].strip()
            features.append({'type':'Feature','id':f'{prefix}-{index + 1}','properties':{
                'name':name,'lat':properties['Lat'],'lon':properties['Lon']
            },'geometry':{'type':'Point','coordinates':[lon,lat]}})
    return {'type':'FeatureCollection','features':features}

def main():
    repository=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--stations',type=Path,default=repository/'data/geometrias/estaciones.gpkg')
    parser.add_argument('--summits',type=Path,default=repository/'data/geometrias/cumbres.shp')
    args=parser.parse_args()
    root=args.source.resolve(strict=True)
    stations_path=args.stations.resolve(strict=True)
    summits_path=args.summits.resolve(strict=True)
    output=repository/'data'
    output.mkdir(exist_ok=True)
    variations=next(root.glob('2_*'))
    polygons=next(variations.glob('2_*'))
    images=next(variations.glob('1_*'))
    glacier_path=polygons/'2026'/'Cuenca_SO_2026 18S.geojson'
    icecap_path=polygons/'2026'/'Surface2026.geojson'
    image_path=next(images.glob('*2026*False_color.tiff'))
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
        Image.fromarray(rgba).save(output/'satellite-2026.webp',quality=86,method=6)
        west,north=affine*(0,0)
        east,south=affine*(width,height)
        to_geo=Transformer.from_crs(3857,4326,always_xy=True).transform
        corners=[to_geo(west,north),to_geo(east,north),to_geo(east,south),to_geo(west,south)]
    stations=point_collection(stations_path,'station')
    stakes=json.loads((output/'stakes.geojson').read_text(encoding='utf-8'))
    b15=next(feature for feature in stakes['features'] if feature['id']=='B15')
    b15_lon,b15_lat=b15['geometry']['coordinates'][:2]
    stations['features'].append({'type':'Feature','id':'station-emam-mocho','properties':{
        'name':'EMAM-Mocho','lat':b15_lat,'lon':b15_lon
    },'geometry':{'type':'Point','coordinates':[b15_lon,b15_lat]}})
    summits=point_collection(summits_path,'summit')
    def source_label(path):
        try:
            return path.relative_to(repository).as_posix()
        except ValueError:
            return path.name
    data={
        'report':{'title':'Informe final — Mocho 2025–2026, versión final','section':'1.1','pages':[3,4]},
        'imageCoordinates':corners,'navigationBounds':[[corners[0][0],corners[2][1]],[corners[2][0],corners[0][1]]],
        'imageDate':'2026-03-10',
        'glacier':collection(glacier_path,'Glaciar Mocho','Área de estudio · 2026','Vertiente suroriental del complejo Mocho–Choshuenco. Superficie de referencia: 4,91 ± 0,09 km².','Anexo 2; delimitación sobre Sentinel-2 del 10/03/2026.','2026-03-10'),
        'icecap':collection(icecap_path,'Capa de hielo Mocho–Choshuenco','Contexto glaciológico · 2026','Conjunto de cuerpos de hielo del complejo volcánico. Superficie de referencia: 12,12 ± 0,43 km².','Anexo 2; delimitación sobre Sentinel-2 del 10/03/2026.','2026-03-10'),
        'stations':stations,'summits':summits,
        'provenance':{'glacier':str(glacier_path.relative_to(root)),'icecap':str(icecap_path.relative_to(root)),'satellite':str(image_path.relative_to(root)),
                      'stations':source_label(stations_path),'summits':source_label(summits_path),'emamMocho':'Baliza B15 · data/stakes.geojson',
                      'outputCrs':'EPSG:4326','imageCrs':'EPSG:3857'}
    }
    (output/'study-area.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f'Created {len(data["glacier"]["features"])} glacier polygons, {len(data["icecap"]["features"])} ice-cap polygons, {len(stations["features"])} stations and {len(summits["features"])} summits.')
    print(f'Image: {width} x {height}; {(output/"satellite-2026.webp").stat().st_size/1e6:.2f} MB')

if __name__=='__main__':
    main()
