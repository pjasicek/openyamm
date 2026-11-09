"""Apply the v2 straightening (scripts/sym_v2.py: head turn onto x = 0, then the midline field) to any points given
in the v1 rest frame (static_v4 coordinates), e.g. the v1 textured mesh used as the bake source.
Library: `straighten(co) -> co'`; Blender-free (numpy + scipy)."""
import numpy as np
from pathlib import Path
from scipy.ndimage import map_coordinates
from scipy.spatial.transform import Rotation
W = Path(__file__).resolve().parents[1] / 'work/v2'
ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))


def straighten(co):
    co = np.array(co, float); x, y, z = co.T; ax = np.abs(x)
    S = np.load(W / 'sym_params.npz'); pivot, rv, target = S['pivot'], S['rotvec'], S['target']
    wing0 = (ax > .085) & (z > .255) & (y > -.33) & (y < -.08)
    head = (y < -.31) & (z > .37) & ~wing0 & (ax < .10)
    neck_band = (y < -.24) & (z > .30) & ~wing0 & (ax < .10)
    w = np.where(head, 1., np.where(neck_band, ss((z - .325) / .06), 0.))
    for i in np.where(w > 0)[0]:
        R = Rotation.from_rotvec(rv * w[i]).as_matrix(); co[i] = (co[i] - pivot) @ R.T + pivot + w[i] * (target - pivot)
    f = np.load(W / 'midline_field.npz'); ys, zs, cf = f['ys'], f['zs'], f['c']
    field = lambda p: map_coordinates(cf, [(p[:, 1] - ys[0]) / (ys[1] - ys[0]), (p[:, 2] - zs[0]) / (zs[1] - zs[0])], order=1, mode='nearest')
    x, y, z = co.T; ax = np.abs(x); wing = (ax > .085) & (z > .255) & (y > -.33) & (y < -.08)
    shift = field(co)
    for s in (1, -1):
        sw = wing & (x * s > 0); root = ss((ax - .085) / .05)
        shift[sw] = (1 - root[sw]) * shift[sw] + root[sw] * field(np.array([[s * .075, -.262, .30]]))[0]
    co[:, 0] -= shift
    return co
