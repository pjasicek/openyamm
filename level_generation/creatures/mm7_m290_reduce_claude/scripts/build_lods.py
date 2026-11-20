"""work/pick_lod0.glb -> work/pick_lods.glb with LOD1-3 and shadow LODs, the Monk's own settings
(mm7_m290_claude/scripts/build_runtime.sh: tools/build_actor_lods.py defaults, ratios 0.5 / 0.18 / 0.06, 8 influences),
with protected points: LOD0 vertices within 1 cm of the floor in any Death/Dead frame, the top 5 mm and the hood tip
(vertices within 2 cm of the rearmost point above 1.5 m). shrink_shadow_lods.py and carry_variants.py then finish
export/mm7_m290.glb. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(P / 'work/pick_lod0.glb')); sc = bpy.context.scene
o = bpy.data.objects['M290']; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
rest = [o.matrix_world @ v.co for v in o.data.vertices]; top = max(p.z for p in rest)
keep = {i for i, p in enumerate(rest) if p.z > top - .005}
tip = max((p for p in rest if p.z > 1.5), key=lambda p: p.y)
keep |= {i for i, p in enumerate(rest) if (p - tip).length < .02}
for name in ('Death', 'Dead'):
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        keep |= {v.index for v in me.vertices if (ev.matrix_world @ v.co).z < .01}; ev.to_mesh_clear()
points = [tuple(rest[i]) for i in sorted(keep)]
print('PROTECTED', len(points), 'points (crown, hood tip', tuple(round(x, 3) for x in tip), ', Death floor contact)')
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(P / 'work/pick_lod0.glb', P / 'work/pick_lods.glb', 'M290', ratios=(.5, .18, .06), max_influences=8,
         protected_points=points)
