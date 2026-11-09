"""Drop needle and degenerate faces from the UV npz BEFORE the Meshy upload (F5 lesson: needle charts reaching across the atlas get painted
as thin lines over other charts). Needle: UV edge > 0.15 with 3D area < 1e-5 m2; degenerate: UV area < 1e-10 with 3D area < 1e-6 m2, or 3D
area < 1e-9. All are sub-millimetre slivers (neck-plane cut, chin and hair-parting midlines). Args: <uv_orig npz> <out uv npz>"""
import sys
import numpy as np
D = dict(np.load(sys.argv[1])); co, tri, uv = D['co'], D['tri'], D['uv']
a3 = np.linalg.norm(np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]]), axis=1) / 2
e = np.max([np.linalg.norm(uv[tri[:, i]] - uv[tri[:, (i + 1) % 3]], axis=1) for i in range(3)], 0)
u2 = uv[tri]; au = np.abs((u2[:, 1, 0] - u2[:, 0, 0]) * (u2[:, 2, 1] - u2[:, 0, 1]) - (u2[:, 2, 0] - u2[:, 0, 0]) * (u2[:, 1, 1] - u2[:, 0, 1])) / 2
bad = ((e > 0.15) & (a3 < 1e-5)) | ((au < 1e-10) & (a3 < 1e-6)) | (a3 < 1e-9)
for k in ('tri', 'mat', 'inner'):
    D[k] = D[k][~bad]
np.savez(sys.argv[2], **D); print('DROPPED', int(bad.sum()), 'faces; left', len(D['tri']), 'zero-uv-area', int(((au < 1e-10) & ~bad).sum()))
