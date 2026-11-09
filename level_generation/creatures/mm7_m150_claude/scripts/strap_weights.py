"""Shoulder straps (piece 3) and stray feather cards re-weighted in place on the textured master (work/rig_v6.blend), so the topology the
retextures were painted on is untouched: each strap vertex copies the skin shell's weights (piece 0, 4 nearest,
inverse distance) WITHOUT the arm chain but WITH the clavicle. The chain's garment rule 3 drops the clavicle too, so
the strap lagged behind the shoulder and the torso's modelled stud bumps poked through it in posed clips (user review
of the viewer: brown ovals on the straps). Args: -- <blend>"""
import bpy, sys, os
import numpy as np
from mathutils.kdtree import KDTree
blend = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([tuple(v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
names = [g.name for g in body.vertex_groups]
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight
ARMS = [i for i, n in enumerate(names) if any(k in n for k in ('UpperArm', 'Forearm', 'Hand', 'Finger'))]
skin = np.where(pv == 0)[0]
kd = KDTree(len(skin))
for i, s in enumerate(skin):
    kd.insert(co[s], i)
kd.balance()
strap = np.where(pv == 3)[0]
for i in strap:
    hits = kd.find_n(co[i], 4)
    w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
    new = (w[:, None] * Wt[[skin[h[1]] for h in hits]]).sum(0) / w.sum()
    new[ARMS] = 0; new /= max(new.sum(), 1e-9)
    for g in body.vertex_groups:
        g.remove([int(i)])
    for j in np.nonzero(new > 1e-4)[0]:
        body.vertex_groups[int(j)].add([int(i)], float(new[j]), 'REPLACE')
# feather cards left on the body by step1_clean's label rules (P124: a card behind the right shoulder, centre |x| 0.29)
# took Meshy's upper-arm weights and swung out with the raised sword arm (user review: a dark strip by the arm): they copy
# the nearest wing vertices (garment 5) instead
STRAY = [int(x) for x in os.environ.get('STRAY_CARDS', '124').split(',') if x]
gv = np.zeros(nv, np.int32); me.attributes['garment'].data.foreach_get('value', gv)
wing = np.where(gv == 5)[0]
kw = KDTree(len(wing))
for i, s_ in enumerate(wing):
    kw.insert(co[s_], i)
kw.balance()
nst = 0
for i in np.where(np.isin(pv, STRAY))[0]:
    hits = kw.find_n(co[i], 3)
    w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
    new = (w[:, None] * Wt[[wing[h[1]] for h in hits]]).sum(0) / w.sum()
    for g in body.vertex_groups:
        g.remove([int(i)])
    for j in np.nonzero(new > 1e-4)[0]:
        body.vertex_groups[int(j)].add([int(i)], float(new[j]), 'REPLACE')
    nst += 1
print('STRAPWEIGHTS stray feather-card vertices moved to the wing', nst, 'pieces', STRAY)
cl = [names.index(n) for n in ('B_L_Clavicle', 'B_R_Clavicle')]
print('STRAPWEIGHTS vertices', len(strap), 'mean clavicle share', round(float(np.mean([sum(e.weight for e in me.vertices[int(i)].groups if e.group in cl) for i in strap])), 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend))
