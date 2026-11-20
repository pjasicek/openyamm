"""Pull the spikes of the grafted hands' forearm stub back into the sleeve (viewer close-up 2026-11-02: one stub vertex
per side 2.9 cm off the forearm axis, 4-5 mm beyond its ring, showed as a skin shard along the cuff). Hand-face vertices
up the sleeve (axis t < T_MAX from the hand joint) whose radius exceeds their ring's median (vertices within 6 mm of t)
by more than SPIKE move radially to median + SPIKE. Positions only. Args: <in blend> <out blend> [spike 0.002] [t_max 0.006]"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
SPIKE = float(a[2]) if len(a) > 2 else 0.002
TMAX = float(a[3]) if len(a) > 3 else 0.006
bpy.ops.wm.open_mainfile(filepath=IN)
o = bpy.data.objects['Body']; me = o.data; rig = o.parent
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
hn = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hn)
hv = sorted({v for p in me.polygons if hn[p.index] for v in p.vertices})
rep = {}
for s in 'LR':
    fa = rig.matrix_world @ rig.data.bones[f'Bip01 {s} Forearm'].head_local
    hd = rig.matrix_world @ rig.data.bones[f'Bip01 {s} Hand'].head_local
    ax = (hd - fa).normalized()
    ids = [j for j in hv if np.sign(me.vertices[j].co.x) == np.sign(hd.x)]
    T = np.array([(me.vertices[j].co - hd).dot(ax) for j in ids])
    R = np.array([((me.vertices[j].co - hd) - ax * t).length for j, t in zip(ids, T)])
    moved = []
    for k, j in enumerate(ids):
        if T[k] > TMAX:
            continue
        ring = np.abs(T - T[k]) < 0.006
        med = float(np.median(R[ring]))
        if R[k] > med + SPIKE:
            p = me.vertices[j].co - hd
            radial = p - ax * T[k]
            me.vertices[j].co = hd + ax * T[k] + radial * ((med + SPIKE) / R[k])
            moved.append((j, round(float(R[k] - med) * 1000, 1)))
    rep[s] = moved
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('DESPIKE', rep)
