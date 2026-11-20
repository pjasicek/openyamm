#!/usr/bin/env python3
"""Fit the six transparent returned hourglass cells to native icon anchors."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
MASTER = HERE / 'newglas-2x3-transparent-master.png'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bbox(alpha, threshold=16):
    ys, xs = np.nonzero(np.asarray(alpha) >= threshold)
    if not len(xs):
        raise ValueError('Empty foreground')
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def main():
    catalog = json.loads((REVIEW / 'catalog.js').read_text().split('=', 1)[1].strip().removesuffix(';'))
    cards = {item['id']: item for item in catalog['items']}
    with Image.open(MASTER) as image:
        if image.size != (1024, 1536) or image.mode != 'RGBA':
            raise ValueError('Changed six-frame transparent master')
        if image.getchannel('A').getextrema()[0] != 0:
            raise ValueError('Missing transparent background')
        master = image.copy()
    report_path = HERE / 'report.json'
    records = json.loads(report_path.read_text())['items'] if report_path.is_file() else {}
    for index in range(6):
        key = f'engine--icons--newglas{index + 1}.bmp'
        card = cards[key]
        if digest(REVIEW / card['source']) != card['source_sha256']:
            raise ValueError(f'Changed native source: {key}')
        with Image.open(REVIEW / card['original']) as image:
            target_box = bbox(image.getchannel('A'))
        cell_box = ((index % 2) * 512, (index // 2) * 512,
                    (index % 2 + 1) * 512, (index // 2 + 1) * 512)
        cell = master.crop(cell_box)
        subject_box = bbox(cell.getchannel('A'), 32)
        if min(subject_box[0], subject_box[1]) < 20 or max(subject_box[2], subject_box[3]) > 492:
            raise ValueError(f'Subject touches cell edge: {key}')
        source_size = (target_box[2] - target_box[0], target_box[3] - target_box[1])
        sampling = ((subject_box[2] - subject_box[0]) / source_size[0],
                    (subject_box[3] - subject_box[1]) / source_size[1])
        if min(sampling) < 2 or max(sampling) / min(sampling) > 1.25:
            raise ValueError(f'Insufficient/distorted master for {key}: {sampling}')
        crop = cell.crop(subject_box).convert('RGBa').resize(
            (source_size[0] * 2, source_size[1] * 2), Image.Resampling.LANCZOS).convert('RGBA')
        candidate = Image.new('RGBA', tuple(card['x2_size']), (0, 0, 0, 0))
        candidate.alpha_composite(crop, (target_box[0] * 2, target_box[1] * 2))
        output = HERE / f'newglas{index + 1}-2x.png'
        candidate.save(output)
        records[key] = {
            'status': 'candidate_technical', 'source_sha256': card['source_sha256'],
            'master': str(MASTER.relative_to(REVIEW)), 'master_sha256': digest(MASTER),
            'artifact': str(output.relative_to(REVIEW)), 'artifact_sha256': digest(output),
            'origin': 'Transparent small-hourglass restoration',
            'method': 'transparent six-frame imagegen master, native alpha-bbox placement',
            'sampling': sampling, 'master_cell': cell_box, 'master_subject': subject_box,
            'native_subject': target_box, 'visual_status': 'pending_manual_review',
        }
    report_path.write_text(json.dumps({'schema': 1, 'items': records}, indent=2) + '\n')
    print('Prepared six transparent small hourglass frames')


if __name__ == '__main__':
    main()
