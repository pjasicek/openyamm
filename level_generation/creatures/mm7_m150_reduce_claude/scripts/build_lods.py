"""work/pick_lod0.glb -> work/pick_lods.glb with LOD1-3 and shadow LODs, the creature's own settings
(the tool's default ratios, 4 influences; REA_LOD_RATIOS overrides), with
protected points: LOD0 vertices within 4 mm (REA_FLOOR_M) of the floor in any Death/Dead frame, the top 5 mm, the outer 5 mm at
both sides and both ends (the MM8 batch LOD locks). shrink_shadow_lods.py then tucks the shadow
LODs inside, as installed. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(P / 'work/pick_lod0.glb')); sc = bpy.context.scene
o = bpy.data.objects['M150']; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
rest = [o.matrix_world @ v.co for v in o.data.vertices]; top = max(p.z for p in rest)
xmin = min(p.x for p in rest); xmax = max(p.x for p in rest); ymin = min(p.y for p in rest); ymax = max(p.y for p in rest)
import os as _os
EXT = float(_os.environ.get('REA_EXT_M', '0.005'))   # m150: 5 mm caught ~800 wing-card and hair vertices; LOD3 stayed at 1k
crit = {'top': [i for i, p in enumerate(rest) if p.z > top - EXT], 'x': [i for i, p in enumerate(rest) if p.x < xmin + EXT or p.x > xmax - EXT],
        'y': [i for i, p in enumerate(rest) if p.y < ymin + EXT or p.y > ymax - EXT]}
print('EXTREMES', {k: len(v) for k, v in crit.items()})
keep = set(i for v in crit.values() for i in v)
import os
FLOOR = float(os.environ.get('REA_FLOOR_M', '0.004'))  # 4 mm: the corpse lies flat on its face
for name in ('Death', 'Dead'):
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        keep |= {v.index for v in me.vertices if (ev.matrix_world @ v.co).z < FLOOR}; ev.to_mesh_clear()
# m150: the corpse lies on its back with both wings flat, ~840 vertices touch the floor; protecting all kept LOD3 at
# 1k triangles. One floor point per FLOOR_CELL rest-space cell is enough to keep the LODs on the floor.
CELL = float(os.environ.get('REA_FLOOR_CELL', '0.06'))
ext = set(i for v in crit.values() for i in v); fl = sorted(keep - ext); cells = {}
for i in fl:
    cells.setdefault(tuple(int(c // CELL) for c in rest[i]), i)
keep = ext | set(cells.values())
points = [tuple(rest[i]) for i in sorted(keep)]
print('PROTECTED', len(points), 'points (extremes + Death floor contact)')
bpy.ops.wm.read_factory_settings(use_empty=True)
import os
R = tuple(float(x) for x in os.environ.get('REA_LOD_RATIOS', '0.5,0.22,0.08').split(','))
print('RATIOS', R)
generate(P / 'work/pick_lod0.glb', P / 'work/pick_lods.glb', 'M150', ratios=R, max_influences=4,
         protected_points=points)
