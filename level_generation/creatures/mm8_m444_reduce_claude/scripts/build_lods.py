"""work/pick_lod0.glb -> work/pick_lods.glb with LOD1-3 and shadow LODs (MM8 Smuggler, node Smuggler). Ratios
REA_LOD_RATIOS, default 0.5 / 0.18 / 0.06 (the installed build's, build_actor_lods' default); the pick uses
0.5 / 0.22 / 0.085: from the 7,050-triangle LOD0 the defaults gave a 401-triangle LOD3 with a pointed skull and lost
boot laces, while 0.085 (579) matches the installed LOD3 (584). 8 influences. Protected points: LOD0 vertices within
1 cm of the floor in any Death/Dead frame, and the rest-pose vertices within 5 mm of each bounding extreme (crown,
soles, front, back, both hands). carry_variants.py then finishes the GLB. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import os, sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(P / 'work/pick_lod0.glb')); sc = bpy.context.scene
o = bpy.data.objects['Smuggler']; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
rest = [o.matrix_world @ v.co for v in o.data.vertices]
keep = set()
for axis in range(3):
    lo = min(p[axis] for p in rest); hi = max(p[axis] for p in rest)
    keep |= {i for i, p in enumerate(rest) if p[axis] < lo + .005 or p[axis] > hi - .005}
for name in ('Death', 'Dead'):
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        keep |= {v.index for v in me.vertices if (ev.matrix_world @ v.co).z < .01}; ev.to_mesh_clear()
points = [tuple(rest[i]) for i in sorted(keep)]
print('PROTECTED', len(points), 'points (bounding extremes + Death floor contact)')
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(P / 'work/pick_lod0.glb', P / 'work/pick_lods.glb', 'Smuggler', ratios=tuple(float(x) for x in os.environ.get('REA_LOD_RATIOS', '.5,.18,.06').split(',')), protected_points=points)
