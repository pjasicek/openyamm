"""work/pick_lod0.glb -> work/pick_lods.glb with LOD1-3 and shadow LODs, the creature's own settings
(mm7_m174_claude: build_actor_lods defaults 0.5 / 0.18 / 0.06; LOD3 at 0.08 here, about the source's 514, 8 influences), with protected
points: LOD0 vertices within 1 cm of the floor in any Death/Dead frame and the top 5 mm of the crown (the MM8 batch
LOD locks). carry_variants.py then finishes export/mm7_m174.glb. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(P / 'work/pick_lod0.glb')); sc = bpy.context.scene
o = bpy.data.objects['M174']; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
rest = [o.matrix_world @ v.co for v in o.data.vertices]; top = max(p.z for p in rest)
keep = {i for i, p in enumerate(rest) if p.z > top - .005}
# the tip of each sun-crown ray (separate pieces round the head, 80-115 faces): the farthest vertex from the head joint
import bmesh
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
key = {}                                     # glTF splits vertices at UV seams: join them by position first
rep = [key.setdefault(tuple(round(c, 5) for c in rest[i]), i) for i in range(len(rest))]
par = list(range(len(rest)))
def find(i):
    while par[i] != i:
        par[i] = par[par[i]]; i = par[i]
    return i
for e in bm.edges:
    a, b = find(rep[e.verts[0].index]), find(rep[e.verts[1].index])
    par[a] = b
comps = {}
for i in range(len(rest)):
    comps.setdefault(find(rep[i]), []).append(i)
hj = rig.matrix_world @ rig.data.bones['B_Head'].head_local; tips = 0
for comp in comps.values():
    far = max(comp, key=lambda i: (rest[i] - hj).length)
    if len(comp) < 150 and (rest[far] - hj).length > .12 and rest[far].z > 1.3:
        keep.update(i for i in comp if (rest[i] - rest[far]).length < 1e-5); tips += 1
print('RAY TIPS', tips)
# bounding extremes (finger tips of the A-pose hands, front and back of the robe): LOD3 lost 11 cm of width without
for ax in (0, 1):
    lo, hi = min(p[ax] for p in rest), max(p[ax] for p in rest)
    keep |= {i for i, p in enumerate(rest) if p[ax] < lo + .005 or p[ax] > hi - .005}
for name in ('Death', 'Dead'):
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        keep |= {v.index for v in me.vertices if (ev.matrix_world @ v.co).z < .01}; ev.to_mesh_clear()
points = [tuple(rest[i]) for i in sorted(keep)]
print('PROTECTED', len(points), 'points (top, crown ray tips, Death floor contact)')
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(P / 'work/pick_lod0.glb', P / 'work/pick_lods.glb', 'M174', ratios=(.5, .18, .08), max_influences=8,
         protected_points=points)
