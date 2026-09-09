"""Prepare the glacier-velocity raster and stakes for the static dashboard."""
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
COLOR_MAX = 30.0
TICKS = [0, 5, 10, 15, 20, 25, 30]
RASTER_NAME = 'Vel_GPS202510-202604.tif'
STAKES_NAME = 'Vel anual balizas_Mocho2025-2026.geojson'
IMAGE_NAME = 'velocity-202510-202604.webp'
MANIFEST_NAME = 'velocity-2025-2026.json'


def corners_wgs84(dataset):
    pixel_corners = [(0, 0), (dataset.width, 0), (dataset.width, dataset.height), (0, dataset.height)]
    native = [dataset.transform * point for point in pixel_corners]
    transformer = Transformer.from_crs(dataset.crs, 'EPSG:4326', always_xy=True)
    return [[round(lon, 9), round(lat, 9)] for lon, lat in (transformer.transform(x, y) for x, y in native)]


def geojson_crs(data):
    name = data.get('crs', {}).get('properties', {}).get('name', '')
    match = re.search(r'(\d+)$', name)
    if not match:
        raise SystemExit('El GeoJSON de velocidad no declara un EPSG reconocible')
    return f'EPSG:{match.group(1)}'


def prepare_stakes(path):
    source = json.loads(path.read_text(encoding='utf-8'))
    source_crs = geojson_crs(source)
    transformer = Transformer.from_crs(source_crs, 'EPSG:4326', always_xy=True)
    features = []
    for feature in source.get('features', []):
        properties = feature.get('properties', {})
        coordinates = feature.get('geometry', {}).get('coordinates', [])
        if len(coordinates) < 2:
            continue
        source_name = str(properties.get('Nombre', '')).strip()
        if not source_name:
            raise SystemExit('Una baliza no tiene Nombre')
        velocity = float(properties['Vel_(m/a)'])
        lon, lat = transformer.transform(float(coordinates[0]), float(coordinates[1]))
        is_previous_b11 = source_name == 'B11_2024-2025'
        name = 'B11' if is_previous_b11 else source_name
        features.append({
            'type': 'Feature',
            'id': name,
            'properties': {
                'name': name,
                'sourceName': source_name,
                'period': '2024–2025' if is_previous_b11 else '2025–2026',
                'velocityMPerYear': round(velocity, 4),
            },
            'geometry': {'type': 'Point', 'coordinates': [round(lon, 9), round(lat, 9)]},
        })
    if len(features) != 10 or len({item['properties']['name'] for item in features}) != 10:
        raise SystemExit(f'Se esperaban 10 balizas únicas y se obtuvieron {len(features)}')
    return {'type': 'FeatureCollection', 'features': features}, source_crs


def prepare(source_dir, output_dir):
    raster_path = source_dir / RASTER_NAME
    stakes_path = source_dir / STAKES_NAME
    cmap = colormaps['rainbow']
    with rasterio.open(raster_path) as dataset:
        if dataset.count != 1 or dataset.crs is None:
            raise SystemExit('El raster de velocidad debe tener una banda y CRS definido')
        values = dataset.read(1, masked=True)
        valid_mask = ~np.ma.getmaskarray(values) & np.isfinite(values.filled(np.nan))
        valid_values = values.data[valid_mask]
        if not valid_values.size:
            raise SystemExit('El raster de velocidad no contiene píxeles válidos')
        scaled = np.clip((values.filled(COLOR_MIN) - COLOR_MIN) / (COLOR_MAX - COLOR_MIN), 0, 1)
        rgba = np.zeros((dataset.height, dataset.width, 4), dtype=np.uint8)
        rgba[valid_mask] = np.rint(cmap(scaled[valid_mask]) * 255).astype(np.uint8)
        rgba[~valid_mask, 3] = 0
        Image.fromarray(rgba, 'RGBA').save(output_dir / IMAGE_NAME, 'WEBP', lossless=True, method=6)
        image_coordinates = corners_wgs84(dataset)
        raster_crs = str(dataset.crs)
        raster_min = float(valid_values.min())
        raster_max = float(valid_values.max())
        valid_pixels = int(valid_values.size)

    stakes, stakes_crs = prepare_stakes(stakes_path)
    stops = []
    for index in range(13):
        color = np.rint(np.asarray(cmap(index / 12)[:3]) * 255).astype(np.uint8)
        stops.append('#' + ''.join(f'{channel:02x}' for channel in color))
    manifest = {
        'quantity': 'Velocidad superficial anualizada',
        'unit': 'm/a',
        'palette': 'rainbow',
        'period': {'start': '2025-10', 'end': '2026-04', 'label': 'OCT 2025–ABR 2026'},
        'colorScale': {'min': COLOR_MIN, 'max': COLOR_MAX, 'ticks': TICKS, 'stops': stops},
        'image': {
            'file': IMAGE_NAME,
            'imageCoordinates': image_coordinates,
            'source': f'data/Velocidad/{RASTER_NAME}',
            'sourceCrs': raster_crs,
            'rasterMin': raster_min,
            'rasterMax': raster_max,
            'validPixels': valid_pixels,
        },
        'stakes': stakes,
        'stakesSource': f'data/Velocidad/{STAKES_NAME}',
        'stakesSourceCrs': stakes_crs,
        'note': 'B11 corresponde al período 2024–2025; las otras nueve balizas corresponden a 2025–2026.',
    }
    (output_dir / MANIFEST_NAME).write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=ROOT / 'data' / 'Velocidad')
    parser.add_argument('--output', type=Path, default=ROOT / 'data')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = prepare(args.source, args.output)
    print(json.dumps({
        'image': result['image']['file'],
        'rasterRange': [result['image']['rasterMin'], result['image']['rasterMax']],
        'scale': result['colorScale'],
        'stakes': len(result['stakes']['features']),
    }, ensure_ascii=False))
