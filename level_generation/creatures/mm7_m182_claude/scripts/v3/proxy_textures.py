"""Proxy colour maps for the v3 render-guided HD masters (system Python): what the v3 model looks like in tier A
before the retexture, from existing paint only.
- body: the installed cdr1 body base colour, its hide / belly regions recoloured with the v2 MM7 tier-A ramps
  (scales, ventral gold) by luminance within each region (2nd-98th percentile; hide t^1.8, so the scales sit in the dark greens of the
  ramp like the native hide), ivory kept;
- head: the v2 head base colour through its own region mask and v2 tier-A ramps (the v2 viewer look);
- wings: the cdr1 wing base colour with the v2 scales ramp darkened to 0.7 (dark green bones; the membrane is
  painted procedurally in the proxy scene).
Out: work/v3/proxy/{body,head,wings}_proxy.png"""
import json
import numpy as np
from pathlib import Path
from PIL import Image
P = Path(__file__).resolve().parents[2]; T = P / 'textures'; C = P / 'work/v3/cdr1_tex'; O = P / 'work/v3/proxy'
lin = lambda c: np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= .0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - .055)
Wl = np.array([.2126, .7152, .0722])
cfg = json.loads((T / 'dragon_ramps.json').read_text()); ramps = cfg['materials'][0]['ramps']['m182_a']
def ramp(colors, t):
    c = np.array(colors); x = np.clip(t, 0, 1) * (len(c) - 1); i = np.minimum(x.astype(int), len(c) - 2); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f
def load(p, mode='RGB'): return np.asarray(Image.open(p).convert(mode), float) / 255
def recolour(base, masks_regions, gain=1.0, gamma=(1.8, 1.0)):
    b = lin(base); lum = b @ Wl; out = b.copy()
    for k, (m, reg) in enumerate(masks_regions):
        sel = m > .5
        if not sel.any(): continue
        lo, hi = np.percentile(lum[sel], [2, 98]); t = np.clip((lum - lo) / max(hi - lo, 1e-6), 0, 1) ** gamma[k]
        out = out * (1 - m[..., None]) + ramp(reg['colors'], t) * gain * m[..., None]
    return srgb(out)
base = load(C / 'cdr1r_body_basecolor_2k.png'); mask = load(C / 'cdr1r_body_region_mask.png', 'RGBA')
Image.fromarray(np.uint8(np.clip(recolour(base, [(mask[..., 0], ramps[0]), (mask[..., 1], ramps[2])]), 0, 1) * 255)).save(O / 'body_proxy.png')
wb = load(C / 'cdr1_wings_basecolor_2k.png'); wm = load(C / 'cdr1_wings_region_mask.png', 'RGBA')
Image.fromarray(np.uint8(np.clip(recolour(wb, [(wm[..., 0], ramps[0]), (wm[..., 1], ramps[2])], gain=.7), 0, 1) * 255)).save(O / 'wings_proxy.png')
hb = lin(load(T / 'dragon_head_basecolor_2k.png')); hm = load(T / 'dragon_head_region_mask.png', 'RGBA'); lum = hb @ Wl; out = hb.copy()
for c, reg in enumerate(ramps):
    lo, hi = reg['range']; out = out * (1 - hm[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * hm[..., c:c + 1]
Image.fromarray(np.uint8(np.clip(srgb(out), 0, 1) * 255)).save(O / 'head_proxy.png')
print('PROXY maps written')
