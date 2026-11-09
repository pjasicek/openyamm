"""Move a grafted head rigidly in the finished rest mesh (after the UVs, so the body unwrap and both retextures stay
valid), its joint loft blending the shift along its length (vertex attribute loft_s from graft_hydra.py; t = loft_s /
the loft's length, 1 at our neck ring, which stays put). Head 3's lower jaw sat inside the front of its own neck
(user review 2026-10-20): SHIFT[k] = (forward along the head bone's horizontal direction, up) in m.
Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
SHIFT = {3: (0.075, 0.045)}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
ob = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = ob.data
part = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', part)
own = np.zeros(len(me.vertices), np.int32); me.attributes['chain_owner'].data.foreach_get('value', own)
ls = np.zeros(len(me.vertices)); me.attributes['loft_s'].data.foreach_get('value', ls)
co = np.array([tuple(v.co) for v in me.vertices])
for k, (fwd, up) in SHIFT.items():
    head_v = np.unique(np.concatenate([list(p.vertices) for p in me.polygons if part[p.index] == k]))
    b = rig.data.bones[f'Head{k}']
    d = np.array(b.tail_local) - np.array(b.head_local); d[2] = 0; d /= np.linalg.norm(d)
    off = d * fwd + np.array([0, 0, up])
    is_head = np.zeros(len(co), bool); is_head[head_v] = True
    loft = (own == k) & (ls > 1e-6) & ~is_head
    L = ls[loft].max() if loft.any() else 1.0
    t = np.clip(ls[loft] / L, 0, 1); w = 1 - t * t * (3 - 2 * t)
    co[is_head] += off
    co[loft] += w[:, None] * off
    print(f'SHIFT head {k}: {int(is_head.sum())} head verts, {int(loft.sum())} loft verts (length {L:.3f} m), offset {off.round(3)}')
me.vertices.foreach_set('co', co.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
