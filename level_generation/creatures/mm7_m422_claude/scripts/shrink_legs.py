"""Thin the trousers hidden inside the coat skirt (after weights_robe.py, before sheet_rig.py; weights untouched).
Smart Topology filled the coat with wide trousers (13-14.5 cm from the leg line at the hips) while the coat skirt hangs
14 cm behind the hip line, so every backward leg swing put the thigh through the closed back of the skirt (walk,
review/poke/). Garment 15 vertices above Z0 move toward their own leg's bone line (thigh head -> calf head -> foot
head, by the vertex's side) by a factor ramping from 1 at Z0 to FMIN at Z1 (smoothstep). The boots and shins below
the hem margin keep their shape. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg
Z0, Z1, FMIN = 0.45, 0.62, float(cfg.C.get('hidden_leg_scale', 0.62))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
gv = np.array([x.value for x in me.attributes['garment'].data])
co = np.array([v.co[:] for v in me.vertices])
J = lambda n: np.array(rig.data.bones[n].head_local)


def near(p, a, b):
    ab = b - a; t = np.clip((p - a) @ ab / (ab @ ab), 0, 1); return a + t * ab


moved = 0; dmax = 0.0
for i in np.where((gv == 15) & (co[:, 2] > Z0))[0]:
    s = 'L' if co[i, 0] > 0 else 'R'
    th, ca, ft = J(f'B_{s}_Thigh'), J(f'B_{s}_Calf'), J(f'B_{s}_Foot')
    p = co[i]
    q1, q2 = near(p, th, ca), near(p, ca, ft)
    q = q1 if np.linalg.norm(p - q1) < np.linalg.norm(p - q2) else q2
    x = min(1.0, max(0.0, (p[2] - Z0) / (Z1 - Z0))); f = 1 - (1 - FMIN) * x * x * (3 - 2 * x)
    new = q + (p - q) * f
    dmax = max(dmax, float(np.linalg.norm(new - p))); co[i] = new; moved += 1
me.vertices.foreach_set('co', co.ravel()); me.update()
print('SHRINKLEGS moved', moved, 'max move cm', round(dmax * 100, 1))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
