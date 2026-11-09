"""Gate copy attributes: the project gates (g5_hand_stretch.py, g6_contacts.py) read the point attributes 'garment',
'finger' and 'piece' of the mm7_m262_claude master; each vertex of a gate copy (gate_import.py) takes them from the
nearest master vertex in the rest pose. Args: -- <gate blend> <master blend>"""
import bpy, sys, os
import numpy as np
from mathutils.kdtree import KDTree
gate, master = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(master))
mb = bpy.data.objects['Body']; mr = bpy.data.objects['Rig']
mr.animation_data_create(); mr.animation_data.action = None
for pb in mr.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get(); ev = mb.evaluated_get(dg); m = ev.to_mesh()
mco = np.array([tuple(mb.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
attrs = {}
for n in ('garment', 'finger', 'piece'):
    if n in mb.data.attributes:
        a = np.zeros(len(mb.data.vertices), np.int32); mb.data.attributes[n].data.foreach_get('value', a); attrs[n] = a
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(gate))
gb = bpy.data.objects['Body']; gco = np.array([tuple(gb.matrix_world @ v.co) for v in gb.data.vertices])
kd = KDTree(len(mco))
for i, c in enumerate(mco):
    kd.insert(c, i)
kd.balance()
hits = [kd.find(c) for c in gco]; idx = np.array([h[1] for h in hits]); dist = np.array([h[2] for h in hits])
for n, a in attrs.items():
    at = gb.data.attributes.get(n) or gb.data.attributes.new(n, 'INT', 'POINT')
    at.data.foreach_set('value', a[idx].tolist())
print('GATEATTRS', list(attrs), 'vertices', len(gco), 'nearest master vertex mm p99', round(float(np.percentile(dist, 99)) * 1000, 2), 'max', round(float(dist.max()) * 1000, 2))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(gate))
