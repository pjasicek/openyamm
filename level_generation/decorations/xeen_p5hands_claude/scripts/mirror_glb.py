#!/usr/bin/env python3
"""Mirror a static decoration GLB across model X (the left stone hand from the right one): positions and normals
negate x, every triangle's winding reverses, UVs and textures stay (the engine's normal-map tangent frame comes from
screen derivatives with the sign divided out, so a mirrored use of the same normal map shades correctly). Node and mesh
names get the new stem. mirror_glb.py <in.glb> <out.glb> <new name>"""
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'level_generation/creatures/claude_shared/floor'))
from glb_pose import Glb  # noqa: E402
src, dst, name = sys.argv[1:4]
g = Glb(src)
j = g.json
COMP = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}


def view(index):
    acc = j['accessors'][index]
    bv = j['bufferViews'][acc['bufferView']]
    dt = np.dtype(COMP[acc['componentType']])
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[acc['type']]
    start = bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
    stride = bv.get('byteStride', 0) or dt.itemsize * width
    return np.ndarray((acc['count'], width), dtype=dt, buffer=g.bin, offset=start, strides=(stride, dt.itemsize))


done = set()
for mesh in j['meshes']:
    for p in mesh['primitives']:
        for key in ('POSITION', 'NORMAL'):
            a = p['attributes'].get(key)
            if a is not None and a not in done:
                done.add(a)
                v = view(a)
                v[:, 0] = -v[:, 0]
                if key == 'POSITION':
                    acc = j['accessors'][a]
                    acc['min'][0], acc['max'][0] = -acc['max'][0], -acc['min'][0]
        ia = p.get('indices')
        if ia is not None and ('i', ia) not in done:
            done.add(('i', ia))
            f = view(ia).reshape(-1, 3)
            f[:] = f[:, ::-1].copy()
    if mesh.get('name', '').startswith('xeen_deco_stonehand_r'):
        mesh['name'] = mesh['name'].replace('xeen_deco_stonehand_r', name)
for n in j['nodes']:
    if n.get('name', '').startswith('xeen_deco_stonehand_r'):
        n['name'] = n['name'].replace('xeen_deco_stonehand_r', name)
g.write(dst)
print('WROTE', dst)
