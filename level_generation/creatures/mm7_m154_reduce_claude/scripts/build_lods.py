"""work/pick_lod0.glb -> work/pick_lods.glb with LOD1-3 and shadow LODs (tools/build_actor_lods.py, default 8 influence
slots like the source build; ratios REA_LOD_RATIOS, default 0.5 / 0.22 / 0.085: LOD1/2 under the source's 5,124 / 1,838 body
triangles; LOD3 ~705 instead of 605, because at 0.072 the helmet folded into a peak and the face flattened), with protected points: LOD0 vertices within 1.5 mm (REA_FLOOR_M) of the floor in
any Death/Dead frame, the top 1 mm (REA_EXT_M: helmet spike tip), the top 1 mm of each horn (|x| > 4 cm, z > 1.6 m:
thin top features), and the outer 1 mm at both sides and both ends (wider bands held so many points that LOD3 pulled
the horns into needles and folded the helmet). shrink_shadow_lods.py then tucks the shadow LODs inside,
as the source build did. The bowstring's nock ring and end rings are protected too. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import os, sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(P / 'work/pick_lod0.glb')); sc = bpy.context.scene
o = bpy.data.objects['M154']; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
rest = [o.matrix_world @ v.co for v in o.data.vertices]; top = max(p.z for p in rest)
xmin = min(p.x for p in rest); xmax = max(p.x for p in rest); ymin = min(p.y for p in rest); ymax = max(p.y for p in rest)
EXT = float(os.environ.get('REA_EXT_M', '0.001'))  # 5 mm bands held 40+ points that LOD3 cannot afford
TOP = os.environ.get('REA_PROTECT_TOP', '1') == '1'
keep = {i for i, p in enumerate(rest) if (TOP and p.z > top - EXT) or p.x < xmin + EXT or p.x > xmax - EXT
        or p.y < ymin + EXT or p.y > ymax - EXT}
for side in ((1, -1) if TOP else ()):
    horn = [i for i, p in enumerate(rest) if p.z > 1.6 and p.x * side > 0.04]
    hz = max(rest[i].z for i in horn); tips = {i for i in horn if rest[i].z > hz - EXT}
    keep |= tips; print('HORN', side, len(tips), 'tip vertices at', round(hz, 4))
# bowstring tube: its nock ring (StringNock weight 1) and both end rings (5 mm from the ends along the string), so every
# LOD keeps a two-segment string that reaches the nock at full draw (a free collapse left the nock ring at 69 % weight
# and 7 faces stretched over 20x in Attack; the source LODs kept a straight 6-triangle string that never drew)
gi = {g.name: g.index for g in o.vertex_groups}
wt = lambda v, n: sum(g.weight for g in v.groups if g.group == gi[n])
sv = [v.index for v in o.data.vertices if wt(v, 'Bow') + wt(v, 'StringNock') > 0.999]
import numpy as np
sp = np.array([rest[i][:] for i in sv]); ax = np.linalg.svd(sp - sp.mean(0))[2][0]; t = (sp - sp.mean(0)) @ ax
string = {sv[k] for k in range(len(sv)) if wt(o.data.vertices[sv[k]], 'StringNock') > 0.999 or t[k] < t.min() + .005
          or t[k] > t.max() - .005}
keep |= string; print('STRING', len(sv), 'vertices,', len(string), 'protected (nock ring and ends)')
FLOOR = float(os.environ.get('REA_FLOOR_M', '0.0015'))
nfloor = 0
for name in ('Death', 'Dead'):
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        fl = {v.index for v in me.vertices if (ev.matrix_world @ v.co).z < FLOOR}; nfloor += len(fl - keep); keep |= fl
        ev.to_mesh_clear()
points = [tuple(rest[i]) for i in sorted(keep)]
print('PROTECTED', len(points), 'points (extremes, horn tips, Death/Dead floor contact', nfloor, ')')
bpy.ops.wm.read_factory_settings(use_empty=True)
R = tuple(float(x) for x in os.environ.get('REA_LOD_RATIOS', '0.5,0.22,0.085').split(','))
print('RATIOS', R)
OUT = os.environ.get('REA_LODS_OUT', 'pick_lods.glb')
generate(P / 'work/pick_lod0.glb', P / 'work' / OUT, 'M154', ratios=R, protected_points=points)
