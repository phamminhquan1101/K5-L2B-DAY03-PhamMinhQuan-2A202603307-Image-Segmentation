"""Measure actual point inference without writing annotations to any CVAT task."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import time
import urllib.request

import numpy as np
from PIL import Image, ImageDraw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--point', type=float, nargs=2, action='append', required=True)
    parser.add_argument('--negative', type=float, nargs=2, action='append', default=[])
    parser.add_argument('--url', help='Nuclio function URL; omit for in-process inference')
    parser.add_argument('--repeat', type=int, default=3)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    image_bytes = args.image.read_bytes()
    if not args.url:
        from model_handler import ModelHandler
        model = ModelHandler()
    payload = {'image': base64.b64encode(image_bytes).decode(),
               'pos_points': args.point, 'neg_points': args.negative}
    runs = []
    for index in range(args.repeat):
        started = time.perf_counter()
        if args.url:
            request = urllib.request.Request(args.url, data=json.dumps(payload).encode(),
                                             headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(request, timeout=90) as response:
                result = json.load(response)
        else:
            result = model.handle(image_bytes, args.point, args.negative)
        if not result['shapes']:
            raise RuntimeError('Model returned an empty mask')
        points = result['shapes'][0]['points']
        left, top, right, bottom = points[-4:]
        runs_rle = points[:-4]
        pixels = np.repeat(np.arange(len(runs_rle)) % 2, runs_rle).astype(bool)
        width, height = right - left + 1, bottom - top + 1
        if pixels.size != width * height:
            raise RuntimeError('Invalid CVAT RLE dimensions')
        full = np.zeros((result['meta']['height'], result['meta']['width']), dtype=bool)
        full[top:bottom + 1, left:right + 1] = pixels.reshape(height, width)
        if not full.any():
            raise RuntimeError('Decoded mask is empty')
        runs.append({'run': index + 1, 'round_trip_ms': round((time.perf_counter() - started) * 1000, 2),
                     **result['meta'], 'bounds': points[-4:], 'rle_foreground_pixels': int(full.sum())})
    with Image.open(args.image) as source:
        original = source.convert('RGBA')
    layer = np.zeros((original.height, original.width, 4), dtype=np.uint8)
    layer[full] = [0, 160, 255, 110]
    overlay = Image.alpha_composite(original, Image.fromarray(layer))
    drawing = ImageDraw.Draw(overlay)
    for values, color in ((args.point, '#00ff00'), (args.negative, '#ff3333')):
        for x, y in values:
            drawing.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color, outline='white', width=2)
    overlay.convert('RGB').save(args.output / 'point-mask-overlay.jpg', quality=92)
    report = {'image': args.image.name, 'image_sha256': hashlib.sha256(image_bytes).hexdigest(),
              'positive_points': args.point, 'negative_points': args.negative,
              'mode': 'nuclio_http' if args.url else 'in_process', 'runs': runs,
              'note': 'Technical inference test; no ground-truth accuracy or manual productivity comparison.'}
    (args.output / 'smoke-test.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
