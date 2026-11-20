"""Sliver triangles near the wrists of a GLB's LOD0 (and whether their corners are new vs the installed GLB)."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import motion_audit
a = motion_audit.Audit(sys.argv[1]); b = motion_audit.Audit(sys.argv[2])
old = cKDTree(b.rest)
_, w = a.pose(None, 0)[0], a.pose(None, 0)[3]
for side in ('LeftHand', 'RightHand'):
    J = a.model.joints[a.joint_names.index(side)]
    c = w[J][:3, 3]
    P = a.rest; T = a.tris
    cen = P[T].mean(1)
    near = np.where(np.linalg.norm(cen - c, axis=1) < 0.07)[0]
    for i in near:
        p = P[T[i]]
        e = [np.linalg.norm(p[(k + 1) % 3] - p[k]) for k in range(3)]
        area = 0.5 * np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0]))
        alt = 2 * area / max(e)
        if max(e) / max(alt, 1e-9) > 8 and max(e) > 0.012:
            isnew = [old.query(x)[0] > 1e-5 for x in p]
            print(side, i, 'long', round(max(e), 4), 'ratio', round(max(e) / max(alt, 1e-9), 1), 'new', isnew, 'centre', np.round(cen[i], 3))
