#!/usr/bin/env python3
"""Move Meshy's body retexture (meshy/retexture_v1, 2K on Meshy's own UVs) onto the packed body layout (uv_pack.py,
uv_atlas.py), per texel and per triangle: the same triangle's barycentric point in Meshy's UVs (no ray casting, the
mesh is the same). Base colour, roughness and metallic bilinear; the normal map is re-encoded from the old layout's
tangent frame into the new one in the frame fs_model.sc rebuilds from position and UV derivatives (the frame() of
lod_repair_claude/scripts/transfer_textures.py), kept in Meshy's +y-down convention for prepare_actor_glb.py.
Triangles whose Meshy UVs are one texel (face_fix.py's goggle brass and strap) take that texel and a flat normal.
Empty texels take the nearest filled one. Writes work/meshy_body_packed/texture_urls_0_<map>.png at W x H.
Args: <uvpack_in.npz> <uv_pack.npz> [W H] (default 2048 1024). Needs pymeshlab (transfer_textures imports it): run with
the lod_repair venv's Python."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'lod_repair_claude' / 'scripts'))
from transfer_textures import frame, normalize, sample  # noqa: E402

d = np.load(sys.argv[1]); P = np.load(sys.argv[2])
W, H = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (2048, 1024)
co, vid, old, nrm, new = d['co'], d['vid'], d['old_uv'], d['normals'], P['uv']
SRC = HERE / 'meshy' / 'retexture_v1'; OUT = HERE / 'work' / 'meshy_body_packed'; OUT.mkdir(exist_ok=True)
maps = {k: np.asarray(Image.open(SRC / f'texture_urls_0_{k}.png').convert('RGB'), np.float32)
        for k in ('base_color', 'normal', 'roughness', 'metallic')}
gl = lambda uv: np.stack([uv[..., 0], 1.0 - uv[..., 1]], -1)        # Blender v up -> image / glTF v down
old_gl, new_gl = gl(old), gl(new)
e1o, e2o = old[:, 1] - old[:, 0], old[:, 2] - old[:, 0]
degenerate = 0.5 * np.abs(e1o[:, 0] * e2o[:, 1] - e1o[:, 1] * e2o[:, 0]) * 2048 * 2048 < 0.05
out = {k: np.zeros((H, W, 3), np.float32) for k in maps}; filled = np.zeros((H, W), bool)
pix = new_gl * np.array([W, H])
for t in range(len(vid)):
    a, b, c = pix[t]
    lo = np.clip(np.floor(np.minimum(np.minimum(a, b), c) - 0.5).astype(int), 0, [W - 1, H - 1])
    hi = np.clip(np.ceil(np.maximum(np.maximum(a, b), c) + 0.5).astype(int), 0, [W - 1, H - 1])
    gx, gy = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
    cx, cy = gx.ravel() + 0.5, gy.ravel() + 0.5
    area = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    if abs(area) < 1e-12:
        continue
    w1 = ((cx - a[0]) * (c[1] - a[1]) - (cy - a[1]) * (c[0] - a[0])) / area
    w2 = ((b[0] - a[0]) * (cy - a[1]) - (b[1] - a[1]) * (cx - a[0])) / area
    ins = (w1 >= -1e-4) & (w2 >= -1e-4) & (w1 + w2 <= 1 + 1e-4)
    if not ins.any():
        continue
    x, y = gx.ravel()[ins], gy.ravel()[ins]
    bary = np.stack([1 - w1[ins] - w2[ins], w1[ins], w2[ins]], -1)
    uv_old = bary @ old_gl[t]
    for k in ('base_color', 'roughness', 'metallic'):
        out[k][y, x] = sample(maps[k], uv_old)
    if degenerate[t]:
        out['normal'][y, x] = (127.5, 127.5, 255.0)
    else:
        p = co[vid[t]]; n = normalize(bary @ nrm[t])
        e1, e2 = np.broadcast_to(p[1] - p[0], n.shape), np.broadcast_to(p[2] - p[0], n.shape)
        t0, b0 = frame(e1, e2, np.broadcast_to(old_gl[t, 1] - old_gl[t, 0], (len(n), 2)),
                       np.broadcast_to(old_gl[t, 2] - old_gl[t, 0], (len(n), 2)), n)
        t1, b1 = frame(e1, e2, np.broadcast_to(new_gl[t, 1] - new_gl[t, 0], (len(n), 2)),
                       np.broadcast_to(new_gl[t, 2] - new_gl[t, 0], (len(n), 2)), n)
        s = sample(maps['normal'], uv_old)
        xy = np.stack([s[:, 0] / 127.5 - 1.0, -(s[:, 1] / 127.5 - 1.0)], -1)     # Meshy +y down -> glTF
        z = np.sqrt(np.maximum(1.0 - (xy ** 2).sum(-1), 0.0))
        target = normalize(t0 * xy[:, :1] - b0 * xy[:, 1:] + n * z[:, None])
        basis = np.stack([t1, -b1, n], -1)
        cf = np.linalg.solve(basis + np.eye(3) * 1e-9, target[:, :, None])[:, :, 0]
        cf[:, 2] = np.maximum(cf[:, 2], 0.05); cf = normalize(cf)
        out['normal'][y, x] = np.stack([cf[:, 0], -cf[:, 1], cf[:, 2]], -1) * 127.5 + 127.5   # back to +y down
    filled[y, x] = True
_, (iy, ix) = distance_transform_edt(~filled, return_indices=True)
for k, v in out.items():
    Image.fromarray(np.clip(np.round(v[iy, ix]), 0, 255).astype(np.uint8)).save(OUT / f'texture_urls_0_{k}.png')
print('RESAMPLED', W, H, 'filled', round(float(filled.mean()), 3), 'degenerate triangles', int(degenerate.sum()), OUT)
