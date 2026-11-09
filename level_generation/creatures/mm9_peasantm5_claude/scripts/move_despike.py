"""Despike the fit's total move (PeasantM5, 2026-11-02): single vertices the ray/nearest sources pulled far from their ring
(a 47 mm dent in the upper back, boot-cuff lips folded in 5 cm). The total move (fitted - original, per vertex) is compared with
the median of its 1-ring's moves; where it differs by more than TOL it is replaced by the ring mean; 4 passes; then 2 gentle
smoothing passes of the whole move field (pinned vertices, whose move is 0, stay 0). Positions only.
Args: -- <original blend> <fitted blend> <out blend> [TOL 0.012]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
ORIG, FIT, OUT = a[:3]; TOL = float(a[3]) if len(a) > 3 else 0.012
bpy.ops.wm.open_mainfile(filepath=ORIG)
c0 = np.array([v.co[:] for v in bpy.data.objects['Body'].data.vertices])
bpy.ops.wm.open_mainfile(filepath=FIT)
me = bpy.data.objects['Body'].data
c1 = np.array([v.co[:] for v in me.vertices]); mv = c1 - c0
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
nb = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
pin = np.linalg.norm(mv, axis=1) < 1e-6
fixed = 0
for _ in range(4):
    new = mv.copy()
    for i, js in enumerate(nb):
        if pin[i] or len(js) < 2: continue
        med = np.median(mv[js], 0)
        if np.linalg.norm(mv[i] - med) > TOL:
            new[i] = mv[js].mean(0); fixed += 1
    mv = new
for _ in range(2):
    new = mv.copy()
    for i, js in enumerate(nb):
        if pin[i] or not js: continue
        new[i] = 0.7 * mv[i] + 0.3 * mv[js].mean(0)
    mv = new
for v in me.vertices: v.co = Vector(c0[v.index] + mv[v.index])
me.update(); bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('DESPIKE replaced', fixed, 'move max mm', round(float(np.linalg.norm(mv, axis=1).max() * 1000), 1))
