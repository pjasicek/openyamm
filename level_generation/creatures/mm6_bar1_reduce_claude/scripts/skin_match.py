#!/usr/bin/env python3
"""Match the head set's skin to the body skin. The tier ramps only recolour clothing, so the skin shows the baked base
colour, and the 1K head set (atlas x >= 1056: face, lips, circlet) came out darker and browner than the body.
Body skin = texels of body-set faces in the upper chest/shoulder/arm band (z 1.15-1.50) outside the region mask
whose colour is skin-like; head skin = head-set texels near the median of its skin-like texels (it also
holds hair islands). Head texels move by a Lab
mean transfer (contrast change capped at 1.15x) plus REA_SKIN_LIFT (default 6) in L*:
the face is vertical and under the hair, so it gets less light than the upward-facing chest, weighted by skin likelihood (distance to the head skin cluster, blurred) so eyes, brows, lips and
the circlet keep their colours. -> work/basecolor_skinmatch.png, review/skin/head_before_after.png; prints Lab stats."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

class color:  # sRGB (D65) <-> CIE Lab
    M = np.array([[.4124564, .3575761, .1804375], [.2126729, .7151522, .0721750], [.0193339, .1191920, .9503041]])
    WP = np.array([.95047, 1., 1.08883])
    @staticmethod
    def rgb2lab(c):
        l = np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4); x = l @ color.M.T / color.WP
        f = np.where(x > (6 / 29) ** 3, np.cbrt(x), x / (3 * (6 / 29) ** 2) + 4 / 29)
        return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)
    @staticmethod
    def lab2rgb(L):
        fy = (L[..., 0] + 16) / 116; f = np.stack([fy + L[..., 1] / 500, fy, fy - L[..., 2] / 200], -1)
        x = np.where(f > 6 / 29, f ** 3, 3 * (6 / 29) ** 2 * (f - 4 / 29)) * color.WP
        l = np.clip(x @ np.linalg.inv(color.M).T, 0, None)
        return np.where(l <= .0031308, l * 12.92, 1.055 * l ** (1 / 2.4) - .055)
img = Image.open('work/img0.png').convert('RGB'); W, H = img.size; X0 = 1056
rgb = np.asarray(img, np.float32) / 255; lab = color.rgb2lab(rgb)
mask = np.asarray(Image.open('work/img3.png'))[..., :2].max(-1) > 20
d = np.load('work/mesh_in.npz'); uv = d['wuv'].reshape(-1, 3, 2); cz = d['verts'][d['faces']].mean(1)[:, 2]
head = uv.mean(1)[:, 0] > .505
def raster(sel):
    m = Image.new('L', (W, H)); dr = ImageDraw.Draw(m)
    for t in uv[sel]: dr.polygon([(u * W, (1 - v) * H) for u, v in t], fill=255)
    return np.asarray(m) > 0
body_px = raster(~head & (cz > 1.15) & (cz < 1.5)) & ~mask
hue = lambda L: np.degrees(np.arctan2(L[..., 2], L[..., 1]))
skinlike = (np.hypot(lab[..., 1], lab[..., 2]) > 15) & (hue(lab) > 48) & (hue(lab) < 76) & (lab[..., 0] > 28) & (lab[..., 0] < 62)
bs = lab[body_px & skinlike]
head_px = raster(head); head_px[:, :X0] = False
hl = lab[head_px & skinlike]; med = np.median(hl, 0)  # the head set also holds hair islands
dist = np.linalg.norm((lab - med) / [14, 6, 7], axis=-1)
w = np.exp(-np.maximum(dist - 1, 0) ** 2) * head_px
w = np.asarray(Image.fromarray((w * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
w[:, :X0] = 0
hs = lab[head_px & (w > .8)]
mh, sh, mb, sb = hs.mean(0), hs.std(0), bs.mean(0), bs.std(0)
print('BODY skin Lab mean', mb.round(1), 'std', sb.round(1), 'n', len(bs))
print('HEAD skin Lab mean', mh.round(1), 'std', sh.round(1), 'n', len(hs))
LIFT = float(os.environ.get('REA_SKIN_LIFT', '6'))  # the vertical face under the hair gets less light than the chest
new = (lab - mh) * np.minimum(sb / sh, 1.15) + mb + [LIFT, 0, 0]  # keep the face's own shading contrast
out = lab * (1 - w[..., None]) + new * w[..., None]
res = np.clip(color.lab2rgb(out), 0, 1)
res[:, :X0] = rgb[:, :X0]
Image.fromarray((res * 255 + .5).astype(np.uint8)).save('work/basecolor_skinmatch.png')
print('HEAD after', color.rgb2lab(res)[head_px & (w > .8)].mean(0).round(1))
os.makedirs('review/skin', exist_ok=True)
a = img.crop((X0, 0, W, H)).resize((512, 512)); b = Image.fromarray((res * 255).astype(np.uint8)).crop((X0, 0, W, H)).resize((512, 512))
s = Image.new('RGB', (1536, 512)); s.paste(a, (0, 0)); s.paste(b, (512, 0))
s.paste(Image.fromarray((w[:, X0:] * 255).astype(np.uint8)).resize((512, 512)).convert('RGB'), (1024, 0))
s.save('review/skin/head_before_after.png')
