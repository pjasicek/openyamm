"""Near-contact zones of the heads (the head-intersection gate's pairs: head k against the other heads, other necks
and the body above 1.05 m): at every half frame of every clip, source faces of head k with a vertex within D of
those surfaces, and the faces they come close to, are kept exactly in the next ladder. The batch I heads clear each
other by a few millimetres in places (head 1's narrowed fins beside head 2's crest); the collapse's optimal placement
moves a decimated vertex that far and the reduced heads touched in every frame.
Usage: blender -b -P contact_lock.py -- <base keep .npy> <out .npy> [D m, default 0.015]"""
import os, sys, bpy
import numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; base, out = a[:2]; D = float(a[2]) if len(a) > 2 else .015
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
sc = bpy.context.scene; ob = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = ob.data
L = np.load(os.path.join(HERE, 'work', 'face_labels.npz')); part, own = L['part'], L['chain_owner']
me.calc_loop_triangles(); polys = [list(t.vertices) for t in me.loop_triangles]
assert len(polys) == len(part)
face_own = np.array([np.bincount(own[p], minlength=6).argmax() for p in polys])
zrest = np.array([me.vertices[p[0]].co.z for p in polys])
heads = {k: np.flatnonzero(part == k) for k in range(1, 6)}
others = {k: np.flatnonzero((part != k) & (face_own != k) & ((part > 0) | ((face_own > 0) & (zrest > 1.05)))) for k in range(1, 6)}
hverts = {k: np.unique(np.array(polys)[heads[k]]) for k in range(1, 6)}
mark = np.zeros(len(polys), bool); vnear = np.zeros(len(me.vertices), bool)
for act in bpy.data.actions:
    rig.animation_data.action = act; f0, f1 = (int(x) for x in act.frame_range)
    for t in np.arange(f0, f1 + 1e-6, .5):  # half frames of the 24 fps import (48 Hz; the clips are keyed at 30)
        sc.frame_set(int(t), subframe=float(t - int(t)))
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        co = [tuple(ob.matrix_world @ v.co) for v in m.vertices]; ev.to_mesh_clear()
        for k in range(1, 6):
            tree = BVHTree.FromPolygons(co, [polys[i] for i in others[k]])
            for vi in hverts[k]:
                hit = tree.find_nearest(co[vi], D)
                if hit[0] is not None:
                    vnear[vi] = True; mark[others[k][hit[2]]] = True
    print('CONTACT', act.name, int(vnear.sum()), int(mark.sum()), flush=True)
mark |= vnear[np.array(polys)].any(1) & (part > 0)
keep = np.load(base); n0 = int(keep.sum()); keep = keep | mark
np.save(os.path.join(HERE, out), keep)
print('CONTACTLOCK', int(mark.sum()), 'faces near contact (per head', {k: int((mark & (part == k)).sum()) for k in range(1, 6)},
      'necks/body', int((mark & (part == 0)).sum()), '); kept', n0, '->', int(keep.sum()))
