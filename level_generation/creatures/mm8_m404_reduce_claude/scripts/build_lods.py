"""work/<tag>_lod0.glb -> work/<tag>_lods.glb with LOD1-3 and shadow LODs. Ratios REA_LOD_RATIOS (default the
installed model's own build, tools/build_actor_lods.py defaults 0.5 / 0.18 / 0.06), 4 influences. The vertices at
each bounding extreme (REA_EXT m below it, default 0: only the extreme vertices) are protected; with the m604
2 cm band (549 points with the floor contacts) LOD3 broke into shards (review/lods/sheet_tries.png). The Death/Dead floor contacts (floor_contacts.py -> work/floor_contacts.json)
are protected too: unprotected, LOD3 sank 5 cm into the floor in Death. Usage: [REA_TAG=r79] [REA_LOD_RATIOS=a,b,c] blender -b -P build_lods.py"""
import os
from pathlib import Path
import sys
import bpy
import json
import numpy as np
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
TAG = os.environ.get('REA_TAG', 'r79'); src = P / f'work/{TAG}_lod0.glb'
EXT = float(os.environ.get('REA_EXT', '0'))  # 2 cm (the m604 default) protected 549 points and LOD3 fell apart
RATIOS = tuple(float(r) for r in os.environ.get('REA_LOD_RATIOS', '0.5,0.18,0.06').split(','))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src))
o = bpy.data.objects['M404']
co = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
pick = np.zeros(len(co), bool)
for k in range(3):
    pick |= co[:, k] > co[:, k].max() - EXT
    pick |= co[:, k] < co[:, k].min() + EXT
points = [tuple(p) for p in co[pick]] + [tuple(p) for p in json.load(open(P / 'work/floor_contacts.json'))]
print('PROTECTED', len(points), 'extreme vertices')
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(src, P / f'work/{TAG}_lods.glb', 'M404', ratios=RATIOS, max_influences=4, protected_points=points)
