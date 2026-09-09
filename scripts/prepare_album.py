"""Prepare ordered, web-sized photographs for the people chapter."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
MAX_WIDTH = 2000
QUALITY = 86
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.webp'}


def ordered_sources(source_dir):
    files = [path for path in source_dir.iterdir() if path.is_file() and path.suffix.lower() in EXTENSIONS]
    try:
        return sorted(files, key=lambda path: int(path.stem))
    except ValueError as error:
        raise SystemExit('Las fotos del álbum deben tener nombres numéricos para conservar su orden') from error


def prepare(source_dir, output_dir):
    files = ordered_sources(source_dir)
    if not files:
        raise SystemExit(f'No se encontraron fotos en {source_dir}')
    photographs = []
    for index, path in enumerate(files, start=1):
        output_name = f'album-{index:02d}.webp'
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert('RGB')
            if image.width > MAX_WIDTH:
                height = round(image.height * MAX_WIDTH / image.width)
                image = image.resize((MAX_WIDTH, height), Image.Resampling.LANCZOS)
            image.save(output_dir / output_name, 'WEBP', quality=QUALITY, method=6)
            photographs.append({
                'order': index,
                'src': output_name,
                'width': image.width,
                'height': image.height,
            })
    manifest = {
        'count': len(photographs),
        'maxWidth': MAX_WIDTH,
        'format': 'WebP',
        'photographs': photographs,
        'source': 'data/album/',
    }
    (output_dir / 'album.json').write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=ROOT / 'data' / 'album')
    parser.add_argument('--output', type=Path, default=ROOT / 'data')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = prepare(args.source, args.output)
    print(json.dumps({'count': result['count'], 'files': [item['src'] for item in result['photographs']]}, ensure_ascii=False))
