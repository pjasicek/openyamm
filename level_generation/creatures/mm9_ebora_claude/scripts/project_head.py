#!/usr/bin/env python3
"""Head paint by projection of the Codex views painted on our own head clay (from mm9_njam_claude/scripts/project_head.py,
0 credits). Ortho cameras are those of head_clay.py. The z-buffer covers every head layer (skin, hair, fringe, horns, ears),
so no view paints through the hair onto the face or the reverse.
- 08_face (close front view) is the face's ONLY paint source inside the face frame, placed by measured landmarks (thin-plate
  warp of the clay -> paint offsets, anchored at the frame corners);
- the other views paint outside the face frame only: front for the crown and fringe, 3/4 for the cheek sides and side hair,
  sides behind the cheeks, back and top for the back of the head;
- hair texels (part 1, 4) refuse skin-coloured paint, skin texels (0, 6, 7, 9) refuse hair-coloured paint;
- per texel weight = facing^3 x distance inside the paint's silhouette; each view is brought to the tone of what is placed.
Writes textures/<pre>_head_proj.png (S) and textures/<pre>_head_pnormal.png (1024, from luminance). Args: <tier a|s> <out prefix eb|sr> [S]"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.interpolate import RBFInterpolator
from scipy.spatial import cKDTree
tier, pre = sys.argv[1], sys.argv[2]; S = int(sys.argv[3]) if len(sys.argv) > 3 else 2048
Z = np.load('work/head_faces.npz'); CO, NO, UV, PART = Z['co'], Z['nor'], Z['uv'], Z['part']
# head fixes 3: face_shape.py reshapes the mouth and nose after this projection's geometry (work/head_faces.npz is the unshaped
# head). Texels are placed on the reshaped head (work/head_faces_shp.npz, same faces) and sample the paint at the field's smooth
# inverse, so painted lines stay smooth on the new surface (riding on the moved vertices they kinked at triangle edges)
SHP = Path('work/head_faces_shp.npz').exists()
CO2 = np.load('work/head_faces_shp.npz')['co'] if SHP else CO
C = np.array([0.0, 0.10, 0.85]); ORTHO = 0.56; FC = np.array([0.0, -0.02, 0.872]); FO = 0.22; R = 1254
VIEWS = {'01_front': (0, -1, 0), '03_left': (1, 0, 0), '02_back': (0, 1, 0), '04_right': (-1, 0, 0), '05_top': (0, 0.0001, 1),
         '06_q34r': (-1, -1.2, 0.15), '07_q34l': (1, -1.2, 0.15), '08_face': (0, -1, 0)}
ORDER = ['08_face', '01_front', '06_q34r', '07_q34l', '03_left', '04_right', '05_top', '02_back']
LMJ = json.load(open('references_head/landmarks.json'))
def cam(d):
    d = np.array(d, float); d /= np.linalg.norm(d); up = np.array([0, 0, 1.0])
    if abs(d @ up) > 0.99: up = np.array([0, 1.0, 0])
    r = np.cross(up, d); r /= np.linalg.norm(r); return d, r, np.cross(d, r)
SKIN, HAIR = (0, 6, 7, 9), (1, 4)
# texel raster
pos2 = np.zeros((S, S, 3), np.float32); pos = np.zeros((S, S, 3), np.float32); nor = np.zeros((S, S, 3), np.float32); cov = np.zeros((S, S), bool); prt = np.zeros((S, S), np.uint8)
for t in range(len(CO)):
    u = UV[t]; x = u[:, 0] * S; y = (1 - u[:, 1]) * S
    x0, x1 = int(max(np.floor(x.min()) - 1, 0)), int(min(np.ceil(x.max()) + 1, S - 1)); y0, y1 = int(max(np.floor(y.min()) - 1, 0)), int(min(np.ceil(y.max()) + 1, S - 1))
    if x1 < x0 or y1 < y0: continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
    if abs(d) < 1e-12: continue
    a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
    b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
    g = 1 - a - b
    m = (a >= -0.03) & (b >= -0.03) & (g >= -0.03)
    pos[y0:y1 + 1, x0:x1 + 1][m] = (a[..., None] * CO[t, 0] + b[..., None] * CO[t, 1] + g[..., None] * CO[t, 2])[m]
    pos2[y0:y1 + 1, x0:x1 + 1][m] = (a[..., None] * CO2[t, 0] + b[..., None] * CO2[t, 1] + g[..., None] * CO2[t, 2])[m]
    nor[y0:y1 + 1, x0:x1 + 1][m] = (a[..., None] * NO[t, 0] + b[..., None] * NO[t, 1] + g[..., None] * NO[t, 2])[m]
    cov[y0:y1 + 1, x0:x1 + 1][m] = True; prt[y0:y1 + 1, x0:x1 + 1][m] = PART[t]
nor /= np.maximum(np.linalg.norm(nor, axis=2, keepdims=True), 1e-6)
Pv = pos[cov]; Nv = nor[cov]; Pp = prt[cov]; Pv2 = pos2[cov].copy()
# Concubine face repaint (2026-11-01 evening): a tier whose landmarks carry 'face_clay': 'shp' had its close face painted on
# the RESHAPED head's clay (references_head/clay_shp_08_face.png, head_clay.py work/head_faces_shp.npz): 08_face is then
# projected from the reshaped texel positions, z-buffered on the reshaped head, with the clay landmarks of that clay
SHPFACE = SHP and LMJ[tier].get('face_clay') == 'shp'
if SHP:
    sys.path.insert(0, 'scripts'); import face_shape
    field = face_shape.make_field(dict(np.load('work/mesh_sub.npz')))
    sel = np.isin(Pp, (0, 9)); Pn = pos2[cov][sel].astype(np.float64)
    Pinv, res = face_shape.inverse(field, Pn)
    print('RESHAPE texels', int(sel.sum()), 'inverse residual mm %.4f' % (res * 1000), 'max shift mm %.1f' % (np.abs(Pinv - Pv[sel]).max() * 1000))
    Pv[sel] = Pinv
print('COVER', round(float(cov.mean()), 3))
def zbuffer(d, r, u, Cc, Oo, CO=CO):
    Z_ = np.full((R, R), -1e9, np.float32)
    px = ((CO - Cc) @ r / Oo + 0.5) * R; py = (0.5 - (CO - Cc) @ u / Oo) * R; dz = (CO - Cc) @ d
    for t in range(len(CO)):
        x, y, z = px[t], py[t], dz[t]
        x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), R - 1)); y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), R - 1))
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        det = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(det) < 1e-12: continue
        a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / det
        b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / det
        g = 1 - a - b; m = (a >= 0) & (b >= 0) & (g >= 0)
        sub = Z_[y0:y1 + 1, x0:x1 + 1]; sub[m] = np.maximum(sub[m], (a * z[0] + b * z[1] + g * z[2])[m])
    return Z_
# the face frame (the close view's job): front of the head, inside the hairline, between the ears, above the jaw line
FACE = (np.clip((0.072 - np.abs(Pv[:, 0])) / 0.015, 0, 1) * np.clip((0.035 - Pv[:, 1]) / 0.015, 0, 1)
        * np.clip((Pv[:, 2] - 0.775) / 0.015, 0, 1) * np.clip((0.985 - Pv[:, 2]) / 0.015, 0, 1))
def bbox(m):
    ys, xs = np.nonzero(m); return xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
def bilinear(im, x, y):
    h, w = im.shape[:2]; x = np.clip(x, 0, w - 1.001); y = np.clip(y, 0, h - 1.001)
    x0, y0 = x.astype(int), y.astype(int); fx, fy = (x - x0)[..., None], (y - y0)[..., None]; im = im.reshape(h, w, -1)
    return im[y0, x0] * (1 - fx) * (1 - fy) + im[y0, x0 + 1] * fx * (1 - fy) + im[y0 + 1, x0] * (1 - fx) * fy + im[y0 + 1, x0 + 1] * fx * fy
LUMW = np.array([0.2126, 0.7152, 0.0722])
SKINREF = np.array(LMJ[tier]['skin_rgb']) / 255; HAIRREF = np.array(LMJ[tier]['hair_rgb']) / 255
def classify(rgb):
    """per pixel: closeness to the tier's skin and hair colours (skin paint vs hair paint)"""
    ds = np.linalg.norm(rgb - SKINREF, axis=1); dh = np.linalg.norm(rgb - HAIRREF, axis=1)
    return ds < dh * 0.8, dh < ds * 0.8
acc = np.zeros((len(Pv), 3), np.float32); wt = np.zeros(len(Pv), np.float32); rep = {}
for name in ORDER:
    p = Path(f'references_head/{tier}_{name}_clean.png')
    if name == '08_face' and LMJ[tier].get('face_file'): p = Path('references_head/' + LMJ[tier]['face_file'])
    if not p.exists(): print('MISSING', p); continue
    d, r, u = cam(VIEWS[name]); Cc, Oo = (FC, FO) if name == '08_face' else (C, ORTHO)
    shp = SHPFACE and name == '08_face'; PV = Pv2 if shp else Pv
    zb = ndimage.maximum_filter(zbuffer(d, r, u, Cc, Oo, CO2 if shp else CO), 3)
    sx = (PV - Cc) @ r / Oo + 0.5; sy = 0.5 - (PV - Cc) @ u / Oo
    vis = (PV - Cc) @ d >= zb[np.clip((sy * R).astype(int), 0, R - 1), np.clip((sx * R).astype(int), 0, R - 1)] - 0.004
    facing = np.clip(Nv @ d, 0, 1)
    im = np.asarray(Image.open(p).convert('RGBA'), np.float32) / 255; H, W = im.shape[:2]; al = im[..., 3] > 0.5
    if name == '08_face':
        ix = sx * W - 0.5; iy = sy * H - 0.5
        src = np.array(LMJ['clay_face_shp' if shp else 'clay_face'], float); dst = np.array(LMJ[tier]['paint_face'], float) * (W / R)
        anchor = np.array([(0, 0), (R, 0), (0, R), (R, R), (R / 2, 0), (0, R / 2), (R, R / 2), (R / 2, R)], float)
        err = np.r_[dst - src * (W / R), np.zeros((len(anchor), 2))]
        f = RBFInterpolator(np.r_[src, anchor], err, kernel='thin_plate_spline', smoothing=0.5)
        q = np.c_[sx * R, sy * R]; dd = np.vstack([f(q[i:i + 200000]) for i in range(0, len(q), 200000)])
        ix = ix + dd[:, 0]; iy = iy + dd[:, 1]
        rep[name] = 'landmarks max err px %.0f' % np.abs(err).max()
    else:
        cl = np.asarray(Image.open(f'references_head/clay_{name}.png').convert('RGBA'))[..., 3] > 128; CH, CW = cl.shape
        ax0, ax1, ay0, ay1 = bbox(al); bx0, bx1, by0, by1 = bbox(cl)
        kx = (ax1 - ax0) / W / ((bx1 - bx0) / CW); ky = (ay1 - ay0) / H / ((by1 - by0) / CH)
        ox = ax0 / W - bx0 / CW * kx; oy = ay0 / H - by0 / CH * ky
        ix = (sx * kx + ox) * W - 0.5; iy = (sy * ky + oy) * H - 0.5; rep[name] = (round(kx, 3), round(ky, 3))
    rgb = bilinear(im[..., :3], ix, iy)
    skinlike, hairlike = classify(rgb)
    if tier == 'a':     # Ebora: dark red ear and cheek shading sits nearer the blue-black hair than the bright skin in RGB and got onto
        # the hair behind the left ear (head fixes 3); any clearly red paint counts as skin for the hair test
        skinlike = skinlike | ((rgb[:, 0] - rgb[:, 1:].max(1)) > 0.08)
    inner = ndimage.distance_transform_edt(al)
    edge = np.clip(bilinear(inner, ix, iy)[:, 0] / (0.012 * W), 0, 1)
    w = facing ** 3 * edge * vis * (bilinear(al.astype(np.float32), ix, iy)[:, 0] > 0.9)
    # inside the face frame the close view is the only source and paints brows, lashes and dark lips: no hair refusal there
    w = w * ~(skinlike & np.isin(Pp, HAIR)) * ~(hairlike & np.isin(Pp, SKIN) & (FACE < 0.5))
    if name == '08_face': w = w * FACE
    else: w = w * (1 - FACE)
    if name in ('06_q34r', '07_q34l'): w = w * 0.8
    if name in ('03_left', '04_right'): w = w * np.where(np.isin(Pp, SKIN), np.clip((Pv[:, 1] - 0.0) / 0.03, 0, 1), 1)
    if name == '05_top': w = w * (Pv[:, 2] > 0.98)
    ov = (w > 0.15) & (wt > 0.15)
    if ov.sum() > 500 and name != '08_face':
        g = np.clip((acc[ov] / wt[ov, None]).mean(0) / np.maximum(rgb[ov].mean(0), 1e-3), 0.8, 1.25); rgb = rgb * g
    acc += rgb * w[:, None]; wt += w
print('VIEWS', tier, rep, 'unseen', round(float((wt < 1e-3).mean()), 3))
ok = wt > 1e-3; tmp = np.zeros_like(acc); tmp[ok] = acc[ok] / wt[ok, None]
# weakly seen texels: the nearest well-seen texel of the same kind (skin / hair / horn) in 3D
kind = np.where(np.isin(Pp, SKIN), 0, np.where(np.isin(Pp, HAIR), 1, 2))
for k in (0, 1, 2):
    good = (kind == k) & (wt > 0.2); bad = (kind == k) & (wt <= 0.2)
    if not good.any() or not bad.any(): continue
    srcs = np.where(good)[0]; sub = srcs[:: max(1, len(srcs) // 60000)]
    d_, nn = cKDTree(Pv[sub]).query(Pv[bad], k=10); w_ = 1 / (d_ + 0.003) ** 2
    fill = (tmp[sub[nn]] * w_[..., None]).sum(1) / w_.sum(1, keepdims=True); kk = np.clip(wt[bad] / 0.2, 0, 1)[:, None]
    tmp[bad] = tmp[bad] * kk + fill * (1 - kk); ok[bad] = True
# nose bridge (coordinator, 2026-11-01: the bright streak down the ridge was the most visible thing on the front view): the
# ridge's highlight is compressed towards the mean of the skin within 9 mm in 3D
lumv = tmp @ LUMW.astype(np.float32)
# the calm siren face (2026-11-01 evening) has a soft painted bridge; at eye height the 'skin beside the nose' is the inner eye
# corners, which pulled the bridge into a dark band between the eyes: there the ridge stops below the eyes
ZRID = 0.876 if SHPFACE else 0.925
ridge = np.isin(Pp, SKIN) & (np.abs(Pv[:, 0]) < 0.012) & (Pv[:, 2] > 0.845) & (Pv[:, 2] < ZRID) & (Pv[:, 1] < 0.0)
if ridge.any():
    # head fixes 3: the target is the skin BESIDE the nose at the same height (12-22 mm out, dark lashes and brows left out);
    # the old 9 mm mean around the ridge kept the paint's pale highlight and face_shape.py widened it into a pale stripe
    sk = np.where(np.isin(Pp, SKIN) & (np.abs(Pv[:, 0]) > 0.012) & (np.abs(Pv[:, 0]) < 0.022) & (Pv[:, 2] > 0.835)
                  & (Pv[:, 2] < 0.935) & (Pv[:, 1] < 0.02) & (lumv > 0.25)
                  & (tmp[:, 0] - tmp[:, 1:].max(1) > 0.2))[0]     # clearly skin: no lash, brow or eye-corner grey
    zb = np.round((Pv[sk, 2] - 0.835) / 0.003).astype(int); ref = {}
    for k_ in np.unique(zb): ref[k_] = np.median(tmp[sk[zb == k_]], axis=0)
    keys = np.array(sorted(ref)); vals = np.array([ref[k_] for k_ in keys])
    q = (Pv[ridge, 2] - 0.835) / 0.003
    mean = np.stack([np.interp(q, keys, vals[:, c]) for c in range(3)], 1)
    fall = np.clip(1 - np.abs(Pv[ridge, 0]) / 0.012, 0, 1); fall = (fall * fall * (3 - 2 * fall))[:, None]
    if SHPFACE: fall = fall * np.clip((ZRID - Pv[ridge, 2]) / 0.008, 0, 1)[:, None]     # feathered top
    tmp[ridge] = tmp[ridge] * (1 - 0.65 * fall) + mean * 0.65 * fall
    print('NOSE ridge texels softened', int(ridge.sum()))
# centre hairline (coordinator, 2026-11-01: "dark brown rectangular stub"): the paint's deep shadow of the clay's old notch sits on the
# hair strip between the fringe arms (luminance 20-39 against 55 beside it); it takes the colour of the hair around it
notch = np.isin(Pp, HAIR) & (np.abs(Pv[:, 0]) < 0.025) & (Pv[:, 2] < 0.988) & (Pv[:, 1] < 0.02)
if notch.any():
    srcs = np.where(np.isin(Pp, HAIR) & ~notch & (Pv[:, 1] < 0.03) & (Pv[:, 2] > 0.93) & (Pv[:, 2] < 1.03))[0]
    srcs = srcs[:: max(1, len(srcs) // 40000)]
    d_, nn = cKDTree(Pv[srcs]).query(Pv[notch], k=24); w_ = 1 / (d_ + 0.004) ** 2
    fill = (tmp[srcs[nn]] * w_[..., None]).sum(1) / w_.sum(1, keepdims=True)
    edge = np.clip((0.025 - np.abs(Pv[notch, 0])) / 0.008, 0, 1) * np.clip((0.988 - Pv[notch, 2]) / 0.006, 0, 1)
    tmp[notch] = tmp[notch] * (1 - 0.85 * edge[:, None]) + fill * 0.85 * edge[:, None]
    print('NOTCH hair texels filled', int(notch.sum()))
# the painted notch (Codex drew the clay's old hairline notch as a dark block down the forehead centre, |x| < 1.2 cm, z 0.925-0.99;
# coordinator 2026-11-01): those skin texels take the clean forehead skin straight below them (z 0.895-0.92), feathered at the sides
col_ = (Pp == 0) & (np.abs(Pv[:, 0]) < 0.022) & (Pv[:, 2] > 0.922) & (Pv[:, 1] < 0.08)     # back over the scalp the hair tongue used to cover
src = np.where((Pp == 0) & (np.abs(Pv[:, 0]) < 0.03) & (Pv[:, 2] > 0.895) & (Pv[:, 2] < 0.918) & (Pv[:, 1] < 0.0))[0]
if col_.any() and len(src):
    src = src[:: max(1, len(src) // 30000)]
    q = Pv[col_].copy(); q[:, 2] = 0.907
    d_, nn = cKDTree(Pv[src]).query(q, k=16); w_ = 1 / (d_ + 0.004) ** 2
    fill = (tmp[src[nn]] * w_[..., None]).sum(1) / w_.sum(1, keepdims=True)
    # feathered at the sides and the bottom (head fixes 3: the hard bottom edge at z 0.922 read as a lighter block)
    k_ = np.where(Pv[col_, 2] > 0.96, 1.0, np.clip((0.016 - np.abs(Pv[col_, 0])) / 0.008, 0, 1)
                  * np.clip((Pv[col_, 2] - 0.922) / 0.014, 0, 1))[:, None]
    hs = np.where(np.isin(Pp, HAIR) & (np.abs(Pv[:, 0]) > 0.02) & (np.abs(Pv[:, 0]) < 0.05) & (Pv[:, 2] > 0.96) & (Pv[:, 2] < 1.03) & (Pv[:, 1] < 0.01))[0]
    hs = hs[:: max(1, len(hs) // 30000)]
    qh = Pv[col_].copy(); qh[:, 0] = np.sign(qh[:, 0] + 1e-6) * 0.03
    d2, n2 = cKDTree(Pv[hs]).query(qh, k=16); w2 = 1 / (d2 + 0.004) ** 2
    hfill = (tmp[hs[n2]] * w2[..., None]).sum(1) / w2.sum(1, keepdims=True)
    up = np.clip((Pv[col_, 2] - 0.952) / 0.010, 0, 1)[:, None]; up = up * up * (3 - 2 * up)     # scalp under the arch reads as hair
    fill = fill * (1 - up) + hfill * up
    tmp[col_] = tmp[col_] * (1 - k_) + fill * k_
    print('NOTCH paint replaced', int(col_.sum()))
# lip junction (head fixes 3): the wider mouth shows the faces inside the junction (turned up, down or back, no view painted
# them, so the fill gave skin: a pale slit between the lips). They take a deep tone of the painted lips
lipz = 0.832
crev = (np.isin(Pp, (0, 9)) & (np.abs(Pv[:, 2] - lipz) < 0.0035) & (np.abs(Pv[:, 0]) < 0.0115) & (Pv[:, 1] < 0.01)
        & (Nv[:, 1] > -0.75))
if crev.any():
    zone = np.where(np.isin(Pp, (0, 9)) & (np.abs(Pv[:, 2] - lipz) < 0.004) & (np.abs(Pv[:, 0]) < 0.009) & (Nv[:, 1] < -0.75))[0]
    lz = tmp[zone] @ LUMW.astype(np.float32); dark = np.median(tmp[zone[lz <= np.percentile(lz, 25)]], axis=0) * 0.8     # a deep lip tone (the darkest 8 % was black: a heavy band)
    k_ = (np.clip((Nv[crev, 1] + 0.75) / 0.3, 0, 1) * np.clip((0.0115 - np.abs(Pv[crev, 0])) / 0.002, 0, 1)
          * np.clip((0.0035 - np.abs(Pv[crev, 2] - lipz)) / 0.001, 0, 1))[:, None]
    tmp[crev] = tmp[crev] * (1 - k_) + dark * k_
    print('LIP junction texels darkened', int(crev.sum()), 'colour', np.round(dark * 255).tolist())
if tier == 's':
    # Concubine face and hair fix (user, 2026-11-01 evening: "ugly face"): (1) the neck seam. The head skin meets the torso in
    # 22 zigzag edges at z 0.75-0.77, and the torso paint there is lighter and yellower (219,159,111 against 210,129,94): a
    # jagged pale line across the neck. Per seam point a linear gain torso/head (medians of skin within 2 cm / 1.2 cm), spread
    # over the head skin by inverse distance and faded out 4 cm above the seam (the face is untouched)
    lin_ = lambda v: np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
    enc_ = lambda v: np.where(v <= 0.0031308, v * 12.92, 1.055 * np.maximum(v, 0) ** (1 / 2.4) - 0.055)
    Dm_ = np.load('work/mesh_sub.npz'); mco, mtri, mmat, mcomp, muv = Dm_['co'] * [-1, 1, 1], Dm_['tri'], Dm_['mat'], Dm_['comp'], Dm_['uv']
    mn_ = [str(x) for x in Dm_['matnames']]; hi_, ti_ = mn_.index('EboraHead'), mn_.index('EboraTorso')
    wk = np.unique(np.round(mco, 5), axis=0, return_inverse=True)[1].ravel()
    th_ = mtri[(mmat == hi_) & (mcomp[mtri].max(1) == 0)]
    e_ = np.sort(wk[np.r_[th_[:, [0, 1]], th_[:, [1, 2]], th_[:, [2, 0]]]], 1); ue, ce = np.unique(e_, axis=0, return_counts=True)
    Pw = np.zeros((wk.max() + 1, 3)); Pw[wk] = mco
    seam = (Pw[ue[ce == 1, 0]] + Pw[ue[ce == 1, 1]]) / 2; seam = seam[seam[:, 2] < 0.80]
    TOR = np.asarray(Image.open('textures/sr_torso_tone.png').convert('RGB'), np.float32) / 255
    tt_ = mtri[mmat == ti_]; tc_ = mco[tt_].mean(1); near = cKDTree(seam).query(tc_)[0] < 0.05; tt_ = tt_[near]
    bc = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4], [2, 2, 1], [1, 2, 2], [2, 1, 2]], float); bc /= bc.sum(1, keepdims=True)
    tp = np.einsum('kc,fcd->fkd', bc, mco[tt_]).reshape(-1, 3); tuv = np.einsum('kc,fcd->fkd', bc, muv[tt_]).reshape(-1, 2)
    tcol = bilinear(TOR, tuv[:, 0] * TOR.shape[1] - 0.5, (1 - tuv[:, 1]) * TOR.shape[0] - 0.5)
    tsk = (tcol[:, 0] > 0.35) & (tcol[:, 0] > tcol[:, 2] * 1.3); tp, tcol = tp[tsk], tcol[tsk]
    hsk = np.where(np.isin(Pp, SKIN) & (Pv[:, 2] < 0.80))[0]
    hcol = tmp[hsk]; hskm = (hcol[:, 0] > 0.35) & (hcol[:, 0] > hcol[:, 2] * 1.3)
    kt, kh = cKDTree(tp), cKDTree(Pv[hsk[hskm]])
    g_ = np.ones((len(seam), 3), np.float32)
    for j, s_ in enumerate(seam):
        it = kt.query_ball_point(s_, 0.02); ih = kh.query_ball_point(s_, 0.012)
        if len(it) > 20 and len(ih) > 20:
            g_[j] = np.median(lin_(tcol[it]), 0) / np.maximum(np.median(lin_(hcol[hskm][ih]), 0), 1e-4)
    g_ = np.clip(g_, 0.6, 1.8)
    sel_ = np.where(np.isin(Pp, SKIN) & (Pv[:, 2] < 0.83))[0]
    d_, nn = cKDTree(seam).query(Pv[sel_], k=min(6, len(seam))); w_ = 1 / (d_ + 0.004) ** 2
    gp = (g_[nn] * w_[..., None]).sum(1) / w_.sum(1, keepdims=True)
    fall = 1 - np.clip(d_[:, 0] / 0.04, 0, 1); fall = (fall * fall * (3 - 2 * fall))[:, None]
    tmp[sel_] = enc_(lin_(tmp[sel_]) * (1 + fall * (gp - 1)))
    print('NECK seam gain', len(seam), 'points, median', np.round(np.median(g_, 0), 3).tolist(), 'texels', int((fall > 0.01).sum()))
    # (2) the underside of the chin and jaw: no view sees it (facing^3 ~ 0), so the fill carried the jaw-line shading in as a
    # dark brown patch, read from below (party height) as a muddy chin. Those texels are lightened towards the neck front's
    # skin (only lightened, low frequency: the local 1 cm mean is matched, detail kept). The underside gets no top light in
    # the viewer or the engine (ambient only below the horizon), so it is painted up to 18 % lighter than the neck where it
    # faces down: still a soft shade under the jaw, no dark 'goatee'
    neck = np.where(np.isin(Pp, SKIN) & (Pv[:, 2] > 0.755) & (Pv[:, 2] < 0.78) & (Nv[:, 1] < -0.3) & (np.abs(Pv[:, 0]) < 0.03))[0]
    T_ = np.median(tmp[neck], 0)
    jaw = np.where(np.isin(Pp, SKIN) & (Pv[:, 2] > 0.75) & (Pv[:, 2] < 0.85) & (np.abs(Pv[:, 0]) < 0.07) & (Pv[:, 1] < 0.06)
                   & (Nv[:, 2] < -0.05))[0]
    sub = jaw[:: max(1, len(jaw) // 60000)]
    d2, n2 = cKDTree(Pv[sub]).query(Pv[jaw], k=24); loc = tmp[sub][n2].mean(1)
    kd = np.clip((-Nv[jaw, 2] - 0.2) / 0.5, 0, 1)[:, None]; kd = kd * kd * (3 - 2 * kd)
    # the local mean is moved to the target colour (additive, so the detail stays and a ruddy cast goes too; a per-channel
    # gain saturated a blush spot to orange); where the mean is already lighter, only half the shift (hue). Kept off the
    # lower lip: the limit follows the jaw line, which rises towards the ears
    tgt = T_ * (1 + 0.18 * kd); shift = tgt - loc
    lighter = (loc @ LUMW.astype(np.float32)) >= (tgt @ LUMW.astype(np.float32))
    shift[lighter] *= 0.5
    zmax = 0.822 + 0.5 * np.maximum(np.abs(Pv[jaw, 0]) - 0.02, 0)
    k_ = (np.clip((-Nv[jaw, 2] - 0.05) / 0.35, 0, 1) * np.clip((zmax - Pv[jaw, 2]) / 0.008, 0, 1)
          * np.clip((0.07 - np.abs(Pv[jaw, 0])) / 0.02, 0, 1))
    k_ = (k_ * k_ * (3 - 2 * k_))[:, None]
    tmp[jaw] = np.clip(tmp[jaw] + k_ * shift, 0, 1)
    print('JAW underside lightened', int((k_ > 0.05).sum()), 'texels to', np.round(T_ * 255).tolist())
# ears (part 7, long flat cards beside the cheeks): soft form shading, darker towards the back edge and the root
ear = Pp == 7
if ear.any():
    t_back = np.clip((Pv[ear, 1] - 0.005) / 0.08, 0, 1); t_root = np.clip((0.085 - np.abs(Pv[ear, 0])) / 0.02, 0, 1)
    shade = 1.0 - 0.28 * t_back - 0.12 * t_root
    tmp[ear] = tmp[ear] * shade[:, None]
    print('EAR texels shaded', int(ear.sum()))
col = np.zeros((S, S, 3), np.float32); have = np.zeros((S, S), bool); col[cov] = tmp; have[cov] = ok
idx = ndimage.distance_transform_edt(~have, return_distances=False, return_indices=True); col = col[idx[0], idx[1]]
Image.fromarray((np.clip(col, 0, 1) * 255 + .5).astype('u1')).save(f'textures/{pre}_head_proj.png')
lum = col @ LUMW.astype(np.float32)
im1k = np.asarray(Image.fromarray((lum * 255).astype('u1')).resize((1024, 1024), Image.LANCZOS), np.float32) / 255
hp = ndimage.gaussian_filter(im1k, 1.2) - ndimage.gaussian_filter(im1k, 8)
gx = ndimage.sobel(hp, axis=1) * 0.45; gy = ndimage.sobel(hp, axis=0) * 0.45     # gentle: the paint already carries the form shading (1.6 read as orange peel)
n = np.dstack([-gx, gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * 0.5 + 0.5) * 255 + .5).astype('u1')).save(f'textures/{pre}_head_pnormal.png')
print('HEAD', tier, pre, 'done')
