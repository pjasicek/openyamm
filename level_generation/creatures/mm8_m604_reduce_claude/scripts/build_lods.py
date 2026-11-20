"""work/r75_lod0.glb -> work/r75_lods.glb with LOD1-3 and shadow LODs, the same ratios and influence budget as
mm8_m604_claude/scripts/build_lods.py (0.5 / 0.25 / 0.125, 4 influences). Vertices within 2 cm of each bounding
extreme (crown, back, front, sides, soles) are protected: the unprotected LOD3 lost 1 cm at the crown and the back,
and picking bounds use the coarsest LOD. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
import bpy
import numpy as np
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
src = P / 'work/r75_lod0.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src))
o = bpy.data.objects['EtherKnight']
co = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
pick = np.zeros(len(co), bool)
for k in range(3):
    pick |= co[:, k] > co[:, k].max() - .02
    pick |= co[:, k] < co[:, k].min() + .02
points = [tuple(p) for p in co[pick]]
print('PROTECTED', len(points), 'extreme vertices')
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(src, P / 'work/r75_lods.glb', 'EtherKnight', ratios=(.5, .25, .125), max_influences=4, protected_points=points)
