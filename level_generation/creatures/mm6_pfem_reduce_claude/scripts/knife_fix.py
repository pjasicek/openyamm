"""Black quad on the clasped hands (three.js viewer): the reduction's weight transfer gave one hand vertex a full Knife
weight; with the knife bone scaled to zero outside Attack its 5 skin faces stretched into the knife's collapse
point. Knife-piece vertices are weighted 1.0 to Knife (split from any non-knife face), and every other vertex with a
Knife weight takes the weights of the nearest non-knife master vertex. (Relabelling faces nearest the master knife
as knife cut holes in the hand and was dropped.) UVs are unchanged (the Meshy return stays valid). In place on work/r45_master.blend."""
import json, os
import bmesh, bpy
import numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'r45_master.blend'))
PARTS = json.loads(bpy.context.scene['pfem_parts']); KNIFE = PARTS.index('Knife')
ob = bpy.data.objects['Peasant']; me = ob.data
with bpy.data.libraries.load(os.path.abspath(os.path.join(HERE, '..', 'mm6_pfem_claude', 'work', 'final_v3_head_repaired.blend'))) as (s, d):
    d.objects = ['Peasant']
src = d.objects[0]; sm = src.data
spart = np.array([a.value for a in sm.attributes['part'].data])
tree = BVHTree.FromPolygons([v.co for v in sm.vertices], [list(p.vertices) for p in sm.polygons])
part = np.array([a.value for a in me.attributes['part'].data])
near = np.array([spart[tree.find_nearest(p.center)[2]] for p in me.polygons])
knife = part == KNIFE      # the knife pieces only: relabelling faces nearest the master knife cut holes in the hand
relabel = int((knife & (part != KNIFE)).sum())
part[knife] = KNIFE
me.attributes['part'].data.foreach_set('value', part.tolist())
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
kf = [f for f in bm.faces if knife[f.index]]
shared = {v for f in kf for v in f.verts if any(not knife[g.index] for g in v.link_faces)}
bmesh.ops.split(bm, geom=kf, use_only_faces=True)
bm.to_mesh(me); bm.free()
# split re-creates the faces (new indices): find the knife again by its label, never by the old face index
part = np.array([a.value for a in me.attributes['part'].data])
kverts = {v for p in me.polygons if part[p.index] == KNIFE for v in p.vertices}
assert all(part[p.index] == KNIFE for p in me.polygons if set(p.vertices) & kverts), 'knife vertices still shared'
gk = ob.vertex_groups['Knife'].index
for vi in kverts:
    for g in list(me.vertices[vi].groups):
        ob.vertex_groups[g.group].remove([vi])
    ob.vertex_groups['Knife'].add([vi], 1.0, 'REPLACE')
# a vertex outside the knife that the reduction's weight transfer gave a Knife weight takes the weights of the
# nearest non-knife master vertex (it dragged its skin faces into the knife's collapse point)
from mathutils import kdtree
sk = src.vertex_groups['Knife'].index
clean = [v for v in sm.vertices if not any(g.group == sk and g.weight > 0 for g in v.groups)]
kd = kdtree.KDTree(len(clean))
for i, v in enumerate(clean):
    kd.insert(v.co, i)
kd.balance()
stray = [v.index for v in me.vertices if v.index not in kverts and any(g.group == gk and g.weight > 0 for g in v.groups)]
for vi in stray:
    sv = clean[kd.find(me.vertices[vi].co)[1]]
    for g in list(me.vertices[vi].groups):
        ob.vertex_groups[g.group].remove([vi])
    for g in sv.groups:
        ob.vertex_groups[src.vertex_groups[g.group].name].add([vi], g.weight, 'REPLACE')
print('KNIFE_FIX stray knife-weighted vertices reweighted', len(stray))
bpy.data.objects.remove(src, do_unlink=True)
print('KNIFE_FIX faces', int((part == KNIFE).sum()), 'relabelled', relabel, 'shared verts split', len(shared), 'knife verts', len(kverts))
bpy.ops.wm.save_mainfile()
