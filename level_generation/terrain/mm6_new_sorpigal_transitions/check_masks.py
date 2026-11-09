"""Check candidate mask format, corner coverage and shared material coverage at observed joins.

This is a structural gate only. It cannot certify visual quality or engine sampling.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parent
MATERIALS = ['dirt', 'grass', 'volcano', 'cobbles']
BASES = {'6dirttyl': 'dirt', '6grastyl': 'grass', '6voltyl': 'volcano'}


def edge(array, side):
    return {'N': array[0], 'S': array[-1], 'E': array[:, -1], 'W': array[:, 0]}[side]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('masks', type=Path, help='Directory containing 33 native-name PNG masks at 512px')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    inventory = json.loads((PROJECT / 'mask_inventory.json').read_text())['masks']
    pairs = json.loads((PROJECT / 'adjacency_constraints.json').read_text())['pairs']
    images, failures, hashes = {}, [], {}
    for record in inventory:
        name = record['tile']
        path = args.masks / f'{name}.png'
        if not path.is_file():
            failures.append({'tile': name, 'reason': 'missing'})
            continue
        with Image.open(path) as image:
            rgba = np.asarray(image.convert('RGBA'))
            if image.size != (512, 512) or not np.all(rgba[:, :, 3] == 255):
                failures.append({'tile': name, 'reason': 'must be 512x512 and opaque'})
                continue
            if not (np.array_equal(rgba[:, :, 0], rgba[:, :, 1]) and
                    np.array_equal(rgba[:, :, 0], rgba[:, :, 2])):
                failures.append({'tile': name, 'reason': 'must be grayscale, not coloured material art'})
                continue
            images[name] = image.convert('L')
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        a = np.asarray(images[name])
        for (y, x), expected in zip([(0, 0), (0, -1), (-1, -1), (-1, 0)], record['corners_NW_NE_SE_SW']):
            target = 0 if expected == 'dirt' else 255
            if abs(int(a[y, x]) - target) > 1:
                failures.append({'tile': name, 'reason': 'corner coverage disagrees with reviewed topology',
                                 'corner_yx': [y, x], 'actual': int(a[y, x]), 'expected': target})
    checks = []
    for size in (512, 256):
        weights = {}
        for name, material in BASES.items():
            array = np.zeros((size, size, 4), dtype=np.float32)
            array[:, :, MATERIALS.index(material)] = 255
            weights[name] = array
        for record in inventory:
            name = record['tile']
            if name not in images:
                continue
            a = np.asarray(images[name].resize((size, size), Image.Resampling.LANCZOS), dtype=np.float32)
            array = np.zeros((size, size, 4), dtype=np.float32)
            array[:, :, 0] = 255-a
            array[:, :, MATERIALS.index(record['white'])] = a
            weights[name] = array
        for pair in pairs:
            if pair['topology_conflict'] or pair['a'] not in weights or pair['b'] not in weights:
                continue
            delta = np.abs(edge(weights[pair['a']], pair['side_a']) - edge(weights[pair['b']], pair['side_b']))
            result = {'pair': pair['id'], 'size': size, 'max_coverage_difference_255': float(delta.max()),
                      'pass': bool(delta.max() <= 1)}
            checks.append(result)
            if not result['pass']:
                failures.append({'reason': 'shared material edge coverage differs', **result})
    result = {'status': 'structural_fail' if failures else 'structural_pass_visual_review_required',
              'mask_hashes': hashes, 'failures': failures, 'edge_checks': checks,
              'excluded_source_conflicts': [p['id'] for p in pairs if p['topology_conflict']],
              'limits': 'Does not certify interior silhouette, composited RGB, repeat patterns, mipmaps or in-game seams.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'], f'({len(failures)} failures, {len(checks)} edge checks)')
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__':
    main()
