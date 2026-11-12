"""half_keys.py's helper rule as a function (follow-up 3, 2026-11-12): the helper's local TRS under its node parent pn, with
its skin rotation half way between the parent side and the child c, turning about the child's joint."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import matrix_quaternion  # noqa: E402


def half_rot(R):
    a = np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))
    if a < 1e-6: return np.eye(3)
    v = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / (2 * np.sin(a)) if a < np.pi - 1e-3 else None
    if v is None:
        w, V = np.linalg.eigh((R + R.T) / 2); v = V[:, w.argmax()]
    t = a / 2; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * K @ K


def helper_local(W, ix, ibm, c, pn):
    Sp = W[ix[pn]] @ ibm[pn]; Sc = W[ix[c]] @ ibm[c]
    Sh = Sp[:3, :3] @ half_rot(Sp[:3, :3].T @ Sc[:3, :3])
    Bc = np.linalg.inv(ibm[c])
    Wh = np.eye(4); Wh[:3, :3] = Sh @ Bc[:3, :3]; Wh[:3, 3] = W[ix[c]][:3, 3]
    L = np.linalg.inv(W[ix[pn]]) @ Wh
    return L[:3, 3], matrix_quaternion(L[:3, :3])
