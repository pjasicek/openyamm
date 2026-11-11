#!/usr/bin/env python3
"""Line drawings of each split prop (work/<prop>/) at five times of a clip, front and side: work/preview_<prop>.png.
Usage: preview.py <prop> [clip]"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import prop_parts as pp  # noqa: E402


def triangles(doc, binary):
    out = []
    for prim in doc['meshes'][0]['primitives']:
        p = pp.array(doc, binary, prim['attributes']['POSITION'])
        out.append(p[pp.array(doc, binary, prim['indices']).reshape(-1, 3)])
    return np.concatenate(out)


def posed(doc, binary, clip, t):
    """LOD0 triangles of a one-node model at time t of clip (rest without it)."""
    node = doc['nodes'][0]
    tri = triangles(doc, binary)
    translation, rotation = node.get('translation', [0, 0, 0]), [0, 0, 0, 1]
    for animation in doc.get('animations', []):
        if animation['name'] != clip:
            continue
        for channel in animation['channels']:
            sampler = animation['samplers'][channel['sampler']]
            times = pp.array(doc, binary, sampler['input']).ravel()
            values = pp.array(doc, binary, sampler['output'])
            k = min(int(np.searchsorted(times, t)), len(times) - 1)
            if channel['target']['path'] == 'translation':
                translation = values[k]
            else:
                rotation = values[k]
    return tri @ pp.quat_matrix(rotation).T + translation


def main():
    prop = sys.argv[1]
    plan = next(p for p in json.loads((pp.HERE / 'work/plans.json').read_text()) if p['prop'] == prop)
    models = [pp.read_glb(Path(plan['body']))] + [pp.read_glb(Path(p['file'])) for p in plan['parts']]
    clips = [a['name'] for d, _ in models for a in d.get('animations', [])]
    clip = sys.argv[2] if len(sys.argv) > 2 else clips[0]
    duration = max(float(pp.array(d, b, s['input']).max()) for d, b in models for a in d.get('animations', [])
                   if a['name'] == clip for s in a['samplers'])
    frames = [[posed(d, b, clip, t) for d, b in models] for t in np.linspace(0, duration, 5)]
    every = np.concatenate([np.concatenate(f) for f in frames]).reshape(-1, 3)
    lo, hi = every.min(0), every.max(0)
    size = 240
    scale = 0.9 * size / (hi - lo).max()
    img = Image.new('RGB', (size * 5, size * 2), 'white')
    draw = ImageDraw.Draw(img, 'RGBA')
    colours = [(120, 120, 120, 70), (200, 110, 40, 90), (40, 110, 200, 90), (40, 160, 60, 90)]
    for k, frame in enumerate(frames):
        for row, (i, j) in enumerate([(0, 1), (2, 1)]):
            for m, tri in enumerate(frame):
                for t3 in tri:
                    pts = [(k * size + size / 2 + (p[i] - (lo[i] + hi[i]) / 2) * scale,
                            row * size + size / 2 - (p[j] - (lo[j] + hi[j]) / 2) * scale) for p in t3]
                    draw.polygon(pts, fill=colours[m % 4], outline=(0, 0, 0, 60))
    draw.text((4, 4), f'{prop} {clip} {duration:.2f}s', fill='black')
    img.save(pp.HERE / f'work/preview_{prop}.png')


if __name__ == '__main__':
    main()
