"""Retexture master for the 45 % female peasant: the original authoring master (rig, 7 clips, sockets, scene data
pfem_parts/eyes/knife/braid) with the reduced mesh in place of Peasant.

- Cand_45 (work/ladder.blend) keeps its skin weights (exact for the knife, data transfer elsewhere).
- Face attribute `part`: nearest master face, then the majority per connected piece (every master part is its own
  pieces; per-face labels leaked across touching pieces on other creatures).
- Face attribute `head` (head texture set): nearest master face, restricted to the head parts.
- Custom normals (face_repair.py's softened skin normals) by data transfer from the master.
Out: work/r45_master.blend (then uv_r45.py for fresh UVs)."""
import json
import os

import bmesh
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(HERE, '..', 'mm6_pfem_claude', 'work', 'final_v3_head_repaired.blend')
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(MASTER))
old = bpy.data.objects['Peasant']; rig = bpy.data.objects['Peasant_Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
PARTS = json.loads(bpy.context.scene['pfem_parts'])
HEAD_PARTS = {PARTS.index(n) for n in ('Body', 'Hair', 'Braid', 'Headband')}
# LADDER/CAND pick the reduced candidate (head-detail rebuild: work_head_proj/work/ladder.blend, Cand_57)
LADDER = os.environ.get('LADDER', os.path.join(HERE, 'work', 'ladder.blend')); CAND = os.environ.get('CAND', 'Cand_45')
with bpy.data.libraries.load(os.path.abspath(LADDER)) as (src, dst):
    dst.objects = [CAND]
new = bpy.data.objects[CAND]
bpy.context.scene.collection.objects.link(new)
new.parent = rig; new.matrix_parent_inverse.identity(); new.matrix_world = old.matrix_world.copy()
for m in list(new.modifiers):
    new.modifiers.remove(m)
arm = new.modifiers.new('Armature', 'ARMATURE'); arm.object = rig
g = new.vertex_groups.get('ReduceProtect')
if g:
    new.vertex_groups.remove(g)
missing = [g.name for g in new.vertex_groups if g.name not in old.vertex_groups]
assert not missing, missing

# part and head from the nearest master face
om = old.data
opart = np.array([a.value for a in om.attributes['part'].data]); ohead = np.array([a.value for a in om.attributes['head'].data])
tree = BVHTree.FromPolygons([v.co for v in om.vertices], [list(p.vertices) for p in om.polygons])
me = new.data
near = np.array([tree.find_nearest(p.center)[2] for p in me.polygons])
fpart = opart[near]; fhead = ohead[near]
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
seen = set(); pieces = 0
for f in bm.faces:
    if f.index in seen:
        continue
    stack, comp = [f], []
    seen.add(f.index)
    while stack:
        x = stack.pop(); comp.append(x.index)
        for e in x.edges:
            for y in e.link_faces:
                if y.index not in seen:
                    seen.add(y.index); stack.append(y)
    vals, counts = np.unique(fpart[comp], return_counts=True)
    print('PIECE', len(comp), {PARTS[v]: int(c) for v, c in zip(vals, counts)})
    fpart[comp] = vals[counts.argmax()]; pieces += 1
bm.free()
fhead = np.where(np.isin(fpart, list(HEAD_PARTS)), fhead, 0)
fhead[np.isin(fpart, [PARTS.index(n) for n in ('Hair', 'Braid', 'Headband')])] = 1
for name, values in (('part', fpart), ('head', fhead)):
    if name in me.attributes:
        me.attributes.remove(me.attributes[name])
    me.attributes.new(name, 'INT', 'FACE').data.foreach_set('value', values.astype(np.int32).tolist())

# softened custom normals from the master
dt = new.modifiers.new('Normals', 'DATA_TRANSFER'); dt.object = old; dt.use_loop_data = True
dt.data_types_loops = {'CUSTOM_NORMAL'}; dt.loop_mapping = 'POLYINTERP_NEAREST'
for o in bpy.data.objects:
    o.select_set(o == new)
bpy.context.view_layer.objects.active = new
while new.modifiers[0].name != dt.name:
    bpy.ops.object.modifier_move_up(modifier=dt.name)
bpy.ops.object.modifier_apply(modifier=dt.name)

me.materials.clear()
for m in old.data.materials:
    me.materials.append(m)
bpy.data.objects.remove(old, do_unlink=True)
new.name = 'Peasant'; me.name = 'Peasant'
from collections import Counter
print('PREP faces', len(me.polygons), 'pieces', pieces, 'head faces', int(fhead.sum()),
      'parts', dict(Counter(PARTS[p] for p in fpart)))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'r45_master.blend'))
