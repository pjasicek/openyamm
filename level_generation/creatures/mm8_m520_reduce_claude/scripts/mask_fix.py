#!/usr/bin/env python3
"""Clear region-mask spill onto arm skin (existing m520 defect: the tier ramp tinted skin above the left wrist wrap and
under the right wrap). On the arms (rest pose |x| > 0.38 m, z 1.15-1.5 m), masked bright texels (luminance over 0.45) whose base colour is closer
(CIE Lab, and within dE 12) to the nearby unmasked skin than to the wrap core (mask > 0.9, leather-dark) are cleared, if they connect in the atlas to
unmasked texels through other such texels. Writes work/retex/mask_fixed.png and review/retex/mask_fix_overlay.png."""
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
t = np.load('work/retex/texel_map.npz'); face, pos = t['face'], t['pos']
mimg = np.asarray(Image.open('work/retex/img3.png').convert('RGBA')).copy()
mask = mimg[..., 0] / 255.
base = np.asarray(Image.open('work/retex/img0.png').convert('RGB'), np.float32) / 255


def lab(c):
    c = np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
    xyz = c @ np.array([[.4124, .3576, .1805], [.2126, .7152, .0722], [.0193, .1192, .9505]]).T / [.9505, 1, 1.089]
    f = np.where(xyz > .008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


L = lab(base)
arm = (face >= 0) & (np.abs(pos[..., 0]) > .38) & (pos[..., 2] > 1.15) & (pos[..., 2] < 1.5)
# wrap core: fully masked and leather-dark (the skin-coloured blob above the left wrap is fully masked too)
lum = base @ np.array([.3, .59, .11])
# skin is bright (the unmasked dark fur rims on top of the wraps made dark wrap texels look skin-like)
core = arm & (mask > .9) & (lum < .43); skin = arm & (mask < .05) & (lum > .45)
cand = arm & (mask > .05)
# local class means: 8 nearest core and skin texels in 3D
tc, ts = cKDTree(pos[core]), cKDTree(pos[skin])
cy, cx = np.where(cand)
_, ic = tc.query(pos[cy, cx], 16); _, is_ = ts.query(pos[cy, cx], 16)
mc = L[core][ic].mean(1); ms = L[skin][is_].mean(1)
ds, dc = np.linalg.norm(L[cy, cx] - ms, axis=1), np.linalg.norm(L[cy, cx] - mc, axis=1)
# skin-like: nearer the skin than the wrap and within dE 12 of the skin (frayed wrap edges are orange-brown, keep them)
skinlike = np.zeros_like(cand); skinlike[cy, cx] = (ds < dc) & (ds < 12) & (lum[cy, cx] > .45)
# keep only skin-like texels connected to unmasked arm skin
grow = ndimage.binary_dilation(skin, iterations=1) & skinlike
lab_, n = ndimage.label(skinlike | skin)
touch = np.unique(lab_[skin]); clear = skinlike & np.isin(lab_, touch[touch > 0])
# texels on the wraps' own faces keep their tint: faces with 15 % or more dark wrap-core texels are wrap geometry
# (their skin-coloured edge texels otherwise left tan notches in the tinted wrap edge)
F = face.max() + 1
frac = np.bincount(face[core], minlength=F) / np.maximum(np.bincount(face[face >= 0], minlength=F), 1)
clear &= ~((face >= 0) & (frac[np.maximum(face, 0)] >= .15))
# the skin-coloured blob above the left wrap (rest pose x 0.37-0.465 m, back side) is cleared whole
patch = (face >= 0) & (pos[..., 0] > .37) & (pos[..., 0] < .465) & (pos[..., 1] > -.02) & (pos[..., 2] > 1.33) \
    & (pos[..., 2] < 1.47) & (mask > 0)
clear |= patch
# gutter texels (bilinear filtering samples them) follow their nearest surface texel, only where that one was cleared:
# clearing every gutter texel near a cleared one also cleared wrap-coloured gutter and left orange flecks on the fringe
_, (ny, nx) = ndimage.distance_transform_edt(face < 0, return_indices=True)
clear |= (face < 0) & (mask > 0) & clear[ny, nx]
print('arm masked texels', int(cand.sum()), 'skin-like', int(skinlike.sum()), 'cleared', int(clear.sum()))
out = mimg.copy(); out[..., 0][clear] = 0
Image.fromarray(out).save('work/retex/mask_fixed.png')
ov = (base * 255).astype(np.uint8).copy(); ov[core] = [0, 90, 255]; ov[clear] = [255, 0, 255]
ys, xs = np.where(arm); crop = (slice(max(ys.min() - 10, 0), ys.max() + 10), slice(max(xs.min() - 10, 0), xs.max() + 10))
Image.fromarray(ov[crop]).save('review/retex/mask_fix_overlay.png')
