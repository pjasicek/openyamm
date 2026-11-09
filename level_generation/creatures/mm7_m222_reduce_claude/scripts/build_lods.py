"""work/pick_lod0.glb -> work/pick_lods.glb with LOD1-3 and shadow LODs: ratios 0.5 / 0.2 / 0.07 of LOD0
(REA_LOD_RATIOS; the source's builder defaults 0.5 / 0.18 / 0.06 gave a 470-triangle LOD3 whose face and arms fell
apart, below the source's 569), up to 8 influences on the LODs like the source (its LOD1-3 carry JOINTS_1), with protected points: LOD0 vertices within 4 mm (REA_FLOOR_M) of the floor in any
Death/Dead frame, the top 5 mm (the helmet crest), the outer 5 mm at both sides and both ends (the MM8 batch LOD
locks). shrink_shadow_lods.py then tucks the shadow LODs inside, as the source export. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import os, sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(P / 'work/pick_lod0.glb')); sc = bpy.context.scene
o = bpy.data.objects['M222']; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
rest = [o.matrix_world @ v.co for v in o.data.vertices]; top = max(p.z for p in rest)
xmin = min(p.x for p in rest); xmax = max(p.x for p in rest); ymin = min(p.y for p in rest); ymax = max(p.y for p in rest)
keep = {i for i, p in enumerate(rest) if p.z > top - .005 or p.x < xmin + .005 or p.x > xmax - .005
        or p.y < ymin + .005 or p.y > ymax - .005}
FLOOR = float(os.environ.get('REA_FLOOR_M', '0.004'))
for name in ('Death', 'Dead'):
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        keep |= {v.index for v in me.vertices if (ev.matrix_world @ v.co).z < FLOOR}; ev.to_mesh_clear()
points = [tuple(rest[i]) for i in sorted(keep)]
print('PROTECTED', len(points), 'points (extremes + Death/Dead floor contact)')
bpy.ops.wm.read_factory_settings(use_empty=True)
R = tuple(float(x) for x in os.environ.get('REA_LOD_RATIOS', '0.5,0.2,0.07').split(','))
print('RATIOS', R)
generate(P / 'work/pick_lod0.glb', P / 'work/pick_lods.glb', 'M222', ratios=R, protected_points=points)
