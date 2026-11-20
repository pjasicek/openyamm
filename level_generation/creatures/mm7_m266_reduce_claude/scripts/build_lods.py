"""work/pick_lod0.glb -> work/pick_lods.glb with LOD1-3 and shadow LODs, the creature's own settings
(mm8_m452_claude/scripts/build_lods.py: the tool's default ratios, 4 influences; REA_LOD_RATIOS overrides), with
protected points: LOD0 vertices within 4 mm (REA_FLOOR_M) of the floor in any Death/Dead frame, the top 5 mm, the outer 5 mm at
both sides and both ends (nose and tail tip; the MM8 batch LOD locks). shrink_shadow_lods.py then tucks the shadow
LODs inside, as installed. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(P / 'work/pick_lod0.glb')); sc = bpy.context.scene
o = bpy.data.objects['M266']; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
rest = [o.matrix_world @ v.co for v in o.data.vertices]; top = max(p.z for p in rest)
xmin = min(p.x for p in rest); xmax = max(p.x for p in rest); ymin = min(p.y for p in rest); ymax = max(p.y for p in rest)
keep = {i for i, p in enumerate(rest) if p.z > top - .005 or p.x < xmin + .005 or p.x > xmax - .005
        or p.y < ymin + .005 or p.y > ymax - .005}
import os
FLOOR = float(os.environ.get('REA_FLOOR_M', '0.004'))  # the rat lies belly-down in Death/Dead: 1 cm caught the whole belly
for name in ('Death', 'Dead'):
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        keep |= {v.index for v in me.vertices if (ev.matrix_world @ v.co).z < FLOOR}; ev.to_mesh_clear()
points = [tuple(rest[i]) for i in sorted(keep)]
print('PROTECTED', len(points), 'points (extremes + Death floor contact)')
bpy.ops.wm.read_factory_settings(use_empty=True)
import os
R = tuple(float(x) for x in os.environ.get('REA_LOD_RATIOS', '0.5,0.18,0.06').split(','))
print('RATIOS', R)
# REA_MAT_RATIOS='Hydra_A:0.5,0.22,0.1;...' per-material LOD ratios (hydra: the body material carries ~60 separate
# dorsal/tail spikes and the claws, which keep a few triangles each, so its LOD3 surface needs a larger share)
MR = {k: tuple(float(x) for x in v.split(',')) for k, v in (i.split(':') for i in os.environ.get('REA_MAT_RATIOS', '').split(';') if i)}
print('MATERIAL RATIOS', MR)
generate(P / 'work/pick_lod0.glb', P / 'work/pick_lods.glb', 'M266', ratios=R, max_influences=4,
         protected_points=points, material_ratios=MR or None)
