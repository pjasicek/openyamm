"""Dump the Body mesh + Rig of a .blend (rest pose) to npz: co, faces (triangulated loops), mat, uv per corner,
weights (dense, bone order = rig bones), bone heads/tails/rest matrices, point attributes.
Usage: blender -b <file> -P dump.py -- <out.npz>"""
import sys, bpy, numpy as np
out = sys.argv[sys.argv.index('--') + 1]
o = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = o.data
mw = np.array(o.matrix_world)
co = np.array([v.co for v in me.vertices]); co = co @ mw[:3, :3].T + mw[:3, 3]
me.calc_loop_triangles()
tri = np.array([t.vertices[:] for t in me.loop_triangles], np.int32)
tloops = np.array([t.loops[:] for t in me.loop_triangles], np.int32)
tpoly = np.array([t.polygon_index for t in me.loop_triangles], np.int32)
mat = np.array([me.polygons[p].material_index for p in tpoly], np.int32)
uvl = me.uv_layers.active.data
uv = np.array([[uvl[l].uv[:] for l in t] for t in tloops], np.float32)
bones = [b.name for b in rig.data.bones]
gi = {g.index: g.name for g in o.vertex_groups}
W = np.zeros((len(me.vertices), len(bones)), np.float32)
for v in me.vertices:
    for g in v.groups:
        n = gi[g.group]
        if n in bones:
            W[v.index, bones.index(n)] = g.weight
rmw = np.array(rig.matrix_world)
heads = np.array([rmw @ np.append(b.head_local, 1) for b in rig.data.bones])[:, :3]
tails = np.array([rmw @ np.append(b.tail_local, 1) for b in rig.data.bones])[:, :3]
mats = np.array([rmw @ np.array(b.matrix_local) for b in rig.data.bones])
parents = np.array([bones.index(b.parent.name) if b.parent else -1 for b in rig.data.bones])
attrs = {}
for a in me.attributes:
    if a.name.startswith('.') or a.name in ('position',):
        continue
    if a.domain == 'POINT' and a.data_type in ('FLOAT', 'INT', 'BOOLEAN'):
        attrs['pa_' + a.name] = np.array([d.value for d in a.data])
    if a.domain == 'FACE' and a.data_type in ('FLOAT', 'INT', 'BOOLEAN'):
        attrs['fa_' + a.name] = np.array([d.value for d in a.data])[tpoly]
np.savez(out, co=co, tri=tri, tpoly=tpoly, mat=mat, uv=uv, W=W, bones=np.array(bones), heads=heads, tails=tails,
         bmats=mats, parents=parents, matnames=np.array([m.name for m in me.materials]), **attrs)
print('DUMPED', out, co.shape, tri.shape, len(bones), list(attrs))
