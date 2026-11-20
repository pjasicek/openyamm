"""Compose the male peasant's 1K body and head maps from the two new Meshy returns (user 2026-10-13: regenerate head and
body textures; the head must not fight the body skin). Adapted from ../mm6_pman_claude_20261013/scripts/
compose_textures.py: same tunic region (green cloth of piece 0), AO, normal strength, roughness/specular classes and
native palette fits (798 -> 799/800). The returns are in the master's own UVs, so there is no reprojection, and the
old return's position-based clean-ups do not apply.
Skin match: the face/neck skin (piece 1) and the forearm/hand skin (pieces 4, 5) both take a per-channel linear gain
to their common geometric-mean skin colour (the returns disagreed: pale peach arms, tanned face); measured on
mid-luminance skin texels (eyes, brows, lips and shadow excluded).
Out: textures/pman_{body,head}_{basecolor,normal,metal_rough}_1k.png, _region_mask.png, pman_ramps.json,
composition.json."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

P = Path(__file__).resolve().parents[1]; T = P / 'textures'; T.mkdir(exist_ok=True); N = 1024
ROOT = P.parents[2]
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
sys.path.insert(0, str(ROOT / 'tools')); import normal_map_convention as NC  # noqa: E402
lin = R.srgb_to_linear


def to_srgb(c):
    return np.where(c <= .0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - .055)


def load(path, mode='RGB'):
    return np.asarray(Image.open(path).convert(mode).resize((N, N), Image.Resampling.LANCZOS), float) / 255


def save(a, path):
    Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + .5)).save(path)


W = np.array([.2126, .7152, .0722])
# body maps come re-packed (tex_relayout.py, tex_resample.py, tex_sample.py: arms x2.6 linear)
raw = {'body': P / 'texturing' / 'body_relayout', 'head': P / 'meshy' / 'head_texture_r45'}
rast = {part: dict(np.load(P / 'work' / f'uvraster_{layer}.npz')) for part, layer in (('body', 'UVMap'), ('head', 'HeadUV'))}
bases = {part: load(raw[part] / 'texture_urls_0_base_color.png') for part in raw}
from scipy.spatial import cKDTree  # noqa: E402
# Review fix (arms): the new body return smudged band brown under the cuffs and gave the arms 1/10 of the installed
# texels; the arms take the installed model's albedo (3D lookup, tex_resample.py), colour-matched below.
arm_ok = load(P / 'texturing' / 'arms_mask.png', 'L') > .99
arm_img = load(P / 'texturing' / 'arms_installed_basecolor.png')
arm_img = arm_img[tuple(ndimage.distance_transform_edt(~arm_ok, return_distances=False, return_indices=True))]
# every covered arm texel (the chart borders too: left to the Meshy skin they drew light seam lines)
arms = rast['body']['coverage'] & np.isin(rast['body']['piece'], [4, 5])
bases['body'][arms] = arm_img[arms]
report_fix = {'arm_texels_from_installed': int(arms.sum())}


def skin_texels(part, pieces):
    d = rast[part]; m = d['coverage'] & np.isin(d['piece'], pieces)
    c = lin(bases[part][m]); lum = c @ W
    lo, hi = np.percentile(lum, [30, 85]); keep = (lum > lo) & (lum < hi)
    return m, c[keep]


body_mask, body_skin = skin_texels('body', [4, 5])
head_mask, head_skin = skin_texels('head', [1])
body_med, head_med = np.median(body_skin, 0), np.median(head_skin, 0)
# The two returns disagree (pale peach arms, tanned face): both meet at their per-channel geometric mean.
target = np.sqrt(body_med * head_med)
gains = {'body': np.clip(target / np.maximum(body_med, 1e-4), .7, 1.45),
         'head': np.clip(target / np.maximum(head_med, 1e-4), .7, 1.45)}
for part, m in (('body', body_mask), ('head', head_mask)):
    c = lin(bases[part]); c[m] *= gains[part]; bases[part] = to_srgb(np.clip(c, 0, 1))
after = {part: np.median(skin_texels(part, pieces)[1], 0).round(4).tolist() for part, pieces in (('body', [4, 5]), ('head', [1]))}
seam = {'body_skin_linear_before': body_med.round(4).tolist(), 'head_skin_linear_before': head_med.round(4).tolist(),
        'target_linear': target.round(4).tolist(), 'gains': {k: v.round(3).tolist() for k, v in gains.items()},
        'after': after}

# Skin guard (review: band/tunic colour on the skin where it meets cloth): skin texels of the arms/hands that are far
# darker than the matched skin or tunic-green take the mean of their 8 nearest clean skin texels (3D)
for part, pieces in (('body', [4, 5]), ('head', [1])):
    d = rast[part]; c = bases[part]; l = lin(c) @ W; sk = d['coverage'] & np.isin(d['piece'], pieces)
    med = np.median(l[sk]); greenish = (c[..., 1] > c[..., 0] * 1.02)
    bad = sk & ((l < .45 * med) | greenish)
    if part == 'body':   # above the wrists (no finger creases) a milder darkening is band colour too
        bad |= sk & (l < .65 * med) & (d['pos'][..., 2] > 1.0)
    if part == 'head':   # lips, brows, eyes, stubble live on the face: only the neck below the jaw is guarded
        bad &= d['pos'][..., 2] < np.percentile(d['pos'][sk][:, 2], 22)
    good = sk & ~bad & (l > .6 * med)
    if bad.any():
        _, idx = cKDTree(d['pos'][good]).query(d['pos'][bad], k=8); c[bad] = c[good][idx].mean(1)
    report_fix[f'skin_guard_{part}'] = int(bad.sum())

# Tunic repair: Meshy painted skin on the collar rim and the leggings' cream on the hem. Bright non-green texels of the
# tunic (the leather arm bands are dark and stay) take the mean of their 8 nearest green tunic texels in 3D.
from scipy.spatial import cKDTree  # noqa: E402
d = rast['body']; tb = bases['body']; tl = tb @ W
tunic = d['coverage'] & (d['piece'] == 0)
tgreen = (tb[..., 1] > tb[..., 0] * 1.06) & (tb[..., 1] > tb[..., 2] * 1.09)
bad = tunic & ~tgreen & (tl > .42); good = tunic & tgreen
_, idx = cKDTree(d['pos'][good]).query(d['pos'][bad], k=8)
tb[bad] = tb[good][idx].mean(1); bases['body'] = tb
tunic_fixed = int(bad.sum())

# Hairline (review: a painted hairline on the skin that does not line up with the hair mesh, a pale gap and a step at
# the mesh edge). Skin under the hair mesh (tex_hairmask.py) takes the nearby hair colour with darker roots; a 4 mm band
# outside the mesh edge blends into it.
h = rast['head']; hc = np.load(P / 'work' / 'hair_cover.npz'); covered, dist = hc['covered'], hc['distance']
c = bases['head']; skin = h['coverage'] & (h['piece'] == 1); hairtex = h['coverage'] & (h['piece'] == 2)
l = lin(c) @ W; med = np.median(l[skin & ~covered & (dist > .02)])
_, idx = cKDTree(h['pos'][hairtex]).query(h['pos'][skin], k=6); root = c[hairtex][idx].mean(1) * .78
w = np.where(covered[skin], 1.0, np.clip(1 - dist[skin] / .004, 0, 1) * .85)
c[skin] = c[skin] * (1 - w[:, None]) + root * w[:, None]
bases['head'] = c   # painted hair beyond the band (temples, sideburns, nape) stays: erasing it cut a hard light curve
report_fix.update(hair_painted=int((w > 0).sum()), hair_covered=int(covered[skin].sum()))
sets = {}; report = {'skin_match': seam, 'tunic_repaired_texels': tunic_fixed, 'review_fixes': report_fix}
for part in ('body', 'head'):
    d = rast[part]; coverage = d['coverage']; piece = d['piece']; base = bases[part]
    green = (base[..., 1] > base[..., 0] * 1.06) & (base[..., 1] > base[..., 2] * 1.09)
    # the whole tunic follows the tier except its dark brown leather bands (a green test missed dark/olive texels at the
    # collar, which stayed green on the B/C tiers)
    brown = (base[..., 0] > base[..., 1] * 1.08) & (base @ W < .45)
    region = (piece == 0) & ~brown & coverage if part == 'body' else np.zeros_like(coverage)
    # leather belts/cuffs and the brass buckle keep their colour; fill tiny cloth colour/shadow gaps only
    region = ndimage.binary_closing(region, iterations=2) & (piece == 0) & coverage
    nearest = ndimage.distance_transform_edt(~coverage, return_distances=False, return_indices=True)
    ao = load(P / 'work' / f'ao_{part}.png', 'L')
    if part == 'body':   # the installed arm albedo already carries its AO: a second AO left light lines at the seams
        ao[arms] = 1.0
    base = base * (1 - .18 * (1 - np.maximum(ao, .4)))[..., None]
    base = base[tuple(nearest)]; mask = region[tuple(nearest)].astype(float)
    save(base, T / f'pman_{part}_basecolor_1k.png'); R.write_mask([mask], T / f'pman_{part}_region_mask.png', N)
    normal = np.uint8(load(raw[part] / 'texture_urls_0_normal.png') * 255 + .5); correlation = NC.measure(normal)
    if correlation <= -.15:
        normal[..., 1] = 255 - normal[..., 1]
    strength = .4 if part == 'head' else .7
    normal = np.uint8(np.clip((normal.astype(float) - np.array([127.5, 127.5, 255])) * strength
                              + np.array([127.5, 127.5, 255]), 0, 255))
    if part == 'body':   # the arm skin is the installed albedo: the resampled low-density Meshy normal streaked it
        normal[arms] = [128, 128, 255]
    Image.fromarray(normal[tuple(nearest)]).save(T / f'pman_{part}_normal_1k.png')
    rough = load(raw[part] / 'texture_urls_0_roughness.png', 'L'); detail = .12 * (rough - np.median(rough[coverage]))
    if part == 'body':   # the resampled Meshy roughness jumps at its old chart borders (lines on the installed arm skin)
        detail[arms] = 0
    rr = np.full((N, N), .88); spec = np.full((N, N), .12); metal = np.zeros((N, N))
    skin = np.isin(piece, [1, 4, 5]); hair = piece == 2
    leather = np.isin(piece, [6, 7]) | ((piece == 0) & brown); brass = np.isin(piece, [10, 11])
    rr[skin] = .76; rr[hair] = .8; rr[leather] = .64; rr[brass] = .36
    spec[hair] = .16; spec[leather] = .3; spec[brass] = .85; metal[brass] = .85
    orm = np.stack([spec, np.clip(rr + detail, .3, .96), metal], axis=-1)[tuple(nearest)]
    save(orm, T / f'pman_{part}_metal_rough_1k.png')
    sets[part] = (base, mask, coverage)
    report[part] = {'region_texels': int(region.sum()), 'normal_correlation': correlation,
                    'normal_green_flipped': correlation <= -.15, 'coverage': round(float(coverage.mean()), 3)}

PAL = P.parent / 'new_sorpigal_3d_stage1_20261006/pman/source/palettes'


def palette(pid):
    return np.frombuffer((PAL / f'pal{pid}.act').read_bytes()[:768], np.uint8).reshape(256, 3) / 255


base = sets['body'][0]; weight = sets['body'][1] * sets['body'][2]; src = palette(798); tiers = {'pman_a': base}; fits = {}
for tier, pid in [('pman_b', 799), ('pman_c', 800)]:
    dst = palette(pid); changed = np.abs(src - dst).sum(1) > .02
    M, *_ = np.linalg.lstsq(np.c_[src[changed], np.ones(changed.sum())], dst[changed], rcond=None)
    tiers[tier] = np.clip(np.c_[base.reshape(-1, 3), np.ones(N * N)] @ M, 0, 1).reshape(N, N, 3)
    fits[tier] = {'palette': pid, 'samples': int(changed.sum())}
ramps, fit = R.fit_ramps(base, tiers, weight); cfg = {'variants': ['pman_a', 'pman_b', 'pman_c'], 'materials': []}
for part, name in [('body', 'Peasant_A'), ('head', 'PeasantHead_A')]:
    cfg['materials'].append({'base': name, 'prefix': name[:-2], 'mask': f'pman_{part}_region_mask.png', 'regions': ['tunic'],
                             'palettes': {'pman_a': 798, 'pman_b': 799, 'pman_c': 800},
                             'ramps': {k: [ramps[k]] for k in cfg['variants']}})
(T / 'pman_ramps.json').write_text(json.dumps(cfg, indent=2))
report['native_palette_fits'] = fits; report['ramp_fit'] = fit
(T / 'composition.json').write_text(json.dumps(report, indent=2, default=str)); print('COMPOSE', json.dumps(report, default=str)[:900])
