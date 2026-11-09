#!/usr/bin/env python3
"""Table rows and suggested bindings for every finished rock (work/<rock>/mm8_deco_<rock>.glb): LOD triangles, file
size, scans, texture size, binding YAML (height = inventory height, z_offset sinks the base ~4 % into uneven
terrain, as the MM6 rocks). Usage: report.py [--yaml]"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
CFG = json.load(open(os.path.join(HERE, 'scripts', 'rocks.json')))
INV = {e['name']: e for e in json.load(open(os.path.join(HERE, '..', 'inventory.json')))}
ONE_OFF = {'rock65', 'rock68', 'rock69'}


def glb(path):
    raw = open(path, 'rb').read(); n = struct.unpack_from('<I', raw, 12)[0]; d = json.loads(raw[20:20 + n])
    base = next(x for x in d['nodes'] if 'mesh' in x)['mesh']
    chain = [base] + d['meshes'][base].get('extras', {}).get('openyamm_lods', [])
    tris = [sum(d['accessors'][p['indices']]['count'] // 3 for p in d['meshes'][i]['primitives']) for i in chain]
    return tris, len(raw), [m['name'] for m in d['materials']]


for rock in sorted(CFG):
    path = os.path.join(HERE, 'work', rock, f'mm8_deco_{rock}.glb')
    if not os.path.exists(path):
        continue
    inv = INV[rock]; cfg = CFG[rock]
    tris, size, mats = glb(path)
    installed = os.path.exists(os.path.join(REPO, 'assets_source', 'engine', 'models', f'mm8_deco_{rock}.glb'))
    if '--yaml' in sys.argv:
        # rune stones: plants grow from the base, so they sink less than the plain rocks
        z = -max(1, round(inv['height'] * (0.015 if rock in ONE_OFF else 0.04)))
        print(f"  - name: {rock}\n    model: engine/models/mm8_deco_{rock}.glb\n    height: {inv['height']}\n"
              f"    height_jitter: {0 if rock in ONE_OFF else 0.15}\n    z_offset: {z}")
    else:
        scans = ' + '.join(p['scan'] for p in cfg['parts'])
        res = cfg.get('texture_size', 1024 if inv['height'] >= 50 else 512 if inv['height'] >= 25 else 256)
        print(f"| `{rock}` | {inv['hint']}, h {inv['height']} w {inv['width']}, {inv['outdoor']} placed | {scans} | "
              f"{' / '.join(map(str, tris))} | {res} | {size / 1e6:.2f} MB | {'yes' if installed else 'no'} |")
