"""MM9's PeasantDM3 hides the ears under the long hair; DM1's Meshy head keeps ears that stood out of the gap between
the cheek and the lengthened hair curtain (review/t3_faces_2row.png). Positions only (the paid head paint stays valid):
head-shell vertices in the ear zone (z 0.405..0.50, y -0.035..0.065 at rest, lateral offset from the head axis above
LAT0) are pulled toward the skull: lat' = LAT0 + (lat - LAT0) * K, feathered over 1.5 cm at the zone's edges.
Args: -- <in blend> <out blend> [K 0.25] [LAT0 0.074]"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts_lib as L
argv = sys.argv[sys.argv.index('--') + 1:]
K = float(argv[2]) if len(argv) > 2 else 0.25
LAT0 = float(argv[3]) if len(argv) > 3 else 0.074
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
co = L.rest_coords(body); lab = L.loose_parts(me)
cand = np.where((co[:, 2] > 0.40) & (co[:, 2] < 0.47))[0]
shell = lab[cand[np.argmin(co[cand, 1])]]
S = np.where(lab == shell)[0]
xc = (co[S, 0].min() + co[S, 0].max()) / 2
def ramp(v, lo, hi, f=0.015):
    return np.clip((v - lo) / f, 0, 1) * np.clip((hi - v) / f, 0, 1)
p = co[S]
w = ramp(p[:, 2], 0.405, 0.50) * ramp(p[:, 1], -0.035, 0.065)
lat = np.abs(p[:, 0] - xc); sgn = np.sign(p[:, 0] - xc)
new_lat = np.where(lat > LAT0, LAT0 + (lat - LAT0) * K, lat)
nx = xc + sgn * (lat + (new_lat - lat) * w)
moved = np.abs(nx - p[:, 0])
new = co.copy(); new[S, 0] = nx
me.vertices.foreach_set('co', new.reshape(-1)); me.update()
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
print('EARFLAT', json.dumps({'moved': int((moved > 1e-4).sum()), 'max_cm': round(float(moved.max()) * 100, 2), 'axis_x': round(xc, 4)}))
