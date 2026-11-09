"""Accessories vs the coat under them, every frame of every clip: per piece, the change of the distance from the piece
centroid to the nearest coat (garments 1/2) surface point against rest, and the sideways slide of that nearest point
(the piece drifting off its painted seat). Prints the worst per clip. Args: -- <blend> <piece,piece,...>"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); PCS = [int(x) for x in a[1].split(',')]
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
gv = np.array([x.value for x in me.attributes['garment'].data]); pv = np.array([x.value for x in me.attributes['piece'].data])
cf = [p for p in me.polygons if all(gv[i] in (1, 2) for i in p.vertices)]
cfv = [tuple(p.vertices) for p in cf]
rest = np.array([v.co[:] for v in me.vertices])
T0 = BVHTree.FromPolygons([tuple(x) for x in rest], cfv)
ref = {}
for pc in PCS:
    m = np.where(pv == pc)[0]
    if not len(m): continue
    c = Vector(rest[m].mean(0)); loc, n, fi, d = T0.find_nearest(c)
    # barycentric anchor on that face: the seat point follows the face
    f = cfv[fi]; P = rest[list(f)]
    w = np.linalg.lstsq(np.c_[P.T, np.ones((3, 1)).T.reshape(3, 1) * 0 + 1].T if False else np.vstack([P.T, np.ones(len(f))]), np.r_[np.array(loc), 1.0], rcond=None)[0]
    ref[pc] = (m, fi, w, d)
for cl in [x for x in ('Standing', 'Walking', 'Attack', 'Hit', 'Death', 'Fidget') if x in bpy.data.actions]:
    act = bpy.data.actions[cl]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range); worst = (0.0, None, None)
    for fr in range(f0, f1 + 1):
        sc.frame_set(fr)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); mm = ev.to_mesh()
        P = np.array([(body.matrix_world @ v.co)[:] for v in mm.vertices]); ev.to_mesh_clear()
        for pc, (m, fi, w, d0) in ref.items():
            seat = (P[list(cfv[fi])] * w[:, None]).sum(0); c = P[m].mean(0)
            # rest offset from the seat, carried rigidly: compare distances (gap change) and the drift
            drift = abs(np.linalg.norm(c - seat) - d0)
            if drift > worst[0]:
                worst = (drift, pc, fr)
    print('ACCGAP', cl.ljust(9), 'worst change of the piece-to-seat distance mm', round(worst[0] * 1000, 1), 'piece', worst[1], 'frame', worst[2])
