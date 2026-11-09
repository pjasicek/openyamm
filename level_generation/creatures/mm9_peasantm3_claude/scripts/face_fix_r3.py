#!/usr/bin/env python3
"""Tier A face marks after the fresh head paint r3 (viewer close-ups, 2026-11-02), paint only, on the geometry:
- nose underside: the paint put red and near-black round the nostril holes (a dark blob from the front and below). Head texels on
  the nose (|x| < 2.2 cm, rest z 0.755-0.79, in front of y -0.075) whose surface faces down (raster normal z < -0.25) take the
  cheek skin x 0.72 with the paint's fine detail, so the geometry's nostrils read as two soft shadows;
- lower lids: texels under each eye redder than the cheek (r/g above x 1.08) move 80 % toward the cheek hue at their own
  brightness; texels there LIGHTER than the cheek by > 12 % (the pale crescent) take the cheek's brightness.
Iris centres as eye_open_pm3.py. Usage (project folder): face_fix_r3.py <export glb> <prefix>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
glb, prefix = sys.argv[1], sys.argv[2]
f = Path(f'textures/{prefix}_head_basecolor.png')
img = np.asarray(Image.open(f).convert('RGB'), float)
N = img.shape[0]
pos, cov = texel_positions(glb, 'PeasantM3Head', N)
bx = np.nan_to_num(pos[..., 0]); by = -np.nan_to_num(pos[..., 2]); bz = np.nan_to_num(pos[..., 1]) - 0.855
P3 = np.stack([bx, by, bz], -1)
nrm = np.cross(np.gradient(P3, axis=1), np.gradient(P3, axis=0))
nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-12)
# orient normals outward (away from the head centre)
out_dir = P3 - np.array([0.0, 0.01, 0.80])
nrm *= np.sign(np.sum(nrm * out_dir, -1, keepdims=True) + 1e-9)
cheek = cov & (bz > 0.775) & (bz < 0.79) & (np.abs(bx) > 0.03) & (np.abs(bx) < 0.055) & (by < -0.04)
ref = np.median(img[cheek], 0); lref = ref @ [0.299, 0.587, 0.114]
lum = img @ [0.299, 0.587, 0.114]
fine = lum - ndimage.gaussian_filter(lum, 2.5)
out = img.copy()
nose = cov & (np.abs(bx + 0.005) < 0.022) & (bz > 0.755) & (bz < 0.79) & (by < -0.075) & (nrm[..., 2] < -0.25)
# r3b: grey / dark texels under the tip and round the nostrils (the paint's columella patch), by colour in the nose box
sat = (img.max(-1) - img.min(-1)) / np.maximum(img.max(-1), 1)
nbox = cov & (np.abs(bx + 0.005) < 0.022) & (bz > 0.755) & (bz < 0.778) & (by < -0.07)
nose |= nbox & ((lum < 0.72 * lref) | (sat < 0.25))
# r3c: the grey columella patch sits further back and higher (under the tip, y > -0.07 too)
nose |= cov & (np.abs(bx + 0.005) < 0.016) & (bz > 0.758) & (bz < 0.786) & (by < -0.055) & (sat < 0.3)
import os
R5 = os.environ.get('R5') == '1'   # r5: fresh paints on the final mouth: nose/lid fixes on both tiers, no lip-band/lip-line edits
IS_A = prefix == 'pm3_tp' or R5     # r4: B (approved) takes only the under-eye facet toning below
nose &= IS_A
ns = ndimage.gaussian_filter(nose.astype(float), 1.5) * cov
skin = ref[None, None] * 0.88 + 0.4 * fine[..., None]      # r3c: the cavities' own shading makes the nostril shadow
out = out * (1 - ns[..., None]) + skin * ns[..., None]
# r3c: red rims round the alae -> the cheek hue at their own brightness
nb2 = cov & (np.abs(bx + 0.005) < 0.026) & (bz > 0.752) & (bz < 0.792) & (by < -0.055)
rgn = out[..., 0] / np.maximum(out[..., 1], 1)
rn = np.clip((rgn - ref[0] / ref[1] * 1.12) / 0.2, 0, 1) * nb2 * IS_A
ln = out @ [0.299, 0.587, 0.114]
out = out * (1 - rn[..., None]) + (ref[None, None] * (ln / max(lref, 1))[..., None]) * rn[..., None]
EYES = [(-0.0326, 0.810), (0.0228, 0.810)]
def sst(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
low = np.zeros(img.shape[:2])
for xe, ze in EYES:
    r = np.sqrt(((bx - xe) / 0.021) ** 2 + ((bz - ze + 0.006) / 0.009) ** 2)
    low = np.maximum(low, (1 - sst((r - 1.0) / 0.5)) * (bz < ze - 0.0015))
low *= cov * (by < -0.03) * IS_A
rg = out[..., 0] / np.maximum(out[..., 1], 1)
red = np.clip((rg - ref[0] / ref[1] * 1.08) / 0.2, 0, 1) * low
l2 = out @ [0.299, 0.587, 0.114]
tone = ref[None, None] * (l2 / max(lref, 1))[..., None]
out = out * (1 - 0.8 * red[..., None]) + tone * 0.8 * red[..., None]
l2 = out @ [0.299, 0.587, 0.114]
pale = np.clip((l2 / max(lref, 1) - 1.12) / 0.1, 0, 1) * low
out = out * (1 - pale[..., None]) + (out * (lref * 1.02 / np.maximum(l2, 1))[..., None]) * pale[..., None]
# r4 (user note "part of lip missing?"): the pale skin band between the lower lip and the beard (A's soul-patch area) takes the
# beard paint of the face point 1.2 cm lower, where its luminance/saturation says skin rather than hair
if prefix == 'pm3_tp' and not R5:
    from scipy.spatial import cKDTree
    fr = cov & (by < -0.03) & (np.abs(bx + 0.003) < 0.05) & (bz > 0.69) & (bz < 0.76)
    tr = cKDTree(np.column_stack([bx[fr], bz[fr]]))
    fy_, fx_ = np.nonzero(fr)
    lip_band = cov & (by < -0.03) & (np.abs(bx + 0.003) < 0.026) & (bz > 0.718) & (bz < 0.741)
    sat2 = (out.max(-1) - out.min(-1)) / np.maximum(out.max(-1), 1)
    rgl = out[..., 0] / np.maximum(out[..., 1], 1)
    paleb = lip_band & (sat2 < 0.48) & (rgl < 1.75)
    ty, tx = np.nonzero(paleb)
    _, k = tr.query(np.column_stack([bx[paleb], bz[paleb] - 0.012]))
    src = out[fy_[k], fx_[k]].copy()
    pw = np.clip(ndimage.gaussian_filter(paleb.astype(float), 3.0) * 1.4, 0, 1)[ty, tx][:, None]   # r4c: soft edge
    out[ty, tx] = out[ty, tx] * (1 - pw) + src * pw
    # nostril holes: painted dark brown -> no darker than 0.62 x cheek (the cavities' shading makes the soft shadow)
    nh = cov & (np.abs(bx + 0.005) < 0.02) & (bz > 0.755) & (bz < 0.778) & (by < -0.06)
    l3 = out @ [0.299, 0.587, 0.114]
    lift = np.where(nh & (l3 < 0.62 * lref), 0.62 * lref / np.maximum(l3, 1), 1.0)
    out = out * ndimage.gaussian_filter(lift, 1.0)[..., None]
    print('FACEFIX4 pale lip band', int(paleb.sum()), 'nostril texels lifted', int((lift > 1.01).sum()))
# r4b: lit facets under both eyes (light triangles in the viewer's top light, user note): texels whose surface faces more
# upward than the cheek round them (raster normal z minus its 6-texel average) are darkened in proportion, so the facet's
# extra light is taken out of the paint (no geometry change); zone: 0.6-2.6 cm below each iris, 2.6 cm either side
nzs = ndimage.gaussian_filter(np.where(cov, nrm[..., 2], 0), 6) / np.maximum(ndimage.gaussian_filter(cov.astype(float), 6), 1e-3)
dn = ndimage.gaussian_filter(np.where(cov, nrm[..., 2] - nzs, 0), 3.0)   # r4c: smoothed (flat facets drew lines)
for xe_ in (-0.0326, 0.0228):
    zone = cov & (by < -0.03) & (np.abs(bx - xe_) < 0.026) & (bz > 0.784) & (bz < 0.804)
    w = ndimage.gaussian_filter(zone.astype(float), 2.0)
    out = out * (1 - (np.clip(dn * 0.6, 0, 0.12) * w)[..., None])
# r3c: the lit fold under the character's left eye (geometry, a pale crescent in the viewer's light): its skin 8 % darker,
# feathered, so the fold's highlight matches the cheek
xe = 0.0228
r = np.sqrt(((bx - xe) / 0.016) ** 2 + ((bz - 0.797) / 0.006) ** 2)
fold = (1 - sst((r - 1.0) / 0.6)) * cov * (by < -0.03) * (prefix == 'pm3_tp') * (not R5)
out = out * (1 - 0.08 * fold[..., None])
# r4c (both tiers): the lip line's downward-facing sawtooth faces (the upper lip's lower edge) shade dark in the viewer's top
# light and drew a jagged dark slit: lip texels in the mouth line band whose surface faces down are lightened toward
# the lip colour x (1 + 0.6 * downwardness), smoothed, so the line reads soft
mb = cov & (by < -0.05) & (np.abs(bx + 0.003) < 0.026) & (bz > 0.740) & (bz < 0.756) & (not R5)
down = ndimage.gaussian_filter(np.where(mb, np.clip(-nrm[..., 2], 0, 1), 0), 1.2)
lipc = np.median(out[mb & (out[..., 0] > out[..., 1] * 1.25)], 0) if (mb & (out[..., 0] > out[..., 1] * 1.25)).any() else ref
tgt = np.clip(lipc[None, None] * (1 + 0.6 * down[..., None]), 0, 255)
wl = np.clip(down * 1.5, 0, 0.85)[..., None]
out = out * (1 - wl) + tgt * wl
print('FACEFIX5 lip line texels', int((down > 0.1).sum()), 'lip', lipc.round())
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(f)
print('FACEFIX3', prefix, 'nose underside texels', int(nose.sum()), 'red lid', int((red > 0.3).sum()), 'pale lid', int((pale > 0.3).sum()), 'cheek', ref.round())
