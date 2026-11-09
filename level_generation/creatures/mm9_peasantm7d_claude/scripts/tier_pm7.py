#!/usr/bin/env python3
"""Colour tiers of PeasantM7 as one shared skin + region mask + ramps (CLAUDE_CREATURE_TEXTURES.md).

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
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a.componentType]
    off = (bv.byteOffset or 0) + (a.byteOffset or 0)
    arr = np.frombuffer(blob, dtype=dt, count=a.count * n, offset=off).reshape(a.count, n)
    return arr


def raster_positions(glb):
    """Per material: NxN rest-pose position (glTF y up) of the texel centre, NaN outside the islands."""
    g = GLTF2().load(glb)
    blob = g.binary_blob()
    mesh = next(m for m in g.meshes if m.name == 'PeasantM7')
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


def main():
    pos = raster_positions(sys.argv[1])
    skinA = np.asarray(Image.open('source/mm9/skins/pm7a.png').convert('RGB'), np.float64) / 255
    skinB = np.asarray(Image.open('source/mm9/skins/pm7b.png').convert('RGB'), np.float64) / 255
    # MM9 skin rectangles (4x preview coordinates): tunic body + skirt, collar band + placket + hem band, breeches, hair
    regions_mm9 = {
        'tunic': ([40, 390, 550, 740], [40, 820, 560, 960]),
        'collar': ([60, 325, 570, 375], [0, 975, 560, 1024]),
        'breeches': ([590, 340, 770, 880],),
        'hair': ([120, 0, 410, 230],),
    }
    q = {}
    for name, rects in regions_mm9.items():
        # per-tier hue filters keep each rectangle to its own cloth (A's gold band vs the blue tunic below it)
        hue_a, hue_b = {'hair': ((0, 50), (0, 50)), 'tunic': ((180, 270), (35, 110)),
                        'collar': ((15, 65), (180, 280))}.get(name, (None, None))
        pa = np.concatenate([mm9_region(skinA, r, hue_a) for r in rects])
        pb = np.concatenate([mm9_region(skinB, r, hue_b) for r in rects])
        q[name] = (quantiles(pa), quantiles(pb))
        print('MM9', name, 'A mean', (pa.mean(0) * 255).round(), 'B mean', (pb.mean(0) * 255).round())

    # ---- body set
    base = R.load_srgb(T / 'pm7_tp_basecolor_graded.png', N)
    P = pos['PeasantM7']
    cov = ~np.isnan(P[..., 0])
    y = np.nan_to_num(P[..., 1], nan=-1)        # height above the floor (glTF y up), m
    h, s, v = hsv(base)
    slate = cov & (h > 175) & (h < 265) & (s > 0.06) & (y > 0.80)
    green = cov & (h > 35) & (h < 130) & (s > 0.06) & (v < 0.6) & (y > 0.80) & ~slate
    # the woven paint flickers in hue texel to texel: close then open each class (3 px) before use
    clean = lambda m: ndi.binary_opening(ndi.binary_closing(m, iterations=2), iterations=1) & cov
    green, slate = clean(green), clean(slate) & ~clean(green)
    breeches = cov & (y > 0.40) & (y < 0.98) & (v < 0.42) & ~green & ~slate & ((h < 45) | (h > 330))
    masks = [soften(green, cov), soften(slate, cov), soften(breeches, cov)]
    names = ['tunic', 'collar', 'breeches']
    print('BODY texels', {n: int(m.sum()) for n, m in zip(names, (green, slate, breeches))}, 'covered', int(cov.sum()))
    lin = R.srgb_to_linear(base)
    lum = lin @ R.LUMA
    targetA = lin.copy()
    for n, m in zip(names, (green, slate, breeches)):
        qa, qb = q[n]
        rank = np.zeros_like(lum)
        vals = lum[m]
        order = np.argsort(np.argsort(vals))
        rank[m] = order / max(len(vals) - 1, 1)
        k = len(qa) - 1
        t = np.clip(rank * k, 0, k)
        i0 = np.minimum(np.floor(t).astype(int), k - 1)
        f = (t - i0)[..., None]
        targetA[m] = tier_a_colour(qa, qb, i0, f, lum)[m]
    tA = R.linear_to_srgb(np.clip(targetA, 0, 1)) if hasattr(R, 'linear_to_srgb') else None
    if tA is None:
        tA = np.where(targetA <= 0.0031308, targetA * 12.92, 1.055 * np.clip(targetA, 0, 1) ** (1 / 2.4) - 0.055)
    ramps_body = {'pm7_a': [], 'pm7_b': []}
    report = {}
    # fit on the class texels themselves (eroded 1 texel), not the padded gutters: Meshy's gutter streaks and the cream
    # lacing stretched the tunic range to luminance 0.8 and left the cloth on the bottom three stops (grey tier A, v1)
    for n, m in zip(names, (green, slate, breeches)):
        core = ndi.binary_erosion(m, iterations=1).astype(np.float64)
        r, rep = R.fit_ramps(base, {'pm7_a': tA, 'pm7_b': base}, core)
        for k_ in ramps_body:
            ramps_body[k_].append(r[k_])
        report[n] = rep
    R.write_mask(masks, T / 'pm7_region_mask.png', N)

    # ---- head set: hair
    hbase = R.load_srgb(T / 'pm7_tp_head_basecolor.png', N)
    HP = pos['PeasantM7Head']
    hcov = ~np.isnan(HP[..., 0])
    hy = np.nan_to_num(HP[..., 1], nan=-1)
    hz = np.nan_to_num(HP[..., 2], nan=0)       # glTF +z = the model's front? measured below
    hh, hs, hv = hsv(hbase)
    # behind the head (glTF -z) the hair reaches the nape, lower than the forehead cut (v1.5: dark nape band on tier A)
    hair = hcov & ((hy > 1.60) | ((hy > 1.44) & (hz < -0.02))) & (hv < 0.50) & ((hh < 40) | (hh > 340)) & (hs > 0.35)
    print('HEAD hair texels', int(hair.sum()), 'covered', int(hcov.sum()), 'head z range', np.nanmin(HP[..., 2]), np.nanmax(HP[..., 2]))
    # v1.4: the feathered edge put the ramp's light end on the forehead skin (a pale ginger line along the hairline on
    # tier A): feather inside the hair only and fade the weight out above the hair's own luminance
    # (not eroded: an eroded class left dark tier-B lines along every hair UV seam on tier A, v1.4)
    hmask = soften(hair, hcov)
    hl = R.srgb_to_linear(hbase) @ R.LUMA
    cap = np.percentile(hl[hair], 92)
    hmask *= np.clip(1 - (hl - cap) / (0.3 * cap), 0, 1)
    hlin = R.srgb_to_linear(hbase)
    hlum = hlin @ R.LUMA
    htA = hlin.copy()
    qa, qb = q['hair']
    vals = hlum[hair]
    rank = np.zeros_like(hlum)
    rank[hair] = np.argsort(np.argsort(vals)) / max(len(vals) - 1, 1)
    k = len(qa) - 1
    t = np.clip(rank * k, 0, k)
    i0 = np.minimum(np.floor(t).astype(int), k - 1)
    f = (t - i0)[..., None]
    htA[hair] = tier_a_colour(qa, qb, i0, f, hlum)[hair]
    htA_s = np.where(htA <= 0.0031308, htA * 12.92, 1.055 * np.clip(htA, 0, 1) ** (1 / 2.4) - 0.055)
    rh, reph = R.fit_ramps(hbase, {'pm7_a': htA_s, 'pm7_b': hbase}, ndi.binary_erosion(hair, iterations=1).astype(np.float64))
    report['hair'] = reph
    R.write_mask([hmask], T / 'pm7_head_region_mask.png', N)
    cfg = {'variants': ['pm7_a', 'pm7_b'],
           'materials': [
               {'base': 'PeasantM7', 'prefix': 'PeasantM7', 'mask': 'pm7_region_mask.png', 'ramps': ramps_body},
               {'base': 'PeasantM7Head', 'prefix': 'PeasantM7Head', 'mask': 'pm7_head_region_mask.png',
                'ramps': {k_: [rh[k_]] for k_ in ('pm7_a', 'pm7_b')}}],
           'note': 'tier_pm7.py: shared paint = PEASANTM7B (row 51); A = PEASANTM7A (row 53) MM9 skin A colour at each luminance quantile x our/MM9-B luminance',
           'fit_report': report}
    json.dump(cfg, open(T / 'pm7_ramps.json', 'w'), indent=1, default=float)
    print('FIT', json.dumps(report, default=float)[:1500])
    # previews of the targets
    Image.fromarray((np.clip(tA, 0, 1) * 255).astype(np.uint8)).save(OUT / 'body_targetA.png')
    Image.fromarray((np.clip(htA_s, 0, 1) * 255).astype(np.uint8)).save(OUT / 'head_targetA.png')
    Image.fromarray((np.stack([green, slate, breeches], -1) * 255).astype(np.uint8)).save(OUT / 'body_classes.png')
    Image.fromarray((hair * 255).astype(np.uint8)).save(OUT / 'head_hair.png')


if __name__ == '__main__':
    main()
