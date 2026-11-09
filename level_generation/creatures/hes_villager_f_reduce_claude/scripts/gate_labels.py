"""Gate copy labels from the source project's gated master: the point attributes 'garment' and 'piece' of its Body
(rest mesh, world space) copied to the gate copy's Body (work/gate_<label>.blend from gate_import.py) by the nearest
master vertex. Each connected part of the gate copy first votes for its master piece (majority of nearest vertices),
and its vertices then take the nearest vertex of that piece only, so a pouch beside the coat never takes the coat's
labels (per-piece labels, retopology playbook). Prints the rest-pose distance to the master (frames must match).
Args: -- <gate blend> <master blend>"""
import bpy, sys, os
import numpy as np
from mathutils.kdtree import KDTree


def kd(points):
    t = KDTree(len(points))
    for i, c in enumerate(points):
        t.insert(c, i)
    t.balance(); return t
gate, master = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(master))
mb = bpy.data.objects['Body']; mm = mb.data
MW = np.array(mb.matrix_world)
mco = np.array([v.co[:] for v in mm.vertices]) @ MW[:3, :3].T + MW[:3, 3]
att = {n: np.array([x.value for x in mm.attributes[n].data]) for n in ('garment', 'piece', 'finger') if n in mm.attributes}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(gate))
gb = bpy.data.objects['Body']; gm = gb.data
GW = np.array(gb.matrix_world)
gco = np.array([v.co[:] for v in gm.vertices]) @ GW[:3, :3].T + GW[:3, 3]
gpc = np.array([x.value for x in gm.attributes['piece'].data])
tree = kd(mco); q = [tree.find(c) for c in gco]
d0 = np.array([x[2] for x in q]); nn = np.array([x[1] for x in q])
out = {n: np.zeros(len(gco), np.int32) for n in att}
for p in np.unique(gpc):
    m = gpc == p
    mp = np.bincount(att['piece'][nn[m]]).argmax()
    ids = np.where(att['piece'] == mp)[0]; t = kd(mco[ids]); j = np.array([t.find(c)[1] for c in gco[m]])
    for n in att:
        out[n][m] = att[n][ids[j]]
for n, val in out.items():
    a = gm.attributes.get(n) or gm.attributes.new(n, 'INT', 'POINT')
    a.data.foreach_set('value', val.tolist())
print('GATELABELS', os.path.basename(gate), 'rest distance to master p50/p99/max mm',
      np.round(np.percentile(d0, [50, 99, 100]) * 1000, 2).tolist(),
      'garments', {int(k): int((out['garment'] == k).sum()) for k in np.unique(out['garment'])})
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(gate))
