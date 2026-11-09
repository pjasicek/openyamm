#!/usr/bin/env python3
"""Remove retained magenta extraction matte from pending 2× UI controls."""

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
        raise ValueError('No visible control artwork')
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def main():
    catalog = json.loads((REVIEW / 'catalog.js').read_text().split('=', 1)[1].strip().removesuffix(';'))
    report_path = HERE / 'report.json'
    records = json.loads(report_path.read_text())['items'] if report_path.is_file() else {}
    count = 0
    for card in catalog['items']:
        if not card['name'].startswith(('context_', 'resume_', 'interact_')):
            continue
        old = next((option for option in card['candidates']
                    if option['origin'] == 'Second-pass selection'), None)
        if old is None:
            continue
        input_path = REVIEW / old['path']
        with Image.open(input_path) as image:
            rgba = image.convert('RGBA')
            pixels = np.asarray(rgba)
        matte = ((pixels[:, :, 0] >= 248) & (pixels[:, :, 1] <= 8) &
                 (pixels[:, :, 2] >= 248) & (pixels[:, :, 3] >= 240))
        if matte.mean() <= .05:
            continue
        if digest(REVIEW / card['source']) != card['source_sha256']:
            raise ValueError(f'Changed native source: {card["id"]}')
        cleaned, parameters = extract(rgba.convert('RGB'))
        native = Image.open(REVIEW / card['original']).convert('RGBA')
        native_box = bbox(native.getchannel('A'))
        subject_box = bbox(cleaned.getchannel('A'))
        desired = (2 * (native_box[2] - native_box[0]), 2 * (native_box[3] - native_box[1]))
        sampling = ((subject_box[2] - subject_box[0]) / desired[0],
                    (subject_box[3] - subject_box[1]) / desired[1])
        if max(sampling) / min(sampling) > 1.25:
            raise ValueError(f'Distorted control for {card["id"]}: {sampling}')
        crop = cleaned.crop(subject_box).convert('RGBa').resize(desired, Image.Resampling.LANCZOS).convert('RGBA')
        output = Image.new('RGBA', tuple(card['x2_size']), (0, 0, 0, 0))
        output.alpha_composite(crop, (native_box[0] * 2, native_box[1] * 2))
        path = HERE / 'cutouts' / (card['id'] + '.png')
        path.parent.mkdir(exist_ok=True)
        output.save(path)
        records[card['id']] = {
            'status': 'candidate_technical', 'source_sha256': card['source_sha256'],
            'master': old['path'], 'master_sha256': old['sha256'],
            'artifact': str(path.relative_to(REVIEW)), 'artifact_sha256': digest(path),
            'origin': 'Cleaned UI control cutout',
            'method': 'spatial magenta-matte unmix; premultiplied native-bbox fit',
            'native_subject': native_box, 'returned_subject': subject_box, 'fit_scale': sampling,
            'matte_ratio_before': round(float(matte.mean()), 5), 'cleanup': parameters,
            'visual_status': 'pending_manual_review',
        }
        count += 1
    if count != 27:
        raise ValueError(f'Expected 27 unclean control returns, found {count}')
    report_path.write_text(json.dumps({'schema': 1, 'items': records}, indent=2) + '\n')
    print(f'Cleaned and fitted {count} magenta-matte controls')


if __name__ == '__main__':
    main()
