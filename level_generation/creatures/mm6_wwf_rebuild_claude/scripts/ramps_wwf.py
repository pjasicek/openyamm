#!/usr/bin/env python3
"""Werewolf copy (shorts = warm native pixels, gem = the rest; palettes 831/832/833) of: Tier ramps for the rebuilt lizardman (method of ../mm8_lizardman_peasant_tiers_claude/scripts/tier_ramps.py):
garment and trim regions; A = least-squares fit to the graded base (A looks as painted); B (Farmer, 402) and C
(Villager, 403): native pixels that change between the palettes, split into garment/trim by their 401 colour, sorted
by 401 luminance; stop k = the tier's mean colour at the region texels' luminance quantile of stop k, scaled to A's
stop luminance. Writes textures/wwf_ramps.json (region_variants.py config)."""
import glob, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
W = np.array([0.2126, 0.7152, 0.0722]); PROD = HERE.parent / 'mm6_wfigt1'
TIERS = {'wwf_b': '832', 'wwf_c': '833'}
RANK_GAIN = 1.25          # sprite pixels carry painted shading; the albedo is this much brighter
base = np.asarray(Image.open(HERE / 'textures/wwf_basecolor.png').convert('RGB'), np.float64) / 255
gw, tw = np.load(HERE / 'work/region_weights.npy').astype(np.float64)
ramps = {'wwf_a': []}; report = {}
for name, w in (('shorts', gw), ('gem', tw)):
    r, rep = R.fit_ramps(base, {'wwf_a': base}, w); ramps['wwf_a'].append(r['wwf_a']); report[f'{name}_fit_a'] = rep
A, T = [], {t: [] for t in TIERS}
for f in sorted(glob.glob(str(PROD / 'native_variants/*_831.png'))):
    a = np.asarray(Image.open(f).convert('RGBA')).reshape(-1, 4).astype(int)
    tiers = {t: np.asarray(Image.open(f.replace('_831', f'_{p}')).convert('RGBA')).reshape(-1, 4).astype(int) for t, p in TIERS.items()}
    changed = (a[:, 3] > 0) & np.any([np.abs(a[:, :3] - x[:, :3]).max(1) > 6 for x in tiers.values()], 0)
    A.append(a[changed, :3]); [T[t].append(tiers[t][changed, :3]) for t in TIERS]
A = R.srgb_to_linear(np.concatenate(A) / 255); T = {t: R.srgb_to_linear(np.concatenate(v) / 255) for t, v in T.items()}
nat_warm = ~((A[:, 2] > A[:, 0] * 1.3) & (A[:, 1] > A[:, 0] * 1.2))   # werewolf: everything but the cyan gem is the shorts
lum = R.luminance(base)
for t in TIERS: ramps[t] = []
T['wwf_a'] = A; TIERS['wwf_a'] = '831'; ramps['wwf_a_fit'] = ramps['wwf_a']; ramps['wwf_a'] = []
for region, (weight, sel) in enumerate(((gw, nat_warm), (tw, ~nat_warm))):   # shorts warm, gem cyan
    ramp_a = ramps['wwf_a_fit'][region]; lo, hi = ramp_a['range']; stops_a = np.array(ramp_a['colors'])
    tex = np.sort(lum[weight > 0.9]); nat_l = A[sel] @ W; order = np.argsort(nat_l); n = len(order); half = max(50, n // 60)
    for t in TIERS:
        cols = []
        for k in range(16):
            q = np.searchsorted(tex, lo + (hi - lo) * k / 15) / len(tex)
            i = int(np.clip(q, 0.005, 0.995) * n); wsel = order[max(0, i - half):i + half]
            nat_a, nat_t = A[sel][wsel].mean(0), T[t][sel][wsel].mean(0)
            if region == 0:
                cols.append(np.clip(nat_t * RANK_GAIN, 0, 1))     # shorts: by luminance rank (user review of the 2026-10 model: the paint's bright tan must not survive)
            else:
                cols.append(np.clip(nat_t * (stops_a[k] @ W) / max(nat_a @ W, 1e-4), 0, 1))
        ramps[t].append(ramp_a if (t == 'wwf_a' and region == 1) else {'range': [lo, hi], 'colors': np.round(cols, 6).tolist()})
    report[f'region{region}_native_pixels'] = int(sel.sum())
ramps.pop('wwf_a_fit')
cfg = {'variants': ['wwf_a', 'wwf_b', 'wwf_c'], 'materials': [{'base': 'WwfBase', 'prefix': 'Werewolf', 'mask': 'wwf_region_mask.png',
       'regions': ['shorts', 'gem'], 'palettes': {'wwf_a': 831, 'wwf_b': 832, 'wwf_c': 833}, 'ramps': ramps}], 'report': report}
(HERE / 'textures/wwf_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
print('RAMPS', json.dumps(report))
