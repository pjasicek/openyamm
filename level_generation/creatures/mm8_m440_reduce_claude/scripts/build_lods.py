"""work/r67_lod0.glb -> export/mm8_m440_lods.glb with LOD1-3 and shadow LODs, 4 influences as in production
(mm8_m440_claude/scripts/build_lods.py); preserve_contacts.py then puts the LOD0 right hand and feet back into every
LOD. Ratios 0.5 / 0.3 / 0.17 instead of the production 0.5 / 0.25 / 0.125: from the lighter LOD0 those left brown
smears on the helmet dome at LOD2 and LOD3 (review/lods/); the result is still below every installed LOD.
Wrist and sole vertices are protected as in the Ogre Peasant reduction (bind z below 6 mm or within 3 cm of a hand
bone head): without it the 0.3 LOD2 left a sliver at the right wrist (gate arm_stretch_max 5.3-6.5 against 5).
Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
SRC = P / 'work/r67_lod0.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SRC))
body = bpy.data.objects['M440']; rig = next(m.object for m in body.modifiers if m.type == 'ARMATURE')
hands = [rig.matrix_world @ rig.data.bones[f'B_{s}_Hand'].head_local for s in 'LR']
protected = [list(body.matrix_world @ v.co) for v in body.data.vertices
             if (body.matrix_world @ v.co).z < .006 or any(((body.matrix_world @ v.co) - h).length < .03 for h in hands)]
print('PROTECTED', len(protected))
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(SRC, P / 'export/mm8_m440_lods.glb', node_name='M440', ratios=(.5, .3, .17), max_influences=4, protected_points=protected)
