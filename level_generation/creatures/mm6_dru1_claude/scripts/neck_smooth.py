"""Relax the creased neck surface (review 2: light/dark triangles on the neck were folds in Meshy's neck geometry, the
texture there is uniform). Skin vertices (piece 0) in the neck cylinder (r < 8 cm round the neck joint, z 1.36-1.505)
are Laplacian-smoothed ITERS times (weight K, fading out over the outer 2 cm and the top/bottom 2 cm); open boundary
vertices stay. UVs and weights unchanged. In place on <blend>. Args: -- <blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
ITERS, K = 10, 0.5
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NA = json.load(open(os.path.join(HERE, 'work', 'joints_final.json')))['joints']['Neck']
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; rig.animation_data_create(); rig.animation_data.action = None
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); pl = bm.verts.layers.int['piece']
sel = []
for v in bm.verts:
    if v[pl] != 0 or any(e.is_boundary for e in v.link_edges):
        continue
    r = ((v.co.x - NA[0]) ** 2 + (v.co.y - NA[1]) ** 2) ** 0.5
    if r < 0.08 and 1.36 < v.co.z < 1.505:
        w = K * min(1.0, (0.08 - r) / 0.02) * min(1.0, (v.co.z - 1.36) / 0.02) * min(1.0, (1.505 - v.co.z) / 0.02)
        sel.append((v, w))
for _ in range(ITERS):
    new = {v: v.co.lerp(sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges), w) for v, w in sel}
    for v, p in new.items():
        v.co = p
bm.to_mesh(me); bm.free(); me.update(); bpy.ops.wm.save_mainfile()
print('NECKSMOOTH vertices', len(sel))
