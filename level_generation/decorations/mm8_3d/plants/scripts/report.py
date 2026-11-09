#!/usr/bin/env python3
"""Markdown table rows and suggested decorations.yml bindings for built models (work/<id>/stats.json).
Binding height = the inventory height (sprite pixels x DSFT scale), except models listed in HEIGHT (flat lily pads:
their real height, so the pad keeps the sprite's width). lod_pixels by size. Usage: report.py ids..."""
import json, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
INV = {e['name']: e for e in json.load(open(os.path.join(ROOT, 'level_generation/decorations/mm8_3d/inventory.json')))}
UNITS = 81.7
SHARED = {'plant08': 'plant02'}           # near-identical sprites bound to one model
Z_OFFSET = {'plant43': -2, 'plant44': -2, 'plant46': -2, 'plant47': -2, 'plant50': -2, 'plant51': -2,
            'plant52': -2, 'plant53': -2, 'plant54': -2}
JITTER = {'plant37': 0.1, 'plant38': 0.1, 'plant52': 0.1, 'plant53': 0.1, 'plant54': 0.1}


def binding(sid):
    model_id = SHARED.get(sid, sid)
    st = json.load(open(os.path.join(HERE, 'work', model_id, 'stats.json')))
    e = INV[sid]
    h = e['height']
    if sid in ('plant37', 'plant38'):
        # flat on the water: scale so the model's width matches the sprite's width
        lo, hi = st['bounds_min'], st['bounds_max']
        w = max(hi[0] - lo[0], hi[2] - lo[2])
        h = max(1, round(e['width'] / UNITS * st['lod0_height'] / w * UNITS))
    lod = [300, 120, 60] if h < 90 else ([400, 170, 70] if h < 170 else [500, 200, 80])
    lines = [f'  - name: {sid}', f'    model: engine/models/mm8_deco_{model_id}.glb', f'    height: {h}',
             f'    height_jitter: {JITTER.get(sid, 0.15)}']
    if sid in Z_OFFSET:
        lines.append(f'    z_offset: {Z_OFFSET[sid]}')
    lines.append(f'    lod_pixels: {lod}')
    return '\n'.join(lines), st, model_id


if __name__ == '__main__':
    rows, yaml = [], []
    for sid in sys.argv[1:]:
        y, st, mid = binding(sid)
        yaml.append(y)
        e = INV[sid]
        runtime = os.path.join(ROOT, 'assets_dev/engine/models', f'mm8_deco_{mid}.glb')
        rt = f'{os.path.getsize(runtime) / 1e3:.0f} KB' if os.path.exists(runtime) else 'not installed'
        rows.append(f'| `{sid}` | {e["hint"]} | {e["outdoor"]} | `mm8_deco_{mid}.glb` | '
                    f'{" / ".join(str(t) for t in st["triangles"])} | {st["bytes"] / 1e6:.1f} MB | {rt} | '
                    f'`review/{mid}/compare.png` |')
    print('\n'.join(rows))
    print()
    print('\n'.join(yaml))
