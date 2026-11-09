"""work/r81_lod0.glb -> work/r81_lods.glb with LOD1-3 and shadow LODs, the installed model's ratios and influence
budget (0.5 / 0.25 / 0.125 of LOD0, 4 influences). Protected: the Death/Dead floor contacts (floor_contacts.py) and
vertices within 2 cm of each bounding extreme (crown spikes, snout, tail spikes, claw tips, soles), as the m592 build.
The flat shading survives the collapse (every LOD keeps its own vertices per face). Then shrink_shadow_lods.py and
fix_lod_winding.py (from mm8_m592_reduce_claude). Usage: blender -b -P build_lods.py"""
from pathlib import Path
import json
import os
import sys
import bpy
import numpy as np
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
from mathutils import Vector  # noqa: E402
RATIOS = tuple(float(r) for r in os.environ.get('LOD_RATIOS', '0.5,0.25,0.125').split(','))
src = P / 'work/r81_lod0.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src))
o = bpy.data.objects['CrystalDragon']
co = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
# a 2 cm band protected 1,734 vertices (every paw sits in the floor band, the flat-shaded mesh triples each vertex)
# and LOD3 collapsed into sheets; 5 mm bands on the sides, front, back and top, and the floor via floor_contacts
EXT = float(os.environ.get('LOD_EXTREME_M', '0.005'))
pick = np.zeros(len(co), bool)
for k in range(3):
    pick |= co[:, k] > co[:, k].max() - EXT
    if k < 2:
        pick |= co[:, k] < co[:, k].min() + EXT
pts = [Vector(p) for p in co[pick]] + [Vector(p) for p in json.load(open(P / 'work/floor_contacts.json'))]
print('PROTECTED extremes', int(pick.sum()), 'total', len(pts), 'ratios', RATIOS)
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(src, P / 'work/r81_lods.glb', 'CrystalDragon', ratios=RATIOS, max_influences=4, protected_points=pts)
