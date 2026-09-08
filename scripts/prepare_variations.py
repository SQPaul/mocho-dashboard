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

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r'P:\Projects\Mocho_DGA\2025-2026\1_DASHBOARD\AnexosDigitales\2_Variaciones_de_glaciares')

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
    tr = Transformer.from_crs(32718, 4326, always_xy=True).transform
    with fiona.open(path) as src:
        geometries = []
        for f in src:
            geom = shape(f['geometry'])
            geometries.append(mapping(transform(tr, geom.simplify(20, preserve_topology=True))))
    return {'type': 'Feature', 'id': str(year), 'properties': {'year': year},
            'geometry': {'type': 'GeometryCollection', 'geometries': geometries}}

def main():
    out = ROOT / 'data'; out.mkdir(exist_ok=True)
    data = {'unit': 'km²', 'source': 'Informe final — Mocho 2025–2026, Figura 4, p. 19; Anexo 2, Variaciones de glaciares 2025–2026.',
            'glacier': series('Gl Mocho', 'glacier'), 'icecap': series('Capa de hielo Mocho Choshuenco', 'icecap')}
    (out / 'glacier-variations.json').write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    maps = {'type': 'FeatureCollection', 'features': [], 'availableYears': [2025, 2026],
            'missingYears': [1976, 1986, 2000, 2005, 2015, 2017, 2020, 2022, 2023, 2024],
            'source': 'Anexo 2 · polígonos verificados de 2025 y 2026; las otras geometrías históricas no están en el anexo publicado.'}
    maps['features'].append(polygon(SRC / '2_Polígonos/2025/Surface 2025_m.geojson', 2025))
    maps['features'].append(polygon(SRC / '2_Polígonos/2026/Surface2026.geojson', 2026))
    (out / 'icecap-history.geojson').write_text(json.dumps(maps, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    image = next((SRC / '1_Imágenes').glob('*2026*False_color.tiff'))
    with rasterio.open(image) as src:
        affine, width, height = calculate_default_transform(src.crs, 'EPSG:3857', src.width, src.height, *src.bounds)
        rgb = np.zeros((3, height, width), dtype=np.uint8)
        for i in range(3):
            reproject(rasterio.band(src, i + 1), rgb[i], src_transform=src.transform, src_crs=src.crs,
                      dst_transform=affine, dst_crs='EPSG:3857', resampling=Resampling.bilinear)
        alpha = np.where(rgb.max(axis=0) > 0, 255, 0).astype(np.uint8)
        Image.fromarray(np.dstack([rgb.transpose(1, 2, 0), alpha])).save(out / 'satellite-2026.webp', quality=86, method=6)
    print('Created variation series and compact 2025/2026 polygons')
if __name__ == '__main__': main()
