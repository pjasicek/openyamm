"""After finish_mer.py (UVs frozen; positions only, faces, UVs and paint unchanged): the Smart Topology's thighs inside the tunic are a filler
as wide as the skirt (radius p90 17 cm, max 21 cm), so the robe chains, which hang toward plumb, showed them through the cloth (a brown
streak and smooth green blobs in Standing). Leg vertices (part 5) are pulled toward their thigh's axis to at most R_MAX, blended in from
Z0 (under the knee) to Z1; the visible boot and shin below are unchanged. Args: <in blend> <out blend>"""
import bpy, sys
import numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
R_MAX, Z0, Z1 = 0.085, -0.47, -0.36
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
H = lambda n: np.array(tuple(rig.matrix_world @ rig.data.bones[n].head_local))
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
legv = sorted({v for p in me.polygons if fp[p.index] == 5 for v in p.vertices})
moved = 0; mx = 0.0
for i in legv:
    v = me.vertices[i]; P = np.array(tuple(v.co))
    if P[2] < Z0: continue
    S = 'R' if P[0] < 0 else 'L'
    a, b = H(f'Bip01 {S} Thigh'), H(f'Bip01 {S} Calf')
    ab = b - a; t = np.clip((P - a) @ ab / (ab @ ab), 0, 1); c = a + t * ab; d = P - c; r = np.linalg.norm(d)
    x = np.clip((P[2] - Z0) / (Z1 - Z0), 0, 1); w = x * x * (3 - 2 * x)
    rn = r * (1 - w) + min(r, R_MAX) * w
    if r > 1e-6 and rn < r - 1e-5:
        v.co = Vector((c + d * (rn / r)).tolist()); moved += 1; mx = max(mx, r - rn)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('SLIMLEGS moved', moved, 'max cm', round(mx * 100, 1))
