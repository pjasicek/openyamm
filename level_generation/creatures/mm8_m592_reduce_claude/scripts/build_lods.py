"""work/r78_lod0.glb -> work/r78_lods.glb with LOD1-3 and shadow LODs, the same ratios and influence budget as
mm8_m592_claude/scripts/build_lods.py (0.5 / 0.25 / 0.125, 4 influences). Protected: the Death/Dead floor contacts
(floor_contacts.py) and vertices within 2 cm of each bounding extreme (crown, claw tips, soles), as the m604 build.
Then shrink_shadow_lods.py and fix_lod_winding.py (the m592 project's) and carry_variants.py.
Usage: blender -b -P build_lods.py"""
from pathlib import Path
import json
import sys
import bpy
import numpy as np
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
from mathutils import Vector  # noqa: E402
src = P / 'work/r78_lod0.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src))
o = bpy.data.objects['PlaneGuardian']
co = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
pick = np.zeros(len(co), bool)
for k in range(3):
    pick |= co[:, k] > co[:, k].max() - .02
    pick |= co[:, k] < co[:, k].min() + .02
pts = [Vector(p) for p in co[pick]] + [Vector(p) for p in json.load(open(P / 'work/floor_contacts.json'))]
print('PROTECTED extremes', int(pick.sum()), 'total', len(pts))
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(src, P / 'work/r78_lods.glb', 'PlaneGuardian', ratios=(.5, .25, .125), max_influences=4, protected_points=pts)
