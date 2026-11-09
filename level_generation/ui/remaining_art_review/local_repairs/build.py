#!/usr/bin/env python3
"""Fit the two separately edited late hourglass frames to the frozen canvas."""

import hashlib
import json
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    catalog = json.loads((REVIEW / 'catalog.js').read_text().split('=', 1)[1].strip().removesuffix(';'))
    targets = {item['id']: item for item in catalog['items']}
    report_path = HERE / 'report.json'
    records = json.loads(report_path.read_text())['items'] if report_path.is_file() else {}
    for frame in ('08', '09'):
        key = f'engine--icons--ira-3_{frame}.bmp'
        card = targets[key]
        if digest(REVIEW / card['source']) != card['source_sha256']:
            raise ValueError(f'Changed native image: {key}')
        master_path = HERE / f'ira-3_{frame}-master.png'
        output = HERE / f'ira-3_{frame}-2x.png'
        with Image.open(master_path) as image:
            if image.width != image.height or image.width < card['x2_size'][0] * 2:
                raise ValueError(f'Insufficient/squashed master: {master_path}')
            if image.mode not in ('RGB', 'RGBA') or (image.mode == 'RGBA' and
                    image.getchannel('A').getextrema() != (255, 255)):
                raise ValueError(f'Expected full opaque wood background: {master_path}')
            image.convert('RGB').resize(tuple(card['x2_size']), Image.Resampling.LANCZOS).save(output)
        records[key] = {
            'status': 'candidate_technical', 'source_sha256': card['source_sha256'],
            'master': str(master_path.relative_to(REVIEW)), 'master_sha256': digest(master_path),
            'artifact': str(output.relative_to(REVIEW)), 'artifact_sha256': digest(output),
            'origin': 'Edited hourglass animation repair',
            'method': 'imagegen edit of native late hourglass, matched to prior restored wooden backing',
            'visual_status': 'pending_manual_review',
        }
    report_path.write_text(json.dumps({'schema': 1, 'items': records}, indent=2) + '\n')
    print('Prepared two edited late hourglass frames')


if __name__ == '__main__':
    main()
