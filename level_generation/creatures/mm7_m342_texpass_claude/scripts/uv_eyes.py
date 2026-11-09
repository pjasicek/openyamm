"""Eyeball charts for procedural eyes (close-up fix 2026-11-01): the paid layout work/uv_cc4_fine.npz with each
eyeball (pieces 22 right, 30 left) re-charted as ONE disc in free atlas space. The rest of the layout is unchanged,
so the paid paint stays valid everywhere else.

The Meshy layout cut each eyeball into 3-4 small charts (about 1,000 texels per eye), and every chart drew its own piece
of iris. The eyes are now painted from geometry (face_paint.py), so each eyeball gets an azimuthal projection around its
forward axis (face_geom.eyes): radius = angle from the axis, linear up to KNEE rad and compressed by TAIL beyond it
(the back of the eyeball is hidden behind the skin), at DENSITY times the old texel density. The disc goes into the
largest free circle of the atlas that is clear of every chart by MARGIN texels.

Usage: uv_eyes.py [density 3.5: 4.0 left no free square for the second eye] -> work/uv_eyes.npz (same keys as the layout: uv, tri, xyz) and
work/uv_eyes_report.json."""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import face_geom  # noqa: E402
import texlib  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
DENSITY = float(sys.argv[1]) if len(sys.argv) > 1 else 3.5
KNEE, TAIL = 0.8, 0.2
S, MARGIN = 2048, 4
lay = dict(np.load(HERE / 'work' / 'uv_cc4_fine.npz'))
before = np.load(HERE / 'work' / 'lod0_before.npz')
piece = before['piece']
uv, xyz = lay['uv'].copy(), lay['xyz']
eyes = face_geom.eyes(samples=20000)
report = {'density_factor': DENSITY, 'knee_rad': KNEE, 'tail': TAIL}

# free space: texels clear of every non-eyeball chart (the old eyeball charts are freed)
keep = ~np.isin(piece, list(eyes))
tri_id, _ = texlib.raster(uv[keep], S, grow=0.0)
taken = ndimage.binary_dilation(tri_id >= 0, iterations=MARGIN)
taken[:MARGIN + 1] = taken[-MARGIN - 1:] = True                      # the atlas border counts as taken
taken[:, :MARGIN + 1] = taken[:, -MARGIN - 1:] = True
for k, e in eyes.items():
    f = np.nonzero(piece == k)[0]
    p = xyz[f]
    a3 = np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1).sum() / 2
    u = uv[f] * S
    a2 = np.abs((u[:, 1, 0] - u[:, 0, 0]) * (u[:, 2, 1] - u[:, 0, 1])
                - (u[:, 2, 0] - u[:, 0, 0]) * (u[:, 1, 1] - u[:, 0, 1])).sum() / 2
    old_density = np.sqrt(a2 / a3)                                      # texels per metre
    axis = e['axis']
    e1 = np.cross([0.0, 1.0, 0.0], axis)
    e1 /= np.linalg.norm(e1)                                            # horizontal, towards +x for a forward axis
    e2 = np.cross(axis, e1)                                             # up
    d = p - e['centre']
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    theta = np.arccos(np.clip(d @ axis, -1, 1))
    phi = np.arctan2(d @ e2, d @ e1)
    r = np.where(theta <= KNEE, theta, KNEE + TAIL * (theta - KNEE))
    scale = DENSITY * old_density * e['radius']                         # texels per radian at the axis
    local = np.stack([r * np.cos(phi), -r * np.sin(phi)], -1) * scale   # glTF v down: up on the eye is -v
    radius = float(np.linalg.norm(local, axis=-1).max()) + 1.0
    side = int(np.ceil(2 * radius))
    dist = ndimage.distance_transform_edt(~taken)                      # largest free circle
    cy, cx = np.unravel_index(np.argmax(dist), dist.shape)
    if dist[cy, cx] < radius:
        raise SystemExit(f'no free circle of radius {radius:.0f} texels for eye {k} (largest {dist[cy, cx]:.0f})')
    uv[f] = (local + [cx + 0.5, cy + 0.5]) / S
    tri_e, _ = texlib.raster(uv[f], S)
    taken |= ndimage.binary_dilation(tri_e >= 0, iterations=MARGIN)
    new = uv[f] * S
    a2n = np.abs((new[:, 1, 0] - new[:, 0, 0]) * (new[:, 2, 1] - new[:, 0, 1])
                 - (new[:, 2, 0] - new[:, 0, 0]) * (new[:, 1, 1] - new[:, 0, 1]))
    sgn = (new[:, 1, 0] - new[:, 0, 0]) * (new[:, 2, 1] - new[:, 0, 1]) - (new[:, 2, 0] - new[:, 0, 0]) * (new[:, 1, 1] - new[:, 0, 1])
    vis = theta.mean(1) < np.radians(45)
    a3v = np.linalg.norm(np.cross(p[vis, 1] - p[vis, 0], p[vis, 2] - p[vis, 0]), axis=1)
    report[face_geom.EYES[k]] = {
        'old_texels': round(float(a2)), 'new_texels': round(float(a2n.sum() / 2)), 'disc_px': side,
        'centre_px': [int(cx), int(cy)], 'old_px_per_mm': round(float(old_density / 1000), 2),
        'visible_cap_px_per_mm': round(float(np.sqrt(a2n[vis].sum() / 2 / a3v.sum() * 2) / 1000), 2),
        'minority_winding': int(min((sgn > 0).sum(), (sgn < 0).sum())),
        'axis': axis.round(4).tolist()}
np.savez(HERE / 'work' / 'uv_eyes.npz', uv=uv, tri=lay['tri'], xyz=xyz)
json.dump(report, open(HERE / 'work' / 'uv_eyes_report.json', 'w'), indent=1)
print('UV_EYES', json.dumps(report))
