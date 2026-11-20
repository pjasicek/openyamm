#!/usr/bin/env python3
"""LOD0 hands of the reduced GLB against the installed one: every source vertex with hand + finger weight > 0.5 must
exist at the same bind position (< 0.01 mm) with the same four weights (< 0.002), so the fitted bow grip and the string draw are
unchanged. Usage: grip_check.py <installed.glb> <reduced.glb> [mesh node, default Body]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
FINGERS = ('thumb', 'index', 'middle', 'ring', 'pinky', 'Finger')  # MM8 Dark Elf warrior: B_L_Finger01 ...
NODE = sys.argv[3] if len(sys.argv) > 3 else 'Body'


def lod0(path):
    d, b = read_glb(Path(path)); n = next(x for x in d['nodes'] if x.get('name') == NODE)
    p = d['meshes'][n['mesh']]['primitives'][0]['attributes']
    get = lambda k: np.frombuffer(accessor_bytes(d, b, p[k]), {5121: np.uint8, 5123: np.uint16, 5126: np.float32}[d['accessors'][p[k]]['componentType']]).reshape(-1, 4 if k != 'POSITION' else 3)
    names = [d['nodes'][i]['name'] for i in d['skins'][n['skin']]['joints']]
    W = np.zeros((len(get('POSITION')), len(names)), np.float32)
    np.add.at(W, (np.arange(len(W))[:, None].repeat(4, 1), get('JOINTS_0').astype(int)), get('WEIGHTS_0'))
    return get('POSITION'), W, names


sp, sw, names = lod0(sys.argv[1]); cp, cw, _ = lod0(sys.argv[2])
hand = sw[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or any(k in n for k in FINGERS)]].sum(1) > .5
d, i = cKDTree(cp).query(sp[hand])
wd = np.abs(sw[hand] - cw[i]).max(1)
print('GRIP hand vertices', int(hand.sum()), 'max position diff mm', round(float(d.max()) * 1000, 4),
      'weight diffs > 0.002:', int((wd > .002).sum()), 'max', round(float(wd.max()), 4))
