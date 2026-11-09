#!/usr/bin/env python3
"""Tier region masks and ramps for one PeasantHOF design (CLAUDE_CREATURE_TEXTURES.md: one shared set per design,
region mask + ramps per tier). The design's shared paint is its placed skin (tier A of the GLB); the other MM9 skin of
the same model is a recolour of it in the regions below.

Regions are picked on OUR graded paint by colour and height rules per design (DESIGNS). The tier targets come from
MM9's own two skins of the model: every texel of a region is matched to the nearest point of MM9's bind mesh (the
raw conversion, same frame as our unmirrored export, floors aligned), whose UV gives the MM9 skin texel; MM9 A and B
share the UV layout, so the region's MM9 A and MM9 B colours are known texel for texel. Target per tier = the tier's
MM9 colour at the texel's luminance quantile inside the region (quantile matching, as tiers_pdm2.py) times the gain that
maps MM9's shared-skin region onto our paint (median linear luminance); the shared skin's own tier reproduces our paint.
Head set regions (hair, hood) work the same way on the head material. Ramps fitted with region_variants.fit_ramps.
Writes textures/<d>_region_mask.png (+ _head), textures/<d>_ramps.json, textures/<d>_tier_preview_<v>.png and
review/tier_masks_<d>.png. Usage (project folder): tiers_phof.py <design a> <export glb>"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
from pygltflib import GLTF2
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV
from headpart import texel_parts

W = np.array([0.2126, 0.7152, 0.0722])
N = 1024


def hsv(I):
    mx, mn = I.max(-1), I.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
    r, g, b = I[..., 0], I[..., 1], I[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    return hue, sat, mx


# design: shared skin (tier A of the GLB), other skins, regions {material: [(name, rule(h, s, v, y, part))]}
# rules take hue (deg), saturation, value (0..1 sRGB max), rest height y (m, floor 0), loose part (head set only)
XPOS = [None]                       # texel x (m) for position rules, set per material in build()
DESIGNS = {
    # HOF1: skin a (rows 61, 62) is the shared paint; skin b (row 63) recolours the bodice and the skirt (MM9 B: brown
    # patterned bodice, near-black skirt); B's head is its own image (tier_head.py), so no head regions
    'a': dict(model='phof1', shared='a', tiers=['a', 'b'],
              body=[('bodice', lambda h, s, v, y, p: (h > 165) & (h < 230) & (s > 0.22) & (y > 1.05)),
                    ('skirt', lambda h, s, v, y, p: (h > 5) & (h < 50) & (s > 0.2) & (v < 0.42) & (y > 0.44) & (y < 1.17)),
                    # body skin (neck, chest, forearms, knees) to each tier's own face tone: tier B's head is another woman
                    # with warmer, more yellow skin (neck bands A 195/137/114, B 191/126/91 in the composed head sets)
                    ('skin', lambda h, s, v, y, p: (h > 6) & (h < 32) & (s > 0.26) & (s < 0.62) & (v > 0.55) & ((y > 1.45) | ((np.abs(XPOS[0]) > 0.36) & (y > 1.05))),
                     {'b': [208 / 230, 138 / 146, 102 / 113]})],   # B's neck reference over A's body skin median after skin_warm.py --body-auto (a2 head)
              head=[]),
    # HOF2 (row 64): one tier, its own paint; the dress region (its ramp reproduces the paint) keeps one named variant
    # (phof2_c) for the binding's skin and leaves room for a mod recolour
    'c': dict(model='phof2', shared='c', tiers=['c'],
              body=[('dress', lambda h, s, v, y, p: (h > 5) & (h < 45) & (s > 0.25) & (v < 0.45) & (y > 0.05) & (y < 1.55))],
              head=[]),
}
d = sys.argv[1]; GLB = sys.argv[2]
D = DESIGNS[d]
pre = f'phof{d}_tp'


def mm9_surface(model, tier):
    """Dense samples of MM9's bind mesh: positions (floor at 0) and skin texel colours (sRGB 0..1)."""
    g = GLTF2().load(f'source/mm9/{model}{tier}.glb'); blob = g.binary_blob()

    def acc(i):
        a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
        n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
        dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
        return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
    P, UV, T = [], [], []
    off = 0
    for m in g.meshes:
        for pr in m.primitives:
            p = acc(pr.attributes.POSITION).astype(float); uv = acc(pr.attributes.TEXCOORD_0).astype(float)
            t = acc(pr.indices).reshape(-1, 3).astype(int)
            P.append(p); UV.append(uv); T.append(t + off); off += len(p)
    P, UV, T = np.concatenate(P), np.concatenate(UV), np.concatenate(T)
    # the converted MM9 scene is y-up with the root at the origin; samples, 30 per triangle (bounded: ~600 triangles)
    rng = np.random.default_rng(1)
    a = rng.random((len(T), 30, 2)); flip = a.sum(-1) > 1; a[flip] = 1 - a[flip]
    w = np.stack([1 - a[..., 0] - a[..., 1], a[..., 0], a[..., 1]], -1)
    sp = np.einsum('tsk,tkd->tsd', w, P[T]).reshape(-1, 3); su = np.einsum('tsk,tkd->tsd', w, UV[T]).reshape(-1, 2)
    sp[:, 1] -= P[:, 1].min()
    return sp, su


def skin_img(model, tier):
    return np.asarray(Image.open(f'source/mm9/skins/{model}{tier}.png').convert('RGB'), float) / 255


SP, SU = mm9_surface(D['model'], D['shared'])
tree = cKDTree(SP)
SK = {t: skin_img(D['model'], t) for t in D['tiers']}


def mm9_colours(pos):
    _, i = tree.query(pos, 1)
    uv = SU[i] % 1.0
    h, w = SK[D['shared']].shape[:2]
    xs = np.clip((uv[:, 0] * w).astype(int), 0, w - 1); ys = np.clip((uv[:, 1] * h).astype(int), 0, h - 1)
    return {t: SK[t][ys, xs] for t in D['tiers']}


def build(material, base_png, regions, mask_png, size, kind='body'):
    base = np.asarray(Image.open(base_png).convert('RGB').resize((size, size), Image.LANCZOS), float) / 255
    pos, part, _ = texel_parts(GLB, material, size)
    cov = part >= 0
    P = np.nan_to_num(pos)
    h, s, v = hsv(base)
    lin = RV.srgb_to_linear(base); lum = lin @ W
    masks = []
    XPOS[0] = P[..., 0]
    for reg in regions:
        name, rule = reg[0], reg[1]
        m = cov & rule(h, s, v, P[..., 1], part)
        m = ndimage.binary_opening(ndimage.binary_closing(m, iterations=2), iterations=1) & cov
        masks.append(m)
    WS = []
    for m in masks:
        w = ndimage.gaussian_filter(m.astype(float), 0.8) * cov
        _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
        WS.append(w[iy, ix])
    tot = np.maximum(sum(WS), 1.0) if WS else 1.0
    WS = [w / tot for w in WS]
    RV.write_mask(WS, Path('textures') / mask_png, size=size)
    ramps = {f'{D["model"]}_{t}': [] for t in D['tiers']}
    rep = {}
    for reg, w in zip(regions, WS):
        name = reg[0]; sgain = reg[2] if len(reg) > 2 else None
        core = w > 0.9
        mm = mm9_colours(P[core])
        la = RV.srgb_to_linear(mm[D['shared']])
        gain = np.median(lum[core]) / max(np.median(la @ W), 1e-4)
        if kind in D.get('match_shared', []):
            gain = 1.3          # recoloured to MM9's own colours: its texels carry baked shading (albedo ~1.3x, textures doc)
        q = np.argsort(np.argsort(lum[core])) / max(core.sum() - 1, 1)
        targets = {}
        for t in D['tiers']:
            if t == D['shared'] and kind not in D.get('match_shared', []):
                targets[f'{D["model"]}_{t}'] = base
                continue
            if sgain is not None:           # per-channel sRGB gain on our own paint (not MM9's skin)
                targets[f'{D["model"]}_{t}'] = np.clip(base * np.array(sgain.get(t, [1, 1, 1])), 0, 1)
                continue
            lb = RV.srgb_to_linear(mm[t]); order = np.argsort(lb @ W)
            idx = np.clip((q * (len(order) - 1)).astype(int), 0, len(order) - 1)
            tl = lin.copy(); tl[core] = np.clip(lb[order[idx]] * gain, 0, 1)
            targets[f'{D["model"]}_{t}'] = np.where(tl <= 0.0031308, tl * 12.92, 1.055 * np.power(tl, 1 / 2.4) - 0.055)
        fit, err = RV.fit_ramps(base, targets, w)
        for k in ramps:
            ramps[k].append(fit[k])
        rep[name] = {'texels': int(core.sum()), 'gain_mm9_to_ours': round(float(gain), 3), 'fit_8bit': err,
                     'mm9_median': {t: (np.median(mm[t], 0) * 255).round().tolist() for t in D['tiers']}}
    return WS, ramps, rep, lin, lum


mats = []
report = {}
previews = {}
for kind, material, base_png, size in (('body', 'PeasantHOF', f'textures/{pre}_basecolor_graded.png', N),
                                       ('head', 'PeasantHOFHead', f'textures/{pre}_head_basecolor.png', N)):
    if not D[kind]:
        continue
    mask_png = f'{d}_region_mask{"_head" if kind == "head" else ""}.png'
    WS, ramps, rep, lin, lum = build(material, base_png, D[kind], mask_png, size, kind)
    mats.append({'base': material, 'prefix': material, 'mask': mask_png, 'ramps': ramps})
    report[kind] = rep
    previews[kind] = (WS, ramps, lin, lum)
doc = {'variants': [f'{D["model"]}_{t}' for t in D['tiers']], 'materials': mats,
       'regions': {k: [r[0] for r in D[k]] for k in ('body', 'head')},
       'source': f'MM9 {D["model"].upper()} skins {D["tiers"]} (shared paint: {D["shared"]}); scripts/tiers_phof.py', 'report': report}
json.dump(doc, open(f'textures/{d}_ramps.json', 'w'), indent=1)
for kind, (WS, ramps, lin, lum) in previews.items():
    for v, rl in ramps.items():
        out = lin.copy()
        for k, w in enumerate(WS):
            lo, hi = rl[k]['range']
            tt = np.clip((lum - lo) / (hi - lo), 0, 1) * 15
            i0 = np.floor(tt).astype(int).clip(0, 15); i1 = (i0 + 1).clip(0, 15); f = (tt - i0)[..., None]
            C = np.array(rl[k]['colors']); col = C[i0] * (1 - f) + C[i1] * f
            out = out * (1 - w[..., None]) + col * w[..., None]
        sr = np.where(out <= 0.0031308, out * 12.92, 1.055 * np.power(np.clip(out, 0, 1), 1 / 2.4) - 0.055)
        Image.fromarray(np.uint8(np.clip(sr, 0, 1) * 255)).save(f'textures/{d}_tier_preview_{kind}_{v}.png')
    dbg = np.zeros(lin.shape)
    for k, w in enumerate(WS[:3]):
        dbg[..., k] = w
    Image.fromarray(np.uint8(np.clip(dbg, 0, 1) * 255)).save(f'review/tier_masks_{d}_{kind}.png')
print('TIERS', d, json.dumps({k: {n: {'texels': r['texels'], 'fit': r['fit_8bit'], 'mm9': r['mm9_median']} for n, r in v.items()} for k, v in report.items()}))
