"""work/r55_lod0.glb -> export/mm8_m564_lods.glb with LOD1-3 and shadow LODs, the same ratios and influence budget as
mm8_m564_claude/scripts/build_lods.py (0.5 / 0.25 / 0.125, 4 influences). The horn tips are protected (vertices within
KEEP_R of each horn's forward tip): unprotected, LOD3 lost 4 cm of both horns (front bound -0.478 -> -0.439 m).
Usage: blender -b -P build_lods.py   Then shrink_shadow_lods.py (as the m564 build) and carry_variants.py."""
import os
from pathlib import Path
import sys
import numpy as np
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools')); sys.path.insert(0, str(P / 'scripts'))
from build_actor_lods import generate  # noqa: E402
from glbmesh import read_glb, acc  # noqa: E402
KEEP_R = float(os.environ.get('KEEP_R', '0.02'))
d, b = read_glb(P / 'work/r55_lod0.glb')
node = next(n for n in d['nodes'] if n.get('name') == 'Gorgon')
g = acc(d, b, d['meshes'][node['mesh']]['primitives'][0]['attributes']['POSITION']).astype(float)
v = np.unique(np.round(np.c_[g[:, 0], -g[:, 2], g[:, 1]], 6), axis=0)     # glTF Y-up -> Blender Z-up
points = []
for side in (v[:, 0] < 0, v[:, 0] > 0):
    s = v[side & (v[:, 2] > .3)]; tip = s[np.argmin(s[:, 1])]                 # the gorgon faces -Y
    points += [tuple(p) for p in s[np.linalg.norm(s - tip, axis=1) < KEEP_R]]
print('PROTECTED horn tip vertices', len(points))
generate(P / 'work/r55_lod0.glb', P / 'export/mm8_m564_lods.glb', 'Gorgon', ratios=(.5, .25, .125), max_influences=4,
         protected_points=points)
