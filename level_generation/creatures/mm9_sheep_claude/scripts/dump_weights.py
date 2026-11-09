"""Dump the rigged 'Body' of a blend to npz for weight analysis: world positions, triangles, weights (n, bones),
bone names/heads/tails (world, rest) and the integer attributes 'piece'/'chain' when present.
Args: <blend> <out npz>"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']
arm = bpy.data.objects['MM9_Rig']
me = body.data
mw = body.matrix_world
co = np.array([tuple(mw @ v.co) for v in me.vertices])
me.calc_loop_triangles()
tris = np.array([tuple(t.vertices) for t in me.loop_triangles])
bones = [b.name for b in arm.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
gname = {g.index: g.name for g in body.vertex_groups}
W = np.zeros((len(co), len(bones)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, bidx[gname[g.group]]] = g.weight
heads = np.array([tuple(arm.matrix_world @ b.head_local) for b in arm.data.bones])
tails = np.array([tuple(arm.matrix_world @ b.tail_local) for b in arm.data.bones])
parents = [b.parent.name if b.parent else '' for b in arm.data.bones]
extra = {}
for a in ('piece', 'chain'):
    if a in me.attributes:
        extra[a] = np.array([d.value for d in me.attributes[a].data])
np.savez(argv[1], co=co, tris=tris, W=W, bones=np.array(bones), heads=heads, tails=tails, parents=np.array(parents),
         **extra)
print('DUMP', len(co), len(tris), len(bones), list(extra))
