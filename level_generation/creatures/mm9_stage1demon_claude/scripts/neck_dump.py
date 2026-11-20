"""Neck pass: dump the master (rest pose) for numpy analysis: V, F, part per vertex, head flag per face, UVMap and HeadUV per
face corner, weights (dense, by group name), joints. Args: <blend> <out npz>"""
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); o = bpy.data.objects['Body']; me = o.data; rig = o.parent
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
n = len(me.vertices); nf = len(me.polygons)
V = np.array([v.co[:] for v in me.vertices]); F = np.array([p.vertices[:] for p in me.polygons])
pa = np.zeros(n, int); me.attributes['part'].data.foreach_get('value', pa)
hd = np.zeros(nf, int); me.attributes['head'].data.foreach_get('value', hd)
uv = {}
for nm in ('UVMap', 'HeadUV'):
    d = np.zeros(len(me.loops) * 2); me.uv_layers[nm].data.foreach_get('uv', d); d = d.reshape(-1, 2)
    li = np.array([p.loop_indices[:] for p in me.polygons]); uv[nm] = d[li]
gn = [g.name for g in o.vertex_groups]; W = np.zeros((n, len(gn)), np.float32)
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
nk = np.zeros(nf, int)
if 'neck' in me.attributes: me.attributes['neck'].data.foreach_get('value', nk)
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
np.savez(a[1], V=V, F=F, part=pa, head=hd, uvb=uv['UVMap'], uvh=uv['HeadUV'], W=W, gn=np.array(gn), jn=np.array(list(J)), jp=np.array(list(J.values())),
         mw=np.array(o.matrix_world), neck=nk)
print('DUMPED', n, nf, len(gn))
