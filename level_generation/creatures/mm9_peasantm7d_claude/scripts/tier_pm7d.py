#!/usr/bin/env python3
"""(tier_pm7d.py, from PeasantM7's tier_pm7.py; main() below is PeasantM7d's) Colour tiers of PeasantM7 as one shared skin + region mask + ramps (CLAUDE_CREATURE_TEXTURES.md).

The shared set is the tier B paint (MONSTERS.txt row 51, PEASANTM7B: olive tunic, slate-blue collar and hem band, dark
chestnut hair; 20 of the body's 24 placed objects). Tier A (row 53, PEASANTM7A: slate-blue tunic, gold collar and hem
band, auburn-ginger hair, redder breeches) is ramps on the same texels. Both MM9 skins share one UV layout, so each
region's colour change is measured on the same MM9 skin rectangles:
  body set   R tunic (olive -> slate blue), G collar yoke + placket + hem band (slate -> gold), B breeches
  head set   R hair
Region texels: hue/value classes of the graded paint, limited by height on the runtime GLB's bind pose (texel
positions rasterised from LOD0). Tier A target per texel = qA(t) x L(ours) / L(qB(t)) (linear RGB), t = the texel's luminance
quantile inside its region, q = the MM9 skin's luminance-sorted colour quantiles of that region; then
region_variants.fit_ramps fits both tiers' ramps (tier B reproduces the shared paint).
The face (a different man in skin A, smiling, green eyes) and the brocade pattern of A's collar are not ramps: both
tiers show the B face and plain cloth, coloured gold on A (README "Deviations").
Usage (project folder): tier_pm7.py <runtime glb> -> textures/pm7_region_mask.png, pm7_head_region_mask.png,
pm7_ramps.json, review/tiers_preview/*.png"""
import colorsys
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as R  # noqa: E402
from pygltflib import GLTF2  # noqa: E402

N = 1024
T = Path('textures')
OUT = Path('review/tiers_preview')
OUT.mkdir(parents=True, exist_ok=True)


def accessor(g, blob, i):
    a = g.accessors[i]
    bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a.type]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a.componentType]
    off = (bv.byteOffset or 0) + (a.byteOffset or 0)
    arr = np.frombuffer(blob, dtype=dt, count=a.count * n, offset=off).reshape(a.count, n)
    return arr


def raster_positions(glb, mesh_name='PeasantM7'):
    """Per material: NxN rest-pose position (glTF y up) of the texel centre, NaN outside the islands."""
    g = GLTF2().load(glb)
    blob = g.binary_blob()
    mesh = next(m for m in g.meshes if m.name == mesh_name)
    out = {}
    for p in mesh.primitives:
        P = accessor(g, blob, p.attributes.POSITION).astype(np.float64)
        UV = accessor(g, blob, p.attributes.TEXCOORD_0).astype(np.float64)
        I = accessor(g, blob, p.indices).reshape(-1, 3)
        img = np.full((N, N, 3), np.nan)
        for tri in I:
            uv = UV[tri] * N
            x0, y0 = np.floor(uv.min(0)).astype(int)
            x1, y1 = np.ceil(uv.max(0)).astype(int)
            xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
            if xs.size == 0:
                continue
            q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
            a, b, c = uv
            m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
            if abs(np.linalg.det(m)) < 1e-12:
                continue
            l = np.linalg.solve(m, (q - a).T).T
            w = np.column_stack([1 - l.sum(1), l])
            ok = (w >= -1e-4).all(1)
            if not ok.any():
                continue
            img[q[ok, 1].astype(int), q[ok, 0].astype(int)] = w[ok] @ P[tri]
        out[g.materials[p.material].name.split('_')[0]] = img
    return out


def hsv(img):
    f = img.reshape(-1, 3)
    mx, mn = f.max(1), f.min(1)
    v = mx
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    rc = np.where(mx - mn > 0, (mx - f[:, 0]) / np.maximum(mx - mn, 1e-6), 0)
    gc = np.where(mx - mn > 0, (mx - f[:, 1]) / np.maximum(mx - mn, 1e-6), 0)
    bc = np.where(mx - mn > 0, (mx - f[:, 2]) / np.maximum(mx - mn, 1e-6), 0)
    h = np.where(f[:, 0] == mx, bc - gc, np.where(f[:, 1] == mx, 2 + rc - bc, 4 + gc - rc))
    h = (h / 6.0) % 1.0 * 360
    sh = img.shape[:2]
    return h.reshape(sh), s.reshape(sh), v.reshape(sh)


def quantiles(pixels, k=33):
    lin = R.srgb_to_linear(pixels)
    lum = lin @ R.LUMA
    order = np.argsort(lum)
    lin = lin[order]
    idx = np.linspace(0, len(lin) - 1, k)
    # smooth: mean of a window around each quantile
    w = max(len(lin) // (k * 2), 1)
    return np.array([lin[max(int(i) - w, 0):int(i) + w + 1].mean(0) for i in idx])


def mm9_region(skin, rect, hue=None, vmax=None):
    x0, y0, x1, y1 = (np.array(rect) / 4).astype(int)   # rectangles measured on the 4x preview (1024 px)
    px = skin[y0:y1, x0:x1].reshape(-1, 3)
    if hue is not None or vmax is not None:
        h, s, v = hsv(skin[y0:y1, x0:x1])
        m = np.ones(h.shape, bool)
        if hue is not None:
            lo, hi = hue
            m &= ((h >= lo) & (h <= hi)) if lo < hi else ((h >= lo) | (h <= hi))
        if vmax is not None:
            m &= v <= vmax
        px = skin[y0:y1, x0:x1][m]
    return px


def tier_a_colour(qa, qb, i0, f, lum):
    """Tier A target (linear): MM9 skin A's colour at the texel's luminance quantile, scaled by our luminance over MM9
    skin B's at that quantile, so A keeps MM9's chroma and our paint's light/dark structure (a per-channel ratio on
    our colour kept our paint's hue mix and read grey, v1.2)."""
    ca = qa[i0] * (1 - f) + qa[i0 + 1] * f
    cb = qb[i0] * (1 - f) + qb[i0 + 1] * f
    lb = cb @ R.LUMA
    return ca * np.clip(lum / np.maximum(lb, 1e-4), 0.1, 10.0)[..., None]


def soften(m, src_cov):
    """Pad the mask into the gutters (nearest island texel), then feather 1.5 texels."""
    idx = ndi.distance_transform_edt(~src_cov, return_distances=False, return_indices=True)
    padded = m[idx[0], idx[1]]
    return ndi.gaussian_filter(padded.astype(np.float64), 1.2)



def shoulder_planes(glb):
    """Per side: (shoulder joint, unit arm direction) in glTF rest space, from the skin's inverse bind matrices."""
    g = GLTF2().load(glb)
    blob = g.binary_blob()
    skin = g.skins[0]
    ibm = accessor(g, blob, skin.inverseBindMatrices).reshape(-1, 4, 4)
    pos = {}
    for k, j in enumerate(skin.joints):
        m = np.linalg.inv(ibm[k].T)
        pos[g.nodes[j].name] = m[:3, 3]
    out = []
    for side in ('L', 'R'):
        sh, el = pos[f'Bip01 {side} UpperArm'], pos[f'Bip01 {side} Forearm']
        d = (el - sh) / np.linalg.norm(el - sh)
        out.append((sh, d))
    return out


def main():
    """tier_pm7d.py: PeasantM7d's body tiers on PeasantM7's shared paint (the PEASANTM7B paint, pm7_tp_basecolor_graded.png
    after sleeve_paint_fix.py, copied as pm7d_tp_basecolor_graded.png). Regions: R tunic body, G collar + placket + hem band,
    B breeches (PeasantM7's classes, tier_pm7.py), A sleeves (new: the tunic class beyond a plane 3 cm inside the shoulder
    joint, normal to the upper arm, within 11 cm of the arm's axis; M7 had one tunic region). Both tiers are ramps: D (row 25, PEASANTM7D: green speckled
    tunic and sleeves, gold collar) and C (row 27, PEASANTM7C: plum tunic, gold-ochre sleeves, gold collar and front braid),
    each = MM9 skin X's colour at the texel's luminance quantile inside the region x our luminance / MM9 skin B's at that
    quantile (tier_pm7.py's tier A rule). The head set is not ramped: each tier has its own head paint (tier_head.py).
    Usage (project folder): tier_pm7d.py <PeasantM7 runtime glb for the body texel positions> <mesh name>"""
    glb, mesh_name = sys.argv[1], sys.argv[2]
    pos = raster_positions(glb, mesh_name)
    skins = {t: np.asarray(Image.open(f'source/mm9/skins/{f}.png').convert('RGB'), np.float64) / 255
             for t, f in (('B', 'pm7b'), ('C', 'pm7d_C'), ('D', 'pm7d_D'))}
    regions_mm9 = {
        'tunic': ([190, 390, 550, 740], [40, 820, 560, 960]),
        'collar': ([60, 325, 570, 375], [0, 975, 560, 1024]),
        'breeches': ([590, 340, 770, 880],),
        'sleeves': ([700, 10, 990, 290],),
    }
    hues = {'tunic': {'B': (35, 110), 'C': (270, 359), 'D': (40, 170)},
            'collar': {'B': (180, 280), 'C': (15, 65), 'D': (15, 65)},
            'sleeves': {'B': (35, 110), 'C': (20, 70), 'D': (30, 170)}}
    q = {}
    for name, rects in regions_mm9.items():
        q[name] = {}
        for t, sk in skins.items():
            hue = hues.get(name, {}).get(t)
            px = np.concatenate([mm9_region(sk, r, hue) for r in rects])
            q[name][t] = quantiles(px)
            print('MM9', name, t, 'mean', (px.mean(0) * 255).round(), 'n', len(px))

    base = R.load_srgb(T / 'pm7d_tp_basecolor_graded.png', N)
    P = pos[mesh_name]
    cov = ~np.isnan(P[..., 0])
    y = np.nan_to_num(P[..., 1], nan=-1)
    h, s, v = hsv(base)
    slate = cov & (h > 175) & (h < 265) & (s > 0.06) & (y > 0.80)
    green = cov & (h > 35) & (h < 130) & (s > 0.06) & (v < 0.6) & (y > 0.80) & ~slate
    clean = lambda m: ndi.binary_opening(ndi.binary_closing(m, iterations=2), iterations=1) & cov
    green, slate = clean(green), clean(slate) & ~clean(green)
    breeches = cov & (y > 0.40) & (y < 0.98) & (v < 0.42) & ~green & ~slate & ((h < 45) | (h > 330))
    # sleeves: the tunic class beyond the shoulder plane (3 cm inside the UpperArm joint, normal to the upper arm)
    beyond = np.zeros(cov.shape, bool)
    Pn = np.nan_to_num(P, nan=0.0)
    for sh, d in shoulder_planes(glb):
        side = np.sign(sh[0])
        t_ = (Pn - sh) @ d
        radial = np.linalg.norm((Pn - sh) - t_[..., None] * d, axis=-1)
        beyond |= cov & (t_ > -0.03) & (radial < 0.11) & (np.sign(Pn[..., 0]) == side)
    sleeves = green & beyond
    tunic = green & ~beyond
    classes = {'tunic': tunic, 'collar': slate, 'breeches': breeches, 'sleeves': sleeves}
    names = ['tunic', 'collar', 'breeches', 'sleeves']
    print('BODY texels', {n: int(classes[n].sum()) for n in names}, 'covered', int(cov.sum()))
    masks = [soften(classes[n], cov) for n in names]
    lin = R.srgb_to_linear(base)
    lum = lin @ R.LUMA
    targets = {}
    for t in ('D', 'C'):
        tgt = lin.copy()
        for n in names:
            m = classes[n]
            qa, qb = q[n][t], q[n]['B']
            rank = np.zeros_like(lum)
            vals = lum[m]
            rank[m] = np.argsort(np.argsort(vals)) / max(len(vals) - 1, 1)
            k = len(qa) - 1
            tt = np.clip(rank * k, 0, k)
            i0 = np.minimum(np.floor(tt).astype(int), k - 1)
            f = (tt - i0)[..., None]
            tgt[m] = tier_a_colour(qa, qb, i0, f, lum)[m]
        targets[t] = np.where(tgt <= 0.0031308, tgt * 12.92, 1.055 * np.clip(tgt, 0, 1) ** (1 / 2.4) - 0.055)
    ramps = {'pm7d_d': [], 'pm7d_c': []}
    report = {}
    for n in names:
        core = ndi.binary_erosion(classes[n], iterations=1).astype(np.float64)
        r, rep = R.fit_ramps(base, {'pm7d_d': targets['D'], 'pm7d_c': targets['C']}, core)
        for k_ in ramps:
            ramps[k_].append(r[k_])
        report[n] = rep
    R.write_mask(masks, T / 'pm7d_region_mask.png', N)
    cfg = {'variants': ['pm7d_d', 'pm7d_c'],
           'materials': [{'base': 'PeasantM7d', 'prefix': 'PeasantM7d', 'mask': 'pm7d_region_mask.png', 'ramps': ramps}],
           'note': 'tier_pm7d.py: shared paint = PeasantM7 PEASANTM7B; D = PEASANTM7D (row 25), C = PEASANTM7C (row 27); '
                   'regions R tunic, G collar/placket/hem, B breeches, A sleeves; head: own paint per tier (tier_head.py)',
           'fit_report': report}
    json.dump(cfg, open(T / 'pm7d_ramps.json', 'w'), indent=1, default=float)
    print('FIT', json.dumps(report, default=float)[:2000])
    for t in ('D', 'C'):
        Image.fromarray((np.clip(targets[t], 0, 1) * 255).astype(np.uint8)).save(OUT / f'body_target{t}.png')
    Image.fromarray((np.stack([tunic | sleeves * 0, slate, breeches], -1) * 255).astype(np.uint8)).save(OUT / 'body_classes.png')
    Image.fromarray((np.stack([tunic, sleeves, breeches], -1) * 255).astype(np.uint8)).save(OUT / 'body_tunic_sleeves.png')


if __name__ == '__main__':
    main()
