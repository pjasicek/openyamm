#!/usr/bin/env python3
"""One tier (Lich King, LICHKING1) on the one shared paint, by region mask + ramps (the shared-set rule; a later tier or a tone change is
a ramp, not a new image). Regions from the graded paint: R cloth (dark navy coat and lining: blue hue, low value), G armour (everything else:
knotwork, black plates, rims, medallions, bracers), B gems (saturated red and turquoise). Ramps are fitted to TARGET = the paint with
the tone moves in TONE (compared with MM9 by eye in the viewer). Writes textures/lk_mask.png, textures/lk_ramps.json. Project folder."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '../claude_shared')
import region_variants as RV
T = Path('textures')
base = np.asarray(Image.open(T / 'lk_raw_graded.png').convert('RGB'), np.float32) / 255
cov = np.asarray(Image.open(T / 'lk_cov.png').convert('L').resize(base.shape[1::-1], Image.NEAREST)) > 0
mx, mn = base.max(2), base.min(2); s = (mx - mn) / np.maximum(mx, 1e-4); r, g, b = base[..., 0], base[..., 1], base[..., 2]
h = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
cloth = cov & (h > 195) & (h < 260) & (s > 0.25) & (mx < 0.45)
gems = cov & (s > 0.45) & (mx > 0.55) & ~cloth              # r5: bright stones only; the teal plate undersides go with the armour
silver = cov & ~cloth & ~gems                      # r2: all the armour (knotwork, black plates, rims), not only its bright texels
sm = lambda m: np.clip(ndimage.gaussian_filter(m.astype(np.float32), 1.2), 0, 1)
W = [sm(cloth), sm(silver), sm(gems)]
# tone moves towards MM9 (the skin is a navy-black coat, blue-steel silver): saturation and value per region
TONE = {'cloth': dict(sat=1.1, val=1.12), 'silver': dict(sat=1.0, val=0.62, tint=[0.88, 0.97, 1.12]), 'gems': dict(sat=1.1, val=1.0)}
TEAL = True      # r2: our silver read white next to MM9's dark blue-steel
def toned(img, t):
    L = img.mean(2, keepdims=True); out = L + (img - L) * t.get('sat', 1.0)
    out = out * t.get('val', 1.0) * np.array(t.get('tint', [1, 1, 1])); return np.clip(out, 0, 1)
mats = []; ramps = {}
for (nm, t), w in zip(TONE.items(), W):
    rp, rep = RV.fit_ramps(base, {'lichking': toned(base, t)}, w)
    ramps.setdefault('lichking', []).append(rp['lichking']); print('REGION', nm, int((w > 0.9).sum()), rep)
RV.write_mask(W, T / 'lk_mask.png', 1024)
# r9: the staff's skull, MM9's yellow-green bone (LICHSTAFF.dtx) on the shared head paint: one region (a white mask), one ramp
hb = np.asarray(Image.open(T / 'lk_head_base.png').convert('RGB'), np.float32) / 255
L_ = hb.mean(2, keepdims=True); tint = np.clip(np.power(L_, 0.95) * np.array([0.93, 0.97, 0.58]) * 1.05, 0, 1)
rs, rep_s = RV.fit_ramps(hb, {'lichking': tint}, np.ones(hb.shape[:2], np.float32)); print('REGION staff skull', rep_s)
RV.write_mask([np.ones((64, 64), np.float32)], T / 'lk_staffskull_mask.png', 64)
json.dump({'variants': ['lichking'], 'materials': [{'base': 'LichKing', 'prefix': 'LichKing', 'mask': 'lk_mask.png', 'ramps': ramps},
           {'base': 'LichKingStaffSkull', 'prefix': 'LichKingStaffSkull', 'mask': 'lk_staffskull_mask.png', 'ramps': {'lichking': [rs['lichking']]}}]}, open(T / 'lk_ramps.json', 'w'), indent=1)
print('TONE written')
