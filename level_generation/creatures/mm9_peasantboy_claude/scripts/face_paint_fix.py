#!/usr/bin/env python3
"""Face paint fixes on a head set (positions from head_texel_pos.py; glTF rest, floor 0, +Z front):
1. Closed mouth: the retextures painted slightly parted lips with teeth; in the mouth box (|x| < 2.2 cm, 0.8 cm around
   the lip line, front) low-saturation light texels (teeth) take the lips' own median red x 0.85.
2. Hair strands on skin: Meshy drew thin dark hair strokes across the jaw, chin and neck skin; below the lower lip and above the
   collar, in front of the ear plane, skin-hued texels where a grey closing (7 px) is more than 12 levels lighter take the closing.
3. Nose (second pass, orchestrator 2026-11-02: "a dark brown smudge down one side of the nose"): Meshy baked its side light
   into the paint; the mid-face zone (|x| < 4.5 cm, 1.155-1.25 m, front; after the mouth, so it is symmetric too) takes, on its darker side, the colours of the mirrored
   texel on the lighter side (the geometry is symmetric, so the nostrils still fit it), feathered over 4 mm at the midline
   and 3 mm at the zone's edge.
4. Mouth (second pass: "A reads parted, B's lips swollen"): a closed, calm mouth is painted on the slit
   (work/mouth_slit.json, mouth_slit.py): upper lip 3 mm and lower lip 5.2 mm high at the centre, tapering to the corners
   2.1 cm out, in the lips' own median red; skin elsewhere in the box (the box's ring median); a soft dark line where the
   lips meet; the paint's own fine luminance detail (+-8 %) kept on top.
Reads <prefix>_head_basecolor.png and writes it back (the chain re-composes from Meshy first). Also writes
work/hand_ref_<prefix>.txt (the cheek skin median) for hand_clean.py. Usage: face_paint_fix.py <prefix> ..."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
pos = np.load('work/head_texel_pos.npz')['pos']
ok = np.isfinite(pos[..., 0])
X, Y, Z = np.nan_to_num(pos[..., 0]), np.nan_to_num(pos[..., 1]), np.nan_to_num(pos[..., 2])
LIP = 1.178
mouth = ok & (np.abs(X) < 0.022) & (np.abs(Y - LIP) < 0.008) & (Z > 0.035)
lower = ok & (Y < LIP - 0.012) & (Y > 1.085) & (Z > -0.035)    # above the collar (1.08): the vest knit is no skin
import json, os
from scipy.spatial import cKDTree
SL = np.array(json.load(open('work/mouth_slit.json')))
xs_ = np.linspace(-0.0094, 0.0094, 9)
# the slit loop is the BACK of the mouth (inside, 7-8 mm lower than where the lips meet in front: a debug paint of the
# zone put its mean below the visible mouth); the lip line is the slit's top rim + LIPUP, a gentle smile curve
LIPUP = float(os.environ.get('LIPUP', 0.004))
yc_ = np.array([SL[np.abs(SL[:, 0] - x) < 0.004, 1].max() for x in xs_]) + LIPUP
NX = 0.045
nose = ok & (np.abs(X) < NX) & (Y > 1.155) & (Y < 1.25) & (Z > 0.025)
# boy b's -x cheek keeps a pale patch from the head-layout transfer: his +x side is the source
SRC_SIDE = {'pboyb_tp': 1}
mbox = ok & (np.abs(X) < 0.030) & (np.abs(Y - yc_.mean()) < 0.016) & (Z > 0.035)
cheek = ok & (np.abs(X) > 0.03) & (np.abs(X) < 0.05) & (Y > 1.19) & (Y < 1.215) & (Z > 0.03)


def lipcentre(x):
    return np.interp(x, xs_, yc_)


for pre in sys.argv[1:]:
    p = f'textures/{pre}_head_basecolor.png'
    im = np.asarray(Image.open(p).convert('RGB')).astype(np.float64)
    mx, mn = im.max(2), im.min(2)
    sat = (mx - mn) / np.maximum(mx, 1)
    lum = im @ [0.299, 0.587, 0.114]
    teeth = mouth & (sat < 0.35) & (lum > 95)
    fixm = ndimage.binary_dilation(teeth, iterations=1) & mouth & (sat < 0.45)
    lipred = mouth & ~fixm & (im[..., 0] > im[..., 1] * 1.35) & (lum > 80)
    lipcol = np.median(im[lipred], 0) if lipred.sum() > 50 else np.array([150.0, 80.0, 75.0])
    out = im.copy()
    out[fixm] = lipcol * 0.85          # the teeth between parted lips become lip: the mouth reads closed
    # strands
    cl = np.stack([ndimage.grey_closing(im[..., c], size=(7, 7)) for c in range(3)], -1)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    skinish = (cl[..., 0] > cl[..., 1]) & (cl[..., 1] > cl[..., 2]) & (cl @ [0.299, 0.587, 0.114] > 115) & ((cl[..., 0] - cl[..., 2]) > 55) & ((cl[..., 0] - cl[..., 1]) > 35)
    skinish &= ndimage.binary_erosion(skinish, iterations=3)     # keep off the collar's edge (cream linen is not skin)
    strand = lower & skinish & ((cl - im).mean(2) > 12)
    strand = ndimage.binary_dilation(strand, iterations=1) & lower & skinish
    out[strand] = cl[strand]
    # 4. mouth (fourth pass, user: "look at his mouth"): the face shell is closed at the mouth and its lips meet in a shallow
    # dent at rest z 0.6936 (glTF 1.1761, mouth_close.py removed Meshy's loose lip pieces in front of it). One closed mouth is
    # painted exactly there: lip line LINE (corners 2 mm up at |x| = HALF), upper lip 3.2 mm, lower lip 4.8 mm at the centre,
    # clearly pink lips (skin moved 75 % toward a pink of the skin's own hue), a soft line where they meet, corners fading into
    # the cheeks; the whole mouth box is smooth (no Meshy lip wrinkles: they drew the old lumpy lower lip).
    LINE, HALF = 1.1761, 0.0235
    # (fifth pass: a lip shape, not a band) upper lip thin with a gentle cupid's bow, lower lip fuller with a soft centre
    # highlight, the colour deepest at the inner lips fading to skin at the edges, the parting line darker in the middle and
    # fading at the corners; on the sculpted lips of lip_sculpt.py
    ax = np.abs(X)
    u = np.clip(ax / HALF, 0, 1.5)
    yc = LINE + 0.0020 * np.clip(u, 0, 1) ** 2
    dyl = Y - yc
    t = np.clip(1 - u ** 2, 0, 1)
    bow = 1 + 0.35 * np.exp(-((ax - 0.0045) / 0.0028) ** 2) - 0.25 * np.exp(-(X / 0.0020) ** 2)
    up = 0.0028 * t ** 0.55 * bow
    lo = 0.0052 * t ** 0.6
    soft = 0.0012
    edge = np.where(dyl >= 0, np.clip((up - dyl) / soft + 0.5, 0, 1), np.clip((lo + dyl) / soft + 0.5, 0, 1))
    edge = edge * np.clip(t / 0.3, 0, 1)
    inner = np.exp(-(dyl / 0.0024) ** 2)
    amount = edge * (0.55 + 0.35 * inner)
    ring = ok & (np.abs(X) < 0.035) & (np.abs(Y - LINE) > 0.016) & (np.abs(Y - LINE) < 0.024) & (Z > 0.03)
    skincol = np.median(out[ring], 0)
    rose = np.array([min(255.0, skincol[0] * 0.95), skincol[1] * 0.60, skincol[2] * 0.74])
    col = skincol[None, None, :] + (rose - skincol)[None, None, :] * amount[..., None]
    hl_ = 0.10 * np.exp(-(X / 0.006) ** 2 - ((dyl + 0.0022) / 0.0011) ** 2) * t
    line = np.exp(-(dyl / 0.0005) ** 2) * t ** 0.8
    corner = np.exp(-(((ax - HALF) / 0.0025) ** 2 + (dyl / 0.0018) ** 2))
    col = col * (1 + hl_[..., None]) * (1 - 0.40 * line[..., None]) * (1 - 0.14 * corner[..., None])
    fe = np.clip((0.034 - np.abs(X)) / 0.005, 0, 1) * np.clip((0.016 - np.abs(Y - LINE)) / 0.004, 0, 1)
    mbox2 = ok & (np.abs(X) < 0.034) & (np.abs(Y - LINE) < 0.016) & (Z > 0.03)
    fw = (mbox2 * fe)[..., None]
    out = out * (1 - fw) + col * fw
    lipcol = rose
    # 6. glabella (fifth pass: a dark smudge between the brows on a and e): texels between the brows (|x| < 1.1 cm, glTF
    # y 1.228-1.262, front) darker than 0.94 x the forehead skin take the forehead skin at their own fine detail (+-5 %)
    fh = ok & (np.abs(X) < 0.025) & (Y > 1.266) & (Y < 1.285) & (Z > 0.03)
    fcol = np.median(out[fh], 0)
    gl = ok & (np.abs(X) < 0.011) & (Y > 1.228) & (Y < 1.262) & (Z > 0.03)
    lumo = out @ [0.299, 0.587, 0.114]
    flum = float(fcol @ [0.299, 0.587, 0.114])
    dark = gl & (lumo < 0.94 * flum)
    dark = ndimage.binary_dilation(dark, iterations=2) & gl
    detg = np.clip(lumo / np.maximum(ndimage.gaussian_filter(lumo, 4), 1), 0.95, 1.05)
    wg = np.clip((0.94 * flum - lumo) / (0.10 * flum), 0, 1) * np.clip((0.011 - np.abs(X)) / 0.003, 0, 1)
    wg = (wg * dark)[..., None]
    # target: the surrounding skin's own low-pass with the dark texels left out (normalised convolution), so the fill keeps
    # the face's gradient instead of a flat forehead-coloured plate
    keep = (ok & ~dark).astype(float)
    num = np.stack([ndimage.gaussian_filter(out[..., c] * keep, 10) for c in range(3)], -1)
    den = ndimage.gaussian_filter(keep, 10)[..., None]
    lp = num / np.maximum(den, 1e-3)
    out = out * (1 - wg) + (lp * detg[..., None]) * wg
    glab_n = int(dark.sum())
    # 5. eyes (fourth pass, user review: reddish rims): around each eye (rest z 0.725-0.755, |x| 1-4.6 cm, front) texels
    # redder than the cheek skin (r/g above the cheek's x 1.08) move 75 % toward the cheek's hue at their own luminance
    cheekc = np.median(out[cheek], 0)
    eyez = ok & (Y > 1.205) & (Y < 1.24) & (np.abs(X) > 0.010) & (np.abs(X) < 0.046) & (Z > 0.02)
    rg = out[..., 0] / np.maximum(out[..., 1], 1)
    redm = eyez & (rg > (cheekc[0] / cheekc[1]) * 1.08)
    lumo = out @ [0.299, 0.587, 0.114]
    target = cheekc[None, :] * (lumo[redm] / max(float(cheekc @ [0.299, 0.587, 0.114]), 1))[:, None]
    out[redm] = out[redm] * 0.25 + target * 0.75
    # 3. nose: mirror the lighter side
    lumo = out @ [0.299, 0.587, 0.114]
    L_neg = lumo[nose & (X < -0.004)].mean(); L_pos = lumo[nose & (X > 0.004)].mean()
    src_side = SRC_SIDE.get(pre, 1 if L_pos >= L_neg else -1)
    srcm = nose & (np.sign(X) == src_side) & (np.abs(X) > 0.0005)
    sy, sx = np.nonzero(srcm)
    tree = cKDTree(np.c_[X[srcm], Y[srcm], Z[srcm]])
    dy, dx = np.nonzero(nose & (np.sign(X) == -src_side))
    d, k = tree.query(np.c_[-X[dy, dx], Y[dy, dx], Z[dy, dx]])
    w = np.clip(np.abs(X[dy, dx]) / 0.004, 0, 1) * 0.5 + 0.5
    edge = np.minimum.reduce([(NX - np.abs(X[dy, dx])) / 0.004, (Y[dy, dx] - 1.155) / 0.003, (1.25 - Y[dy, dx]) / 0.003])
    w = w * np.clip(edge, 0, 1) * (d < 0.003)
    out[dy, dx] = out[dy, dx] * (1 - w[:, None]) + out[sy[k], sx[k]] * w[:, None]
    Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(p)
    href = np.median(out[cheek], 0)
    open(f'work/hand_ref_{pre}.txt', 'w').write(','.join(f'{v:.1f}' for v in href))
    print('FACEFIX2', pre, 'glabella texels', glab_n, 'eye rim texels', int(redm.sum()), 'nose source side', src_side, 'lip', lipcol.round(0).tolist(), 'skin', skincol.round(0).tolist(), 'cheek', href.round(0).tolist())
    print('FACEFIX', pre, 'mouth texels', int(fixm.sum()), 'strand texels', int(strand.sum()))
