"""Numbers for the fit on the cleaned blend: MM9 joints (Blender coords, figure's right = -x) and ring centres of our mesh by part.
Args: <clean blend>"""
import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
arm = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']; me = body.data
for b in arm.data.bones:
    if ' L ' not in b.name: print('J', b.name, np.round(np.array(tuple(arm.matrix_world @ b.head_local)), 3).tolist())
P = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
vp = np.zeros(len(P), int)
for p in me.polygons:
    for v in p.vertices: vp[v] = fp[p.index]
for k in sorted(set(vp.tolist())):
    q = P[vp == k]; print('PART', k, len(q), np.round(q.min(0), 3).tolist(), np.round(q.max(0), 3).tolist())
A = P[np.isin(vp, (1, 4)) & (P[:, 0] < 0)]
print('arm rings by x (armour+glove, right side): x centre extent n')
for x in np.arange(0.18, 0.56, 0.02):
    m = (A[:, 0] < -x + 0.01) & (A[:, 0] > -x - 0.01) & (A[:, 2] > -0.2)
    if m.sum() > 3:
        c = 0.5 * (A[m].min(0) + A[m].max(0)); print(round(x, 2), np.round(c, 3).tolist(), np.round(np.ptp(A[m], axis=0), 3).tolist(), int(m.sum()))
L = P[(vp == 5) & (P[:, 0] < 0)]
print('leg rings by z (legs, right side)')
for z in np.arange(0.15, -0.95, -0.05):
    m = (L[:, 2] < z + 0.01) & (L[:, 2] > z - 0.01)
    if m.sum() > 3:
        c = 0.5 * (L[m].min(0) + L[m].max(0)); print(round(z, 2), np.round(c, 3).tolist(), np.round(np.ptp(L[m], axis=0), 3).tolist(), int(m.sum()))
H = P[np.isin(vp, (20,))]
print('face/neck rings by z')
for z in np.arange(0.95, 0.55, -0.03):
    m = (H[:, 2] < z + 0.01) & (H[:, 2] > z - 0.01)
    if m.sum() > 3:
        c = 0.5 * (H[m].min(0) + H[m].max(0)); print(round(z, 2), np.round(c, 3).tolist(), np.round(np.ptp(H[m], axis=0), 3).tolist(), int(m.sum()))
