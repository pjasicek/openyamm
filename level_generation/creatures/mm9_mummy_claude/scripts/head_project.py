"""Head colour by projection of the Codex busts (free; heads differ per tier). numpy software raster.
Args: <tier A|B|C> <out png> [size]. Uses work/uv_dump.npz (ph, uh: head corners), work/head_align.json."""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
HERE = Path(__file__).resolve().parents[1]
tier, out = sys.argv[1:3]; SIZE = int(sys.argv[3]) if len(sys.argv) > 3 else 2048
D = np.load(HERE / 'work/uv_dump.npz'); P = D['ph'].reshape(-1, 3, 3); U = D['uh'].reshape(-1, 3, 2)
LM = json.load(open(HERE / 'scripts/head_landmarks.json'))
POW, FRONT = 10, 3.0
VIEWS = {'01_front': ((1, 0, 0), (0, -1, 0)), '02_back': ((-1, 0, 0), (0, 1, 0)), '03_left': ((0, -1, 0), (-1, 0, 0)), '04_right': ((0, 1, 0), (1, 0, 0))}   # image right axis, to-camera axis
fn = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
# smooth normals by position
key = np.round(P.reshape(-1, 3), 4); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
Ns = np.zeros((inv.max() + 1, 3)); np.add.at(Ns, inv, np.repeat(fn, 3, 0)); Ns /= np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-12)
VN = Ns[inv].reshape(-1, 3, 3)
# texel barycentrics by raster: per triangle in UV
tex_pos = np.zeros((SIZE, SIZE, 3), np.float32); tex_n = np.zeros((SIZE, SIZE, 3), np.float32); cov = np.zeros((SIZE, SIZE), bool)
uvp = U * SIZE; uvp[..., 1] = SIZE - uvp[..., 1]
for i in range(len(P)):
    a, b, c = uvp[i]
    x0, x1 = int(np.floor(min(a[0], b[0], c[0]))) - 1, int(np.ceil(max(a[0], b[0], c[0]))) + 2
    y0, y1 = int(np.floor(min(a[1], b[1], c[1]))) - 1, int(np.ceil(max(a[1], b[1], c[1]))) + 2
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, SIZE), min(y1, SIZE)
    if x1 <= x0 or y1 <= y0: continue
    xs, ys = np.meshgrid(np.arange(x0, x1) + .5, np.arange(y0, y1) + .5)
    d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(d) < 1e-9: continue
    l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
    l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
    l2 = 1 - l0 - l1
    m = (l0 > -0.03) & (l1 > -0.03) & (l2 > -0.03)
    if not m.any(): continue
    yy, xx = ys[m].astype(int), xs[m].astype(int)
    w = np.stack([l0[m], l1[m], l2[m]], 1)
    tex_pos[yy, xx] = w @ P[i]; tex_n[yy, xx] = w @ VN[i]; cov[yy, xx] = True
tex_n /= np.maximum(np.linalg.norm(tex_n, axis=2, keepdims=True), 1e-9)
print('coverage', cov.mean())
acc = np.zeros((SIZE, SIZE, 3)); wsum = np.zeros((SIZE, SIZE))
for v, (rx, cam) in VIEWS.items():
    rx, cam = np.array(rx, float), np.array(cam, float)
    im = np.asarray(Image.open(HERE / f'references_head/tier{tier}/{v}.png').convert('RGBA'), float) / 255
    L = LM[tier][v]
    def fy(z): 
        zs, ys = np.array(LM['z']), np.array(L['y'], float)
        out_ = np.interp(z, zs, ys)
        return out_ + (z > zs[-1]) * (z - zs[-1]) * -3000 + (z < zs[0]) * (zs[0] - z) * 3000
    def fx(u):
        us, xs = np.array(L['u']), np.array(L['x'], float)
        out_ = np.interp(u, us, xs); k0 = (xs[1] - xs[0]) / (us[1] - us[0]); k1 = (xs[-1] - xs[-2]) / (us[-1] - us[-2])
        return out_ + (u < us[0]) * (u - us[0]) * k0 + (u > us[-1]) * (u - us[-1]) * k1
    h, w_ = im.shape[:2]
    # outside the silhouette: the nearest opaque pixel, inset, so a hood wider than the bust samples its edge
    solid = ni.binary_erosion(im[..., 3] > 0.9, iterations=4)
    idx_ = ni.distance_transform_edt(~solid, return_distances=False, return_indices=True)
    im = im[idx_[0], idx_[1]]
    # depth buffer of the head in this view
    zb = np.full((h, w_), -1e9)
    Q = P.reshape(-1, 3); qx = fx(Q @ rx); qy = fy(Q[:, 2]); qz = Q @ cam
    for i in range(len(P)):
        j = i * 3
        xa = qx[j:j + 3]; ya = qy[j:j + 3]; za = qz[j:j + 3]
        x0, x1 = max(int(xa.min()), 0), min(int(xa.max()) + 2, w_); y0, y1 = max(int(ya.min()), 0), min(int(ya.max()) + 2, h)
        if x1 <= x0 or y1 <= y0: continue
        xs, ys = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1))
        d = (ya[1] - ya[2]) * (xa[0] - xa[2]) + (xa[2] - xa[1]) * (ya[0] - ya[2])
        if abs(d) < 1e-9: continue
        l0 = ((ya[1] - ya[2]) * (xs - xa[2]) + (xa[2] - xa[1]) * (ys - ya[2])) / d
        l1 = ((ya[2] - ya[0]) * (xs - xa[2]) + (xa[0] - xa[2]) * (ys - ya[2])) / d
        l2 = 1 - l0 - l1
        m = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
        if not m.any(): continue
        z = l0 * za[0] + l1 * za[1] + l2 * za[2]
        zb[y0:y1, x0:x1][m] = np.maximum(zb[y0:y1, x0:x1][m], z[m])
    px = fx(tex_pos @ rx); py = fy(tex_pos[..., 2]); pz = tex_pos @ cam
    ix, iy = np.clip(px.astype(int), 0, w_ - 1), np.clip(py.astype(int), 0, h - 1)
    vis = cov & (pz > zb[iy, ix] - 0.012) & (tex_n @ cam > 0.0)
    # image colour, alpha limits it (never past the silhouette)
    col = np.stack([ni.map_coordinates(im[..., c], [py, px], order=1, mode='nearest') for c in range(3)], 2)
    weight = (np.clip(tex_n @ cam, 0, 1) + 0.03) ** POW * vis
    if v == '01_front': weight *= FRONT
    acc += col * weight[..., None]; wsum += weight
    print(v, 'visible', vis.mean())
m = wsum > 1e-16
out_c = np.zeros((SIZE, SIZE, 3)); out_c[m] = acc[m] / wsum[m, None]
miss = cov & ~m
print('missing texels', miss.sum(), 'of', cov.sum()); np.savez('work/head_dbg.npz', miss=miss[::4, ::4], pos=tex_pos[::4, ::4], n=tex_n[::4, ::4], cov=cov[::4, ::4])
# fill: nearest valid
idx = ni.distance_transform_edt(~m, return_distances=False, return_indices=True)
filled = out_c[idx[0], idx[1]]
Image.fromarray((np.clip(filled, 0, 1) * 255 + .5).astype(np.uint8)).save(out)
