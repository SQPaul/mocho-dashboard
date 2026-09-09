"""Prepare transparent, georeferenced GPR overlays for the static dashboard."""
import argparse
import json
import re
from pathlib import Path

import numpy as np
import rasterio
from matplotlib import colormaps
from PIL import Image
from pyproj import Transformer


ROOT = Path(__file__).resolve().parents[1]
COLOR_MIN = 0.0
COLOR_MAX = 17.0
SUMMARY = [
    {'label': 'Oct 2021', 'n': 14295, 'distanceKm': 7.30, 'meanM': 5.02, 'stdM': 0.73, 'minM': 3.08, 'maxM': 7.18},
    {'label': 'Oct 2022', 'n': 4176, 'distanceKm': 7.54, 'meanM': 7.34, 'stdM': 1.85, 'minM': 4.10, 'maxM': 13.89},
    {'label': 'Oct 2023', 'n': 26961, 'distanceKm': 13.30, 'meanM': 7.14, 'stdM': 1.79, 'minM': 0.21, 'maxM': 13.70},
    {'label': 'Oct 2024', 'n': 28397, 'distanceKm': 14.18, 'meanM': 9.13, 'stdM': 2.61, 'minM': 1.06, 'maxM': 17.11},
    {'label': 'Oct 2025', 'n': 19467, 'distanceKm': 9.90, 'meanM': 5.05, 'stdM': 0.89, 'minM': 3.14, 'maxM': 8.77},
]


def corners_wgs84(dataset):
    pixel_corners = [(0, 0), (dataset.width, 0), (dataset.width, dataset.height), (0, dataset.height)]
    native = [dataset.transform * point for point in pixel_corners]
    transformer = Transformer.from_crs(dataset.crs, 'EPSG:4326', always_xy=True)
    return [[round(lon, 9), round(lat, 9)] for lon, lat in (transformer.transform(x, y) for x, y in native)]


def prepare(source_dir, output_dir):
    cmap = colormaps['Blues']
    campaigns = []
    files = sorted(source_dir.glob('GPR_*.tif'))
    if len(files) != 5:
        raise SystemExit(f'Se esperaban 5 GeoTIFF GPR y se encontraron {len(files)} en {source_dir}')

    for path in files:
        match = re.fullmatch(r'GPR_(\d{2})(\d{2})(\d{4})\.tif', path.name)
        if not match:
            raise SystemExit(f'Nombre GPR no reconocido: {path.name}')
        day, month, year = match.groups()
        with rasterio.open(path) as dataset:
            values = dataset.read(1, masked=True)
            mask = ~np.ma.getmaskarray(values) & np.isfinite(values.filled(np.nan))
            scaled = np.clip((values.filled(COLOR_MIN) - COLOR_MIN) / (COLOR_MAX - COLOR_MIN), 0, 1)
            rgba = np.zeros((dataset.height, dataset.width, 4), dtype=np.uint8)
            rgba[mask] = np.rint(cmap(scaled[mask]) * 255).astype(np.uint8)
            rgba[~mask, 3] = 0
            output_name = f'gpr-{year}.webp'
            Image.fromarray(rgba, 'RGBA').save(output_dir / output_name, 'WEBP', lossless=True, method=6)
            valid = values.compressed()
            campaigns.append({
                'year': int(year),
                'date': f'{year}-{month}-{day}',
                'label': f'{day} OCT {year}',
                'image': output_name,
                'imageCoordinates': corners_wgs84(dataset),
                'source': f'data/GPR/{path.name}',
                'sourceCrs': str(dataset.crs),
                'rasterMin': float(valid.min()),
                'rasterMax': float(valid.max()),
                'validPixels': int(valid.size),
            })

    stops = []
    for index in range(9):
        color = np.rint(np.asarray(cmap(index / 8)[:3]) * 255).astype(np.uint8)
        stops.append('#' + ''.join(f'{channel:02x}' for channel in color))
    manifest = {
        'unit': 'm',
        'palette': 'Blues',
        'colorScale': {'min': COLOR_MIN, 'max': COLOR_MAX, 'ticks': [0, 3, 6, 9, 12, 15, 17], 'stops': stops},
        'defaultYear': 2025,
        'campaigns': campaigns,
        'summary': SUMMARY,
        'summarySource': 'data/GPR/Tabla_resumen_GPR.png',
    }
    (output_dir / 'gpr-campaigns.json').write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=ROOT / 'data' / 'GPR')
    parser.add_argument('--output', type=Path, default=ROOT / 'data')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = prepare(args.source, args.output)
    print(json.dumps({'campaigns': len(result['campaigns']), 'years': [item['year'] for item in result['campaigns']], 'scale': result['colorScale']}, ensure_ascii=False))
