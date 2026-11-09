"""Smooth the crumpled lid/brow geometry round the eyes (review 1 follow-up: faceted shards round the eyes in the
viewer and in Blender; the clay render shows folds there). Face-skin vertices (piece 0, not on the eye caps' rims)
within RADIUS of an eye centre are Laplacian-smoothed ITERS times with weight falling to 0 at RADIUS; UVs and weights
are unchanged. In place on <blend>. Args: -- <blend>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
blend = sys.argv[sys.argv.index('--') + 1]
RADIUS, ITERS, K = 0.022, 6, 0.5
EYES = [Vector((0.017, -0.107, 1.573)), Vector((-0.030, -0.107, 1.573))]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; rig.animation_data_create(); rig.animation_data.action = None
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
pl = bm.verts.layers.int['piece']; ec = bm.faces.layers.int['eye_cap']
rim = {v for f in bm.faces if f[ec] for v in f.verts}
sel = []
for v in bm.verts:
    if v[pl] != 0 or v in rim:
        continue
    d = min((v.co - c).length for c in EYES)
    if d < RADIUS:
        sel.append((v, K * (1 - d / RADIUS)))
for _ in range(ITERS):
    new = {}
    for v, w in sel:
        nb = [e.other_vert(v).co for e in v.link_edges]
        avg = sum(nb, Vector()) / len(nb)
        new[v] = v.co.lerp(avg, w)
    for v, p in new.items():
        v.co = p
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_mainfile()
print('LIDSMOOTH vertices', len(sel), 'iterations', ITERS)
