#!/usr/bin/env python3
"""Unmix cyan extraction backing on two small pending UI indicators."""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
ROOT = REVIEW.parents[2]
sys.path.insert(0, str(ROOT / 'level_generation/creatures/mm6_goblin/direct_ai_attack'))
from clean_edges import extract  # noqa: E402


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bbox(alpha, threshold=16):
    ys, xs = np.nonzero(np.asarray(alpha) >= threshold)
    if not len(xs):
        raise ValueError('Empty foreground')
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def unmix_cyan(image):
    source = np.asarray(image.convert('RGBA')).copy()
    rgb = source[:, :, :3].copy()
    rgb[source[:, :, 3] < 8] = (0, 255, 255)
    # The established edge cleaner estimates an opaque magenta matte. Exchanging
    # red and green converts this known cyan key into that same extraction case.
    converted = Image.fromarray(rgb[:, :, [1, 0, 2]])
    cleaned, parameters = extract(converted)
    output = np.asarray(cleaned).copy()
    output[:, :, :3] = output[:, :, [1, 0, 2]]
    output[:, :, 3] = np.minimum(output[:, :, 3], source[:, :, 3])
    return Image.fromarray(output), parameters


def main():
    catalog = json.loads((REVIEW / 'catalog.js').read_text().split('=', 1)[1].strip().removesuffix(';'))
    cards = {item['id']: item for item in catalog['items']}
    report_path = HERE / 'report.json'
    records = json.loads(report_path.read_text())['items'] if report_path.is_file() else {}
    for key in ('engine--icons--6pending.bmp', 'engine--icons--wizeye.bmp'):
        card = cards[key]
        if digest(REVIEW / card['source']) != card['source_sha256']:
            raise ValueError(f'Changed native source: {key}')
        old = next(option for option in card['candidates']
                   if option['origin'] == 'Measured retained-sheet extraction')
        cleaned, parameters = unmix_cyan(Image.open(REVIEW / old['path']))
        native = Image.open(REVIEW / card['original']).convert('RGBA')
        native_box = bbox(native.getchannel('A'))
        restored_box = bbox(cleaned.getchannel('A'))
        desired = (2 * (native_box[2] - native_box[0]), 2 * (native_box[3] - native_box[1]))
        crop = cleaned.crop(restored_box).convert('RGBa').resize(desired, Image.Resampling.LANCZOS).convert('RGBA')
        candidate = Image.new('RGBA', tuple(card['x2_size']), (0, 0, 0, 0))
        candidate.alpha_composite(crop, (native_box[0] * 2, native_box[1] * 2))
        output = HERE / 'cutouts' / (key + '.png')
        output.parent.mkdir(exist_ok=True)
        candidate.save(output)
        records[key] = {
            'status': 'candidate_technical', 'source_sha256': card['source_sha256'],
            'master': old['path'], 'master_sha256': old['sha256'],
            'artifact': str(output.relative_to(REVIEW)), 'artifact_sha256': digest(output),
            'origin': 'Cleaned cyan-backed indicator',
            'method': 'channel-permuted spatial key unmix; premultiplied native-bbox fit',
            'native_subject': native_box, 'returned_subject': restored_box,
            'cleanup': parameters, 'visual_status': 'pending_manual_review',
        }
    report_path.write_text(json.dumps({'schema': 1, 'items': records}, indent=2) + '\n')
    print('Cleaned two cyan-backed indicators')


if __name__ == '__main__':
    main()
