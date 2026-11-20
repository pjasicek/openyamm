"""Dump the rest mesh of a master blend's Body (positions, faces, head/hand flags, UVMap/HeadUV per loop) to npz.
Args (Blender): <blend> <out npz>"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
P = np.array([body.matrix_world @ v.co for v in me.vertices])
L = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', L)
ls = np.zeros(len(me.polygons), np.int32); me.polygons.foreach_get('loop_start', ls)
lt = np.zeros(len(me.polygons), np.int32); me.polygons.foreach_get('loop_total', lt)
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
hn = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hn)
uv = {}
for n in ('UVMap', 'HeadUV'):
    a = np.zeros(len(me.loops) * 2); me.uv_layers[n].data.foreach_get('uv', a); uv[n] = a.reshape(-1, 2)
vg = {g.index: g.name for g in body.vertex_groups}
W = np.zeros((len(me.vertices), 4)); Wi = -np.ones((len(me.vertices), 4), int)
for v in me.vertices:
    gs = sorted(v.groups, key=lambda g: -g.weight)[:4]
    for k, g in enumerate(gs): W[v.index, k] = g.weight; Wi[v.index, k] = g.group
bones = {b.name: list(rig.matrix_world @ b.head_local) + list(rig.matrix_world @ b.tail_local) for b in rig.data.bones}
import json; json.dump(bones, open(argv[1] + '.bones.json', 'w'))
np.savez(argv[1], P=P, L=L, ls=ls, lt=lt, head=hd, hand=hn, uv=uv['UVMap'], huv=uv['HeadUV'], W=W, Wi=Wi,
         vg=np.array([vg.get(i, '') for i in range(max(vg) + 1)]), mw=np.array(body.matrix_world))
print('DUMP', len(P), len(ls))
