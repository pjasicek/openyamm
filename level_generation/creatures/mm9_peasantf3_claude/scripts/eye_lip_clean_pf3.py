#!/usr/bin/env python3
"""Eyes and lips on the fresh head paint (pass 5; user: "eyes, what are these black things", "black stuff on her upper lip"), judged in the
review viewer at a face close-up:
- lower lids: Meshy painted the lower lid's ledge (the jagged rim of the socket below each eyeball) dark brown, which reads as a dark wedge
  under each eye. Head-shell texels (not the eyeballs) within 2-13 mm below the eyeball's centre and |dx| < 17 mm whose luminance is under
  0.92 of the cheek below take the cheek's colour toward that level, their fine detail kept;
- eyeballs: Meshy painted the eyeball pieces' lower part (below the iris, which shows under the jagged lower-lid edge) lid-brown and their
  rims stick out at the corners as white slivers; ball texels below 0.3 of the ball's radius under its centre, and outside 0.85 of it,
  take the cheek skin (0.90-0.96 of it), so the lower lid reads as one surface;
- lips: a dark parting painted between the lips (Meshy) on the closed mouth; mouth-box texels darker than 0.7 of the lips' median take the
  lip colour round them (normalised convolution), and the lips are desaturated 15 %.
Args: <in png> <out png>   (project folder; positions from work/uv_tex2.npz)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
D = np.load('work/uv_tex2.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
Z0 = -0.9297; kh = names.index('head')
im = np.asarray(Image.open(sys.argv[1]).convert('RGB'), np.float32) / 255; S = im.shape[0]
hf = np.where((mat == 1) & (comp[tri[:, 0]] == kh))[0]
# head pieces by position-welded connectivity: eyeballs are small pieces beside the nose at eye height
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); par = np.arange(inv.max() + 1)
def f_(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for t in tri[hf]:
    r = f_(inv[t[0]]); par[f_(inv[t[1]])] = r; par[f_(inv[t[2]])] = r
root = np.array([f_(inv[t[0]]) for t in tri[hf]]); cen = co[tri[hf]].mean(1); isball = np.zeros(len(hf), bool)
for r in np.unique(root):
    m = root == r; c = cen[m].mean(0)
    if m.sum() < 400 and 0.015 < abs(c[0]) < 0.05 and 1.58 < c[2] - Z0 < 1.65: isball[m] = True
POS = np.full((S, S, 3), np.nan); BALL = np.zeros((S, S), bool)
for j, f in enumerate(hf):
    q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, S)), np.arange(max(y0, 0), min(y1 + 1, S)))
    pts = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]
    M = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(M)) < 1e-12: continue
    l = np.linalg.solve(M, (pts - q[2]).T).T; l3 = np.c_[l, 1 - l.sum(1)]; ok = (l3 > -0.01).all(1)
    yy, xx = pts[ok, 1].astype(int), pts[ok, 0].astype(int); POS[yy, xx] = l3[ok] @ co[tri[f]]; BALL[yy, xx] = isball[j]
cov = ~np.isnan(POS[..., 0]); x, y, z = (np.nan_to_num(POS[..., k]) for k in range(3)); zs = z - Z0
LUM = np.array([0.2126, 0.7152, 0.0722]); lum = im @ LUM; det = (lum - ni.gaussian_filter(lum, 1.5))[..., None]
out = im.copy(); rep = {}
for sg in (1, -1):
    b = BALL & (np.sign(x) == sg)
    if not b.any(): continue
    bc = np.array([np.median(x[b]), np.median(y[b]), np.median(zs[b])])
    front = b & (y < np.percentile(y[b], 40))                            # the visible front of the ball
    rad = np.hypot(x - bc[0], zs - bc[2])
    rv = float(np.percentile(rad[front], 95)) if front.any() else 0.012
    dx, dz = x - bc[0], zs - bc[2]
    ck = cov & ~BALL & (np.abs(dx) < 0.012) & (dz < -0.016) & (dz > -0.024) & (y < -0.08)
    cheek = np.median(out[ck], 0); cl = float(cheek @ LUM)
    band = cov & ~BALL & (np.abs(dx) < 0.017) & (dz < -0.002) & (dz > -0.013) & (y < -0.07)
    dark = band & (lum < 0.92 * cl)
    k = np.clip((0.92 * cl - lum) / (0.25 * cl), 0, 1) * dark
    k = ni.gaussian_filter(k, 1.0)[..., None] * band[..., None]
    out = out * (1 - k) + np.clip(cheek * 0.95 + det * 0.6, 0, 1) * k
    # the ball's lower part below the iris and its outer rim read as the lower lid: cheek skin, a touch darker toward the lash line
    low = np.clip((-dz - 0.30 * rv) / (0.25 * rv), 0, 1); outer = np.clip((rad - 0.85 * rv) / (0.15 * rv), 0, 1)
    kr = (np.maximum(low, outer) * b)[..., None]
    shade = (0.90 + 0.06 * np.clip((-dz - 0.3 * rv) / (0.7 * rv), 0, 1))[..., None]
    out = out * (1 - kr) + np.clip(cheek * shade + det * 0.4, 0, 1) * kr
    rim = kr[..., 0] > 0.5
    rep[sg] = {'lid texels': int((k[..., 0] > 0.3).sum()), 'rim texels': int(rim.sum()), 'ball radius mm': round(rv * 1000, 1)}
# lips
mbox = cov & ~BALL & (np.abs(x) < 0.03) & (zs > 1.535) & (zs < 1.575) & (y < -0.09)
hsv = np.asarray(Image.fromarray((np.clip(out, 0, 1) * 255).astype('u1')).convert('HSV'), np.float32) / 255
lip = mbox & ((hsv[..., 0] * 360 < 15) | (hsv[..., 0] * 360 > 340)) & (hsv[..., 1] > 0.35)
lm = float(np.median((out @ LUM)[lip])) if lip.any() else 0.5
slit = mbox & ((out @ LUM) < 0.7 * lm)
slit = ni.binary_dilation(slit, iterations=1) & mbox
good = lip & ~slit
w = ni.gaussian_filter(good.astype(np.float32), 3.0); c = np.stack([ni.gaussian_filter(out[..., i] * good, 3.0) for i in range(3)], -1) / np.maximum(w, 1e-4)[..., None]
ks = ni.gaussian_filter(slit.astype(np.float32), 0.8)[..., None] * mbox[..., None]
out = out * (1 - ks) + np.clip(c + det * 0.3, 0, 1) * ks
lipm = ni.gaussian_filter((lip | slit).astype(np.float32), 1.0)[..., None]
g = out @ LUM; out = out * (1 - 0.15 * lipm) + g[..., None] * 0.15 * lipm
rep['lip texels'] = int(lip.sum()); rep['slit texels'] = int(slit.sum())
# pass 5 (viewer close-up): a white glint painted on the lower lip (it reads as wet gloss in any light) takes the lip colour round it
lum2 = out @ LUM
hsv2 = np.asarray(Image.fromarray((np.clip(out, 0, 1) * 255).astype('u1')).convert('HSV'), np.float32) / 255
hl = mbox & ni.binary_dilation(lip, iterations=3) & (hsv2[..., 1] < 0.32) & (lum2 > 1.3 * lm)   # near-white on the lips (skin there is saturated)
hl = ni.binary_dilation(hl, iterations=1) & mbox & ~(hsv2[..., 1] > 0.45) | hl
good2 = lip & ~hl
w2 = ni.gaussian_filter(good2.astype(np.float32), 3.0); c2 = np.stack([ni.gaussian_filter(out[..., i] * good2, 3.0) for i in range(3)], -1) / np.maximum(w2, 1e-4)[..., None]
c2 = np.where((w2 > 0.05)[..., None], c2, np.median(out[lip], 0))                          # island edges: the lips' median colour
kh_ = np.maximum(ni.gaussian_filter(hl.astype(np.float32), 0.6), hl)[..., None] * mbox[..., None]
out = out * (1 - kh_) + np.clip(c2, 0, 1) * kh_
# pass 5 (viewer close-up, a white glint along the lower lip): the mouth's midline strip (|x| < 4 mm) is its own thin UV island, which
# Meshy painted skin and cream; its texels take the mean colour of the 8 texels off the midline (4-9 mm) nearest in height and depth
from scipy.spatial import cKDTree
mid_box = cov & ~BALL & (zs > 1.525) & (zs < 1.578) & (y < -0.09)
srcm = mid_box & (np.abs(x) > 0.004) & (np.abs(x) < 0.009); dstm = mid_box & (np.abs(x) <= 0.004)
_, nn_ = cKDTree(np.c_[y[srcm], zs[srcm]] * 1000).query(np.c_[y[dstm], zs[dstm]] * 1000, k=8)
out[dstm] = out[srcm][nn_].mean(1)
rep['midline mouth texels'] = int(dstm.sum())
# the nose's midline strip (bridge to tip) likewise: dark and pink specks on the seam
nb = cov & ~BALL & (zs > 1.565) & (zs < 1.64) & (y < -0.09)
srcn = nb & (np.abs(x) > 0.003) & (np.abs(x) < 0.007); dstn = nb & (np.abs(x) <= 0.003)
_, nn2 = cKDTree(np.c_[y[srcn], zs[srcn]] * 1000).query(np.c_[y[dstn], zs[dstn]] * 1000, k=8)
out[dstn] = out[srcn][nn2].mean(1)
rep['midline nose texels'] = int(dstn.sum())
# pass 5: thin dark lines painted from the nose wings round the mouth (nasolabial arcs, lines on a young face) are lifted to the skin round them
nl = cov & ~BALL & (np.abs(x) > 0.008) & (np.abs(x) < 0.05) & (zs > 1.485) & (zs < 1.60) & (y < -0.075) & ~ni.binary_dilation(lip, iterations=4)
lum3 = out @ LUM; bl = np.stack([ni.gaussian_filter(out[..., i], 4.0) for i in range(3)], -1)
kn = (np.clip(((bl @ LUM) - lum3 - 0.004) / 0.025, 0, 1) * nl)
kn = ni.gaussian_filter(kn, 0.7)[..., None] * nl[..., None]
out = out * (1 - kn) + bl * kn
rep['lip glint texels'] = int(hl.sum()); rep['nasolabial texels'] = int((kn[..., 0] > 0.3).sum())
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype('u1')).save(sys.argv[2]); print('EYELIP', rep)
