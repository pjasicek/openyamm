"""work/pick_lod0.glb -> work/pick_lods.glb with LOD1-3 and shadow LODs, the same settings as
mm8_m424_claude/scripts/build_lods.py (build_actor_lods defaults 0.5 / 0.18 / 0.06, 4 influences), with protected
points: LOD0 vertices within 1 cm of the floor in any Death/Dead frame (LOD3 Death went 15 mm under the floor
unlocked) and the top 5 mm of the crown (LOD3 lost 1.3 cm of height). Then mm8_m424_claude/scripts/
shrink_shadow_lods.py and carry_variants.py finish export/mm8_m424.glb. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(P / 'work/pick_lod0.glb')); sc = bpy.context.scene
o = bpy.data.objects['M424']; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
rest = [o.matrix_world @ v.co for v in o.data.vertices]; top = max(p.z for p in rest)
keep = {i for i, p in enumerate(rest) if p.z > top - .005}
for name in ('Death', 'Dead'):
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        keep |= {v.index for v in me.vertices if (ev.matrix_world @ v.co).z < .01}; ev.to_mesh_clear()
points = [tuple(rest[i]) for i in sorted(keep)]
print('PROTECTED', len(points), 'points (crown + Death floor contact)')
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(P / 'work/pick_lod0.glb', P / 'work/pick_lods.glb', 'M424', max_influences=4, protected_points=points)
