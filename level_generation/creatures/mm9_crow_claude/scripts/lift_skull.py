"""Skull lift (2026-10-30, second head pass; after uv_atlas_v4.py and the 4K retexture, before dump_uv3d/bake_ao).
Topology and UVs are unchanged, so the retexture stays valid.

Args: <uv blend (uv_v4)> <out blend> <report json> [angle deg]

The head was not rolled (in the flight loop the beak hook points down, roll within a few degrees of MM9's Xhead), but
it read upside down: the Meshy crow looks down in the bind pose with its beak attached to the bottom of the skull, so
the skull sat behind the beak base, on the beak line (+3 mm above it; MM9's skull sits +27 mm above its beak line).
Once MM9's flight raises the head ~55 deg, that skull and throat hang under the beak as a chin, with a flat wall above
the beak: the crown seems to face down. The skull (everything weighted to Xhead, eyes included; not the beak) is
turned up about the beak base by ANGLE deg toward the crown side, blended by its Xhead weight into the neck, so the
crown rises above the beak line and the throat tucks in. The beak keeps its direction (matched to MM9 earlier).
"""
import bpy, sys, json, math
import numpy as np
from mathutils import Vector, Quaternion

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
ANGLE = float(argv[3]) if len(argv) > 3 else 30.0

bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
me = body.data
n = len(me.vertices)
P = np.array([tuple(v.co) for v in me.vertices])
piece = np.array([d.value for d in me.attributes['piece'].data])
gi = {g.name: g.index for g in body.vertex_groups}


def weight(name):
    w = np.zeros(n)
    for v in me.vertices:
        for g in v.groups:
            if g.group == gi[name]:
                w[v.index] = g.weight
    return w


wb, wh, wp = weight('Xbeak'), weight('Xhead'), weight('Xheadpiv')
eyes = piece == 2
E = P[eyes].mean(0)
bk = np.nonzero(wb > 0.9)[0]
d = np.linalg.norm(P[bk] - E, axis=1)
base = P[bk[np.argsort(d)[:max(3, len(bk) // 10)]]].mean(0)
tip = P[bk[np.argsort(d)[-max(3, len(bk) // 10):]]].mean(0)
axis = (tip - base) / np.linalg.norm(tip - base)
crown = np.array([0.0, -axis[2], axis[1]])          # +90 deg from the beak axis about +X: the forward-up side
crown = crown if crown[2] > 0 else -crown


def skull_offset(Q):
    s = Q[(wh > 0.5) & (wb < 0.1)] - base
    s = s - np.outer(s @ axis, axis)
    return float((s @ crown).mean() * 1000)


before = skull_offset(P)
# blend: the full turn for the skull (Xhead, eyes), half for Xheadpiv, none for the beak and the neck behind
k = np.clip(wh + 0.5 * wp, 0, 1) * (1 - np.clip(wb, 0, 1))
k[eyes] = 1.0
P2 = P.copy()
for i in np.nonzero(k > 1e-4)[0]:
    q = Quaternion(Vector((1, 0, 0)), math.radians(ANGLE) * k[i])
    P2[i] = base + np.array(q @ Vector(P[i] - base))
after = skull_offset(P2)
for v in me.vertices:
    v.co = Vector(P2[v.index])
me.update()
rep = {'angle_deg': ANGLE, 'beak_base': base.tolist(), 'beak_axis': axis.tolist(),
       'skull_above_beak_line_mm': [before, after], 'moved': int((k > 1e-4).sum())}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('LIFT ' + json.dumps(rep))
