"""work/pick_lod0.glb -> work/pick_lods.glb with LOD1-3 and shadow LODs, the creature's own settings
(the tool's default ratios, 4 influences; REA_LOD_RATIOS overrides), with
protected points: LOD0 vertices within 4 mm (REA_FLOOR_M) of the floor in any Death/Dead frame, the top 5 mm, the outer 5 mm at
both sides and both ends (the MM8 batch LOD locks). shrink_shadow_lods.py then tucks the shadow
LODs inside, as installed. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import os
import sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(P / 'work/pick_lod0.glb')); sc = bpy.context.scene
o = bpy.data.objects['HVM']; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
rest = [o.matrix_world @ v.co for v in o.data.vertices]; top = max(p.z for p in rest)
xmin = min(p.x for p in rest); xmax = max(p.x for p in rest); ymin = min(p.y for p in rest); ymax = max(p.y for p in rest)
EXT = float(os.environ.get('REA_EXT_M', '0.005'))   # m178: 1 mm (the 5 mm bands held 310 points: claw, tooth, tail tips)
keep = {i for i, p in enumerate(rest) if p.z > top - EXT or p.x < xmin + EXT or p.x > xmax - EXT
        or p.y < ymin + EXT or p.y > ymax - EXT}
FLOOR = float(os.environ.get('REA_FLOOR_M', '0.004'))  # 4 mm: the corpse lies flat on its face
for name in os.environ.get('REA_FLOOR_CLIPS', 'Death,Dead').split(','):   # m178: the idle soles locked too many points for LOD3
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0 + int((f1 - f0) * float(os.environ.get('REA_FLOOR_FROM', '0'))), f1 + 1):   # m178: the fallen part only
        sc.frame_set(f); ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        keep |= {v.index for v in me.vertices if (ev.matrix_world @ v.co).z < FLOOR}; ev.to_mesh_clear()
points = [tuple(rest[i]) for i in sorted(keep)]
print('PROTECTED', len(points), 'points (extremes + Death floor contact)')
bpy.ops.wm.read_factory_settings(use_empty=True)
R = tuple(float(x) for x in os.environ.get('REA_LOD_RATIOS', '0.5,0.26,0.085')   .split(','))
print('RATIOS', R)
generate(P / 'work/pick_lod0.glb', P / 'work/pick_lods.glb', 'HVM', ratios=R, max_influences=4,
         protected_points=points)
