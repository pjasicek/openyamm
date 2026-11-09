#!/usr/bin/env python3
"""Ebora tone pass (project folder): MM9's skin is a deep red-orange (median sRGB 204,39,13); Meshy painted a light
peach-orange (245-255,101,52). Skin texels (soft mask by hue, saturation and value) are scaled in linear light towards
TARGET; nothing else changes. On the head set, orange skin paint that Meshy put on the hair and fringe charts (seen at
the forehead and temples) is replaced by the hair colour around it. Writes textures/eb_<set>_tone.png.
Args: [target r,g,b] (default 212,52,20)"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
import os
PRE = os.environ.get('PRE', 'eb')
T = np.array([float(x) for x in (sys.argv[1] if len(sys.argv) > 1 else '212,52,20').split(',')]) / 255
SRC = np.array([float(x) for x in os.environ.get('SRC', '248,102,51').split(',')]) / 255
HUE = float(os.environ.get('HUE', '0.045')); SAT = [float(x) for x in os.environ.get('SAT', '0.30,0.50').split(',')]
lin = lambda v: np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
enc = lambda v: np.where(v <= 0.0031308, v * 12.92, 1.055 * np.maximum(v, 0) ** (1 / 2.4) - 0.055)
K = lin(T) / lin(SRC)
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def hsv(a):
    mx = a.max(-1); mn = a.min(-1); d = mx - mn + 1e-9
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6
    return h, d / (mx + 1e-9), mx
def skin_w(a):
    h, s, v = hsv(a)
    hd = np.minimum(np.abs(h - HUE), 1 - np.abs(h - HUE))
    w = (1 - ss(hd, 0.035, 0.065)) * ss(s, SAT[0], SAT[1]) * ss(v, 0.12, 0.30)
    if len(SAT) > 2: w = w * (1 - ss(s, SAT[2], SAT[3]))
    return w
D = np.load('work/uv_frozen.npz'); tri, uv, mat, comp = D['tri'], D['uv'], D['mat'], D['comp']
NAMES = ['body', 'hair', 'belt', 'horns', 'fringe', 'emblem', 'eyes', 'ears', 'spikes', 'mouth', 'drop']
for s in ('torso', 'head', 'legs'):
    PROJ = s == 'head' and os.path.exists(f'textures/{PRE}_head_proj.png')     # head pass 2026-11-01: the projected Codex head replaces Meshy's
    a = np.asarray(Image.open(f'textures/{PRE}_head_proj.png' if PROJ else f'textures/{PRE}_{s}_raw_graded.png').convert('RGB'), np.float64) / 255
    w = skin_w(a)[..., None]
    Kx = K
    if PROJ and PRE == 'sr': Kx = np.ones(3)      # siren: the projected face is already on MM9's SIREN1 tone (206,135,98 vs 222,152,109); a seam gain lightened it
    if PROJ and PRE == 'eb':      # the projected head takes the body's skin tone at the neck seam (seam_gain.py: per-channel linear gain)
        import subprocess, json as _j
        sg = _j.loads(subprocess.check_output([sys.executable, '-W', 'ignore', 'scripts/seam_gain.py', PRE]).decode().strip().splitlines()[-1])
        Kx = np.array(sg['gain']); print('head seam gain', sg)
    o_lin = lin(a) * (1 - w + w * Kx)
    if PROJ and PRE == 'eb':      # head fixes 3: the seam gain (R x1.3) clipped the light mid-face at 255, a flat pale nose plane;
        k0 = 0.72                 # a soft shoulder keeps the highlight gradient
        o_lin = np.where(o_lin > k0, k0 + (1 - k0) * np.tanh((o_lin - k0) / (1 - k0)), o_lin)
        print('head highlight shoulder: texels over 0.98 linear R', int((o_lin[..., 0] > 0.98).sum()))
    out = enc(o_lin)
    if PRE == 'eb' and not PROJ:      # Meshy's dark slash marks in the skin (upper chest by the straps): small dark islands inside skin, inpainted
        sw = skin_w(out) > 0.5
        skin_area = ndi.binary_closing(sw, iterations=6)
        lum = out @ np.array([0.2126, 0.7152, 0.0722])
        med = ndi.median_filter(np.where(sw, lum, np.nan_to_num(lum)), size=15)
        dark = skin_area & ~sw & (lum < 0.80 * med)
        lab, n = ndi.label(dark); sz = ndi.sum(dark, lab, range(1, n + 1))
        small = np.isin(lab, 1 + np.where(sz < 400)[0]) & (lab > 0)
        # keep islands fully surrounded by skin (not the edge of a strap or glove)
        ring = ndi.binary_dilation(small, iterations=3) & ~ndi.binary_dilation(small, iterations=1)
        lab2, n2 = ndi.label(small); keep = np.zeros(n2 + 1, bool)
        for k in range(1, n2 + 1):
            r = ndi.binary_dilation(lab2 == k, iterations=3) & ~(lab2 == k)
            keep[k] = sw[r].mean() > 0.85 if r.any() else False
        fix = keep[lab2] & (lab2 > 0)
        fix = ndi.binary_dilation(fix, iterations=1)
        idx = ndi.distance_transform_edt(fix, return_distances=False, return_indices=True)
        fw = ndi.gaussian_filter(fix.astype(float), 1.0)[..., None]
        out = out * (1 - fw) + out[idx[0], idx[1]] * fw
        print(s, 'skin marks inpainted', int(fix.sum()), 'texels')
    if s == 'head' and PRE == 'eb' and not PROJ:
        Hh, Ww = a.shape[:2]
        hm = Image.new('L', (Ww, Hh), 0); dr = ImageDraw.Draw(hm)
        for t, m_ in zip(tri, mat):
            if m_ != 1 or comp[t[0]] not in (NAMES.index('hair'), NAMES.index('fringe')): continue
            dr.polygon([(float(uv[i, 0] * 2 * Ww), float((1 - (uv[i, 1] - 0.5) * 2) * Hh)) for i in t], fill=255)
        hm = ndi.binary_dilation(np.asarray(hm) > 0, iterations=2)
        bad = hm & (skin_w(a) > 0.15)
        good = hm & ~ndi.binary_dilation(bad, iterations=2)
        idx = ndi.distance_transform_edt(~good, return_distances=False, return_indices=True)
        fill = out[idx[0], idx[1]]
        bw = ndi.gaussian_filter(bad.astype(float), 1.2)[..., None] * hm[..., None]
        out = out * (1 - bw) + fill * bw
        print('hair texels repainted', int(bad.sum()))
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype('u1')).save(f'textures/{PRE}_{s}_tone.png')
    print(s, 'skin weight mean', round(float(w.mean()), 3))
