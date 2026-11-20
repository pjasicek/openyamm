"""work/r72_lod0.glb -> export/mm8_m436_lods.glb with LOD1-3 and shadow LODs, the m436 project's settings
(mm8_m436_claude/scripts/build_lods.py: 4 influences, sole and wrist vertices protected: bind z below 6 mm or within
3 cm of a hand bone head, recomputed for the reduced LOD0). Ratios 0.5 / 0.24 / 0.117: the gate runner wants LOD3 at
most 10 % of LOD0 and a hand edge region in every LOD; 0.10 and 0.11 (938 / 973 triangles) collapsed the hands,
0.117 gives 1,047. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
SRC = P / 'work/r72_lod0.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SRC))
body = bpy.data.objects['M436']; rig = next(m.object for m in body.modifiers if m.type == 'ARMATURE')
hands = [rig.matrix_world @ rig.data.bones[f'B_{s}_Hand'].head_local for s in 'LR']
protected = []
for v in body.data.vertices:
    co = body.matrix_world @ v.co
    if co.z < .006 or any((co - h).length < .03 for h in hands):
        protected.append(list(co))
print('PROTECTED', len(protected))
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(SRC, P / 'export/mm8_m436_lods.glb', 'M436', ratios=(.5, .24, .117), max_influences=4, protected_points=protected)
