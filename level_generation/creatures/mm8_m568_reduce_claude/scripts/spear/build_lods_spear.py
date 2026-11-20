"""work/r76_lod0_spear.glb (reduced LOD0 with the Raven-style clips) -> export/mm8_m568_lods.glb, as ../build_lods.py
(0.5 / 0.25 / 0.125, 4 influences) but with the LOD0 vertices within 8 cm of both armpits kept in every level: with
the new shoulder swing a long LOD2 face from the chest to the upper arm stretched 22x in Fidget and Hit.
Usage: blender -b -P build_lods_spear.py"""
from pathlib import Path
import sys
import numpy as np
P = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(P.parents[2] / 'tools')); sys.path.insert(0, str(Path(__file__).parent))
from build_actor_lods import generate  # noqa: E402
from gltf_pose import Gltf  # noqa: E402
g = Gltf(P / 'work/r76_lod0_spear.glb'); node = g.doc['nodes'][g.names['Body']]
pos = np.concatenate([g.acc(p['attributes']['POSITION']) for p in g.doc['meshes'][node['mesh']]['primitives']])
pos = np.stack([pos[:, 0], -pos[:, 2], pos[:, 1]], 1)  # glTF Y-up -> Blender Z-up
keep = np.zeros(len(pos), bool)
for c in ([.33, .02, 1.51], [-.33, .02, 1.51]):
    keep |= np.linalg.norm(pos - c, axis=1) < .08
pts = [tuple(map(float, p)) for p in np.unique(np.round(pos[keep], 6), axis=0)]
print('PROTECTED armpit vertices', len(pts))
from mathutils import Vector  # noqa: E402
generate(P / 'work/r76_lod0_spear.glb', P / 'export/mm8_m568_lods.glb', 'Body', ratios=(.5, .25, .125), max_influences=4,
         protected_points=[Vector(p) for p in pts])
