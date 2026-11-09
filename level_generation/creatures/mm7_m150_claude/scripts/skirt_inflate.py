"""Skirt and tab clearance in place on the textured master (work/rig_v6.blend), once (flag on the rig): the Smart
Topology skirt sits within 0.5 cm of the thighs at rest, so any lag of the dress weights shows the thigh through it
(user review: the left leg bleeds through the skirt in the attack). Every skirt (garment 6) and tab (garment 7) vertex
below the belt (z < BELT - 0.04) that is nearer than GAP to the thigh skin (piece 0 with thigh weight > 0.3) moves
outward along the direction from that skin point by the shortfall, fading in over the 4 cm below the belt so the
waistband stays on the belt. Geometry only: UVs and weights are kept. Args: -- <blend>"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
blend = sys.argv[sys.argv.index('--') + 1]
GAP, BELT = float(os.environ.get('SKIRT_GAP', '0.02')), float(os.environ.get('SKIRT_BELT', '1.04'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
if rig.get('skirt_inflate_applied'):
    print('SKIRTINFLATE already applied'); raise SystemExit
co = np.array([tuple(v.co) for v in me.vertices])
pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
gv = np.zeros(len(co), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
gi = {g.name: g.index for g in body.vertex_groups}
thw = np.array([sum(e.weight for e in v.groups if e.group in (gi['B_L_Thigh'], gi['B_R_Thigh'])) for v in me.vertices])
skin = np.where((pv == 0) & (thw > 0.3) & (co[:, 2] < BELT))[0]
kd = KDTree(len(skin))
for i, s in enumerate(skin):
    kd.insert(co[s], i)
kd.balance()
moved, worst = 0, 0.0
for i in np.where(np.isin(gv, [6, 7]) & (co[:, 2] < BELT))[0]:
    p = Vector(co[i]); q, j, d = kd.find(p)
    fade = min(max((BELT - co[i, 2]) / 0.04, 0.0), 1.0)
    if d < GAP and fade > 0:
        n = (p - q).normalized() if d > 1e-5 else Vector((np.sign(co[i, 0]) or 1.0, -0.5, 0)).normalized()
        n.z = 0; n.normalize()
        me.vertices[i].co = p + n * (GAP - d) * fade
        moved += 1; worst = max(worst, GAP - d)
me.update()
rig['skirt_inflate_applied'] = 1
print('SKIRTINFLATE vertices moved', moved, 'largest push cm', round(worst * 100, 2), 'gap', GAP)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend))
