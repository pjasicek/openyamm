#!/usr/bin/env python3
"""LOD0 hands of the reduced GLB against the installed one: every source vertex with hand + finger weight > 0.5 must
exist at the same bind position (< 0.01 mm) with the same four weights (< 0.002), so the fitted sword grips are
unchanged (MM8 Centaur: fingers only, the palms were cut at 60 %; also the string and arrow). Usage: grip_check.py <installed.glb> <reduced.glb>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
FINGERS = ('thumb', 'index', 'middle', 'ring', 'pinky')


def lod0(path):
    d, b = read_glb(Path(path)); n = next(x for x in d['nodes'] if x.get('name') == 'Body')
    p = d['meshes'][n['mesh']]['primitives'][0]['attributes']
    get = lambda k: np.frombuffer(accessor_bytes(d, b, p[k]), {5121: np.uint8, 5123: np.uint16, 5126: np.float32}[d['accessors'][p[k]]['componentType']]).reshape(-1, 4 if k != 'POSITION' else 3)
    names = [d['nodes'][i]['name'] for i in d['skins'][n['skin']]['joints']]
    W = np.zeros((len(get('POSITION')), len(names)), np.float32)
    np.add.at(W, (np.arange(len(W))[:, None].repeat(4, 1), get('JOINTS_0').astype(int)), get('WEIGHTS_0'))
    return get('POSITION'), W, names


sp, sw, names = lod0(sys.argv[1]); cp, cw, _ = lod0(sys.argv[2])
for label, pred in (('finger', lambda n: any(k in n.lower() for k in FINGERS)), ('string/arrow', lambda n: n.startswith('String') or n == 'Arrow')):
  hand = sw[:, [i for i, n in enumerate(names) if pred(n)]].sum(1) > .5
  d, i = cKDTree(cp).query(sp[hand])
  wd = np.abs(sw[hand] - cw[i]).max(1)
  print('GRIP', label, 'vertices', int(hand.sum()), 'max position diff mm', round(float(d.max()) * 1000, 4),
        'weight diffs > 0.002:', int((wd > .002).sum()), 'max', round(float(wd.max()), 4))
