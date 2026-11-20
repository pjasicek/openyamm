"""Separate the sleeve ruffles from the dress (in place on work/rig_textured_uv.blend; idempotent).

Smart Topology fused each sleeve ruffle's lowest tip to the dress side at the hip (A-pose contact), and Meshy's
weights gave those ruffle tips up to 0.7 pelvis. When the arm moved, the bridge faces stretched up to 18x and the
ruffles splayed into spikes (G4 right-forearm p99 3.6-4.2 in Hit, Running and Death; review/textured_frames).
- bridge faces: faces with an arm vertex (arm-bone weight >= 0.5) and a dress vertex (pelvis/dress weight >= 0.5)
  near the hip are deleted (UVs of every other face unchanged);
- ruffle vertices (piece 0, arm-bone weight >= 0.15, below 1.15 m) keep arm bones only, renormalised.
Prints the counts. Run before export_runtime.py."""
import bpy, bmesh
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
path = P / 'work/rig_textured_uv.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
names = [g.name for g in body.vertex_groups]
ARM = [i for i, n in enumerate(names) if any(k in n for k in ('UpperArm', 'Forearm', '_Hand', 'Finger'))]
DRESS = [i for i, n in enumerate(names) if n == 'B_Pelvis' or n.startswith('Dress_')]
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([v.co[:] for v in me.vertices])
W = np.zeros((len(me.vertices), len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
arm_w = W[:, ARM].sum(1); dress_w = W[:, DRESS].sum(1)
arm_v = (pv == 0) & (arm_w >= 0.5); dress_v = (pv == 0) & (dress_w >= 0.5) & (co[:, 2] < 1.10)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bridge = [f for f in bm.faces if any(arm_v[v.index] for v in f.verts) and any(dress_v[v.index] for v in f.verts)
          and abs(f.calc_center_median().x) > 0.15]
bmesh.ops.delete(bm, geom=bridge, context='FACES_ONLY')
bm.to_mesh(me); bm.free(); me.update()
ruffle = np.flatnonzero((pv == 0) & (arm_w >= 0.15) & (co[:, 2] < 1.15))
for i in ruffle:
    row = np.zeros(len(names)); row[ARM] = W[i, ARM]; row /= row.sum()
    for e in list(me.vertices[i].groups):
        body.vertex_groups[e.group].remove([int(i)])
    for j in np.flatnonzero(row > 1e-5):
        body.vertex_groups[int(j)].add([int(i)], float(row[j]), 'REPLACE')
bpy.ops.wm.save_mainfile()
print('CUFFS bridge faces deleted', len(bridge), 'ruffle vertices on arm bones only', len(ruffle),
      'triangles', sum(len(p.vertices) - 2 for p in me.polygons))
