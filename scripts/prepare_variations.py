"""Generate compact chapter 2 derivatives from the report annex."""
import json
from pathlib import Path
import openpyxl
import fiona
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from PIL import Image
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform
from shapely.ops import unary_union
from shapely import make_valid

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r'P:\Projects\Mocho_DGA\2025-2026\1_DASHBOARD\AnexosDigitales\2_Variaciones_de_glaciares')
ARCHIVE = Path(r'P:\Projects\Mocho_DGA')
HISTORICAL = {
    1979: 'SIG/Delimitacion_glaciar/Mocho19790406.shp',
    1987: 'SIG/Delimitacion_glaciar/Surface_1987.shp',
    2000: 'SIG/Delimitacion_glaciar/Mocho20000221.shp',
    2005: 'SIG/Delimitacion_glaciar/surface_2005.shp',
    2017: 'SIG/Delimitacion_glaciar/Surface_2017.shp',
    2020: 'SIG/Delimitacion_glaciar/surface_2020.shp',
    2022: 'SIG/Delimitacion_glaciar/Surface_2022.shp',
    2023: '2023-2024/GIS/Delimitacion/Surface 2023.shp',
    2024: '2023-2024/GIS/Delimitacion/Surface 2024.shp',
}

def series(sheet, key):
    rows = list(openpyxl.load_workbook(SRC / 'Variaciones de glaciares 2025-2026.xlsx', data_only=True)[sheet].values)
    out = []
    for row in rows[1:]:
        if not isinstance(row[0], (int, float)): continue
        rate = row[8] if key == 'glacier' else row[7]
        out.append({'year': int(row[0]), 'area': float(row[1]), 'error': float(row[4]),
                    'perimeter': float(row[2]), 'rate': None if rate is None else float(rate), 'series': key})
    return out

def polygon(path, year):
    with fiona.open(path) as src:
        tr = Transformer.from_crs(src.crs, 4326, always_xy=True).transform
        metric = Transformer.from_crs(src.crs, 32718, always_xy=True).transform
        geoms = [make_valid(shape(f['geometry'])) for f in src if f['geometry']]
        geom = unary_union(geoms)
        area = transform(metric, geom).area / 1e6
        geo = transform(tr, geom.simplify(5, preserve_topology=True))
        west, south, east, north = geo.bounds
        assert -72.2 < west < east < -71.9 and -40.1 < south < north < -39.8, (year, geo.bounds)
        assert geo.is_valid and geo.geom_type in ('Polygon', 'MultiPolygon')
        crs = src.crs.to_string()
    return {'type': 'Feature', 'id': str(year), 'properties': {'year': year},
            'geometry': mapping(geo), 'sourceCrs': crs,
            'sourcePath': path.relative_to(ARCHIVE).as_posix(), 'geometryAreaKm2': area}

def main():
    out = ROOT / 'data'; out.mkdir(exist_ok=True)
    data = {'unit': 'km²', 'source': 'Informe final — Mocho 2025–2026, Figura 4, p. 19; Anexo 2, Variaciones de glaciares 2025–2026.',
            'glacier': series('Gl Mocho', 'glacier'), 'icecap': series('Capa de hielo Mocho Choshuenco', 'icecap')}
    (out / 'glacier-variations.json').write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    maps = {'type': 'FeatureCollection', 'features': [polygon(ARCHIVE / p, year) for year, p in HISTORICAL.items()],
            'availableYears': sorted([*HISTORICAL, 2025, 2026]), 'missingYears': [1976, 1986, 2015],
            'source': 'Archivo SIG de Mocho_DGA y Anexo 2. Cada geometría conserva ruta, CRS y año del archivo original.',
            'note': 'Los contornos de 1979 y 1987 están identificados con esos años en el proyecto QGIS 2022–2023; no se reasignan a 1976 ni 1986. Las áreas publicadas proceden del Excel, no de las geometrías simplificadas.'}
    maps['features'].append(polygon(SRC / '2_Polígonos/2025/Surface 2025_m.geojson', 2025))
    maps['features'].append(polygon(SRC / '2_Polígonos/2026/Surface2026.geojson', 2026))
    for f in maps['features']:
        row = next((r for r in data['icecap'] if r['year'] == f['properties']['year']), None)
        f['properties'].update({'source': f.pop('sourcePath'), 'sourceCrs': f.pop('sourceCrs'),
                                'geometryAreaKm2': f.pop('geometryAreaKm2'),
                                'area': row['area'] if row else None, 'error': row['error'] if row else None})
    (out / 'icecap-history.geojson').write_text(json.dumps(maps, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    image = next((SRC / '1_Imágenes').glob('*2026*False_color.tiff'))
    with rasterio.open(image) as src:
        affine, width, height = calculate_default_transform(src.crs, 'EPSG:3857', src.width, src.height, *src.bounds)
        rgb = np.zeros((3, height, width), dtype=np.uint8)
        for i in range(3):
            pixels = src.read(i + 1)
            if pixels.dtype != np.uint8:
                valid = pixels[np.isfinite(pixels) & (pixels != (src.nodata or 0))]
                low, high = np.percentile(valid, [2, 98])
                pixels = np.clip((pixels-low) / max(high-low, 1) * 255, 0, 255).astype(np.uint8)
            reproject(pixels, rgb[i], src_transform=src.transform, src_crs=src.crs,
                      dst_transform=affine, dst_crs='EPSG:3857', resampling=Resampling.bilinear)
        alpha = np.where(rgb.max(axis=0) > 0, 255, 0).astype(np.uint8)
        Image.fromarray(np.dstack([rgb.transpose(1, 2, 0), alpha])).save(out / 'satellite-2026.webp', quality=86, method=6)
        west, north = affine * (0, 0)
        east, south = affine * (width, height)
        to_geo = Transformer.from_crs(3857, 4326, always_xy=True).transform
        corners = [to_geo(west,north), to_geo(east,north), to_geo(east,south), to_geo(west,south)]
        data.update(imageCoordinates=corners, navigationBounds=[[corners[0][0],corners[2][1]], [corners[2][0],corners[0][1]]],
                    imageDate='2026-03-10', imageSource=image.relative_to(ARCHIVE).as_posix())
    (out / 'glacier-variations.json').write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print('Created series, georeferenced image and contours:', maps['availableYears'])
if __name__ == '__main__': main()
