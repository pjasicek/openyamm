"""work/r55_lod0.glb -> work/r55_lods.glb with LOD1-3 and shadow LODs at 0.5 / 0.25 / 0.11 and 4 influences (2,895 /
1,447 / 636, at or below the installed 5,263 / 1,893 / 630; the production ratios 0.5 / 0.18 / 0.06 on the smaller
LOD0 gave a blocky 346-triangle LOD3). Protected points: the crown (top 3 cm), the outer hand tips (3 cm at either x
extreme), the rest floor contact (under 1 cm) and the posed floor contacts of every clip (floor_contacts.py). Without
them LOD3 came out 5 cm lower and 13 cm narrower (the picking bounds use the coarsest LOD) and dipped 25 mm under the
floor. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
import numpy as np
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate, read_glb, accessor_bytes  # noqa: E402
doc, binary = read_glb(P / 'work/r55_lod0.glb')
prim = next(m for m in doc['meshes'] if m['name'] == 'Body')['primitives'][0]
pos = np.frombuffer(accessor_bytes(doc, binary, prim['attributes']['POSITION']), np.float32).reshape(-1, 3)
z_up = np.stack([pos[:, 0], -pos[:, 2], pos[:, 1]], 1)   # glTF Y up -> Blender Z up
keep = (z_up[:, 2] < .01) | (z_up[:, 2] > z_up[:, 2].max() - .03) | (z_up[:, 0] > z_up[:, 0].max() - .03) | (z_up[:, 0] < z_up[:, 0].min() + .03)
import json  # noqa: E402
points = [tuple(map(float, p)) for p in np.unique(np.concatenate([z_up[keep].round(6), json.load(open(P / 'work/floor_contacts.json'))]), axis=0)]
print('PROTECTED', len(points))
generate(P / 'work/r55_lod0.glb', P / 'work/r55_lods.glb', 'Body', ratios=(.5, .25, .11), max_influences=4,
         protected_points=points)
