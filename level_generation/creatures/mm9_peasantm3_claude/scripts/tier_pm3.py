#!/usr/bin/env python3
"""Colour tiers of PeasantM3 as one shared skin + region mask + ramps (CLAUDE_CREATURE_TEXTURES.md).

The shared set is the tier A paint (MONSTERS.txt row 52, PEASANTM3A: wine-red velvet tunic, orange-gold brocade bands;
12 of the body's 16 placed objects). Tier B (row 45, PEASANTM3B: brown knit tunic, duller gold bands) is ramps on the
same texels. Breeches, boots and belt are the same art and colour in both MM9 skins (measured), so they are no region.
Both MM9 skins share one UV layout, so each region's colour change is measured on the same MM9 skin rectangles:
  body set   R tunic (red -> brown); the brocade bands are no region (both tiers keep the painted bands)
Region texels: hue/value classes of the graded paint, limited to the main shell (torso, sleeves, skirt; breeches and
boots are their own pieces in the same ochre/gold hues) (texel positions rasterised
from LOD0 of the textured export). Tier B target per texel = qB(t) x L(ours) / L(qA(t)) (linear RGB), t = the texel's
luminance quantile inside its region; region_variants.fit_ramps fits both tiers' ramps (tier A reproduces the paint).
The faces are different men: each tier has its own head image (tier_head.py), no head ramps. Skin B's jewelled chain
necklace is not carried (README "Deviations").
Usage (project folder): tier_pm3.py work/pm3_body_tex_unlined.glb (the textured export of work/rigid_v1.blend: the own-paint
twins of the lined build share their faces UVs and would overwrite the piece and island rasters) <textured glb> -> textures/pm3_region_mask.png, pm3_ramps.json, review/tiers_preview/"""
import colorsys
import os
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
    mesh = next(m for m in g.meshes if m.name == 'PeasantM3')
    out = {}
    for p in mesh.primitives:
        P = accessor(g, blob, p.attributes.POSITION).astype(np.float64)
        UV = accessor(g, blob, p.attributes.TEXCOORD_0).astype(np.float64)
        I = accessor(g, blob, p.indices).reshape(-1, 3)
        img = np.full((N, N, 3), np.nan)
        # connected pieces (positions welded at UV seams): per-texel piece id of its triangle
        key = np.unique(np.round(P, 5), axis=0, return_inverse=True)[1].ravel()
        par = np.arange(key.max() + 1)
        def find(a):
            while par[a] != a:
                par[a] = par[par[a]]; a = par[a]
            return a
        for t3 in key[I]:
            ra, rb, rc = find(t3[0]), find(t3[1]), find(t3[2])
            par[rb] = ra; par[find(rc)] = ra
        root = np.array([find(k) for k in range(len(par))])
        tri_piece = root[key[I[:, 0]]]
        par2 = np.arange(len(P))
        def find2(a):
            while par2[a] != a:
                par2[a] = par2[par2[a]]; a = par2[a]
            return a
        for t3 in I:
            r0 = find2(t3[0]); par2[find2(t3[1])] = r0; par2[find2(t3[2])] = r0
        tri_island = np.array([find2(t3[0]) for t3 in I])
        iid = np.full((N, N), -1, np.int64)
        pid = np.full((N, N), -1, np.int64)
        for ti, tri in enumerate(I):
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
            pid[q[ok, 1].astype(int), q[ok, 0].astype(int)] = tri_piece[ti]
            iid[q[ok, 1].astype(int), q[ok, 0].astype(int)] = tri_island[ti]
        nm = g.materials[p.material].name.split('_')[0]
        out[nm] = img
        out[nm + '#piece'] = pid
        out[nm + '#island'] = iid
        # the main shell = the piece with the most triangles (torso, sleeves, tunic skirt; legs and boots are own pieces)
        vals, cnt = np.unique(tri_piece, return_counts=True)
        out[nm + '#main'] = vals[np.argsort(-cnt)[:2]]     # torso+sleeves shell; tunic skirt + breeches piece
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
    skinA = np.asarray(Image.open('source/mm9/skins/pm3a.png').convert('RGB'), np.float64) / 255
    skinB = np.asarray(Image.open('source/mm9/skins/pm3b.png').convert('RGB'), np.float64) / 255
    # MM9 skin rectangles (4x preview coordinates): tunic body + skirt (right of B's chain), brocade collar band + hem band
    regions_mm9 = {
        'tunic': ([140, 380, 572, 780], [140, 800, 572, 972]),
        'brocade': ([0, 320, 572, 376], [0, 984, 572, 1024]),
    }
    q = {}
    for name, rects in regions_mm9.items():
        hue = {'tunic': (330, 40), 'brocade': (15, 60)}[name]
        pa = np.concatenate([mm9_region(skinA, r, hue) for r in rects])
        pb = np.concatenate([mm9_region(skinB, r, hue) for r in rects])
        q[name] = (quantiles(pa), quantiles(pb))
        print('MM9', name, 'A mean', (pa.mean(0) * 255).round(), 'B mean', (pb.mean(0) * 255).round())

    base = R.load_srgb(T / 'pm3_tp_basecolor_graded.png', N)
    P = pos['PeasantM3']
    cov = ~np.isnan(P[..., 0])
    y = np.nan_to_num(P[..., 1], nan=-1)        # height above the floor (glTF y up), m
    print('HEIGHT range', np.nanmin(P[..., 1]), np.nanmax(P[..., 1]))
    h, s, v = hsv(base)
    clean = lambda m: ndi.binary_opening(ndi.binary_closing(m, iterations=2), iterations=1) & cov
    pid = pos['PeasantM3#piece']
    mains = pos['PeasantM3#main']
    tunic_y = np.isin(pid, mains)
    red = cov & ((h > 335) | (h < 18)) & (s > 0.35) & (v < 0.75) & tunic_y
    # the tunic skirt is one Meshy piece with the breeches (same gold/ochre hues): gold only above the skirt's lowest
    # red texels (the hem band sits on the skirt's bottom edge, 3 cm margin)
    skirt_piece = min(mains, key=lambda k: y[pid == k].min())
    # reddish specks in the woven breeches reach down to 0.4 m: the skirt starts at the first 5 cm band holding more
    # than 10 % of the densest band's red texels (0.85 m on this paint)
    hist, edges = np.histogram(y[clean(red) & (pid == skirt_piece)], bins=np.arange(0.4, 1.15, 0.05))
    hem_y = edges[np.argmax(hist > 0.1 * hist.max())] - 0.03
    red &= (pid != skirt_piece) | (y > hem_y)
    print('SKIRT heights', np.histogram(y[clean(red) & (pid == skirt_piece)], bins=np.arange(0.4, 1.1, 0.05))[0].tolist())
    print('SKIRT piece', skirt_piece, 'hem limit y', round(float(hem_y), 3))
    gold = cov & (h > 18) & (h < 58) & (s > 0.45) & (v > 0.30) & tunic_y & ~red & ((pid != skirt_piece) | (y > hem_y))
    red, gold = clean(red), clean(gold) & ~clean(red)
    # gold specks in the velvet (sheen) join the tunic; only large gold pieces (the bands) stay out of it
    lab, nl = ndi.label(gold)
    sizes = ndi.sum(gold, lab, range(1, nl + 1))
    band = np.isin(lab, 1 + np.nonzero(sizes >= 150)[0])
    red = (red | (gold & ~band)) & tunic_y
    gold = band
    # brocade bands are no region: a luminance ramp cannot keep tier A's red zigzags on gold (fit error 10 / 36 levels),
    # and skin B's bands are only ~20 % duller than A's (measured), so both tiers keep the painted bands
    # G: the body set's neck skin (the nape and neck sides below the head-set cut, painted in A's warm tone): tier B's
    # paler skin by the ratio of the two head sets' cheek skin (fix_neck_pm3.py refs: A 215,126,92; B 238,162,123)
    r_ax = np.hypot(np.nan_to_num(P[..., 0]), np.nan_to_num(P[..., 2]))
    neck = cov & (y > 1.44) & (r_ax < 0.13) & (h > 5) & (h < 35) & (s > 0.2) & (s < 0.7) & (v > 0.5) & ~red
    neck = clean(neck)
    # B: the breeches (the skirt piece below the hem): the 4K paint made them bright gold-ochre, MM9's are dark brown with a
    # gold weave in both skins (mean 74,40,18): both tiers take MM9's colour at each luminance quantile x our weave
    breeches = cov & (pid == skirt_piece) & (y < hem_y - 0.01) & ~red
    # above the hem the same piece holds the hem band (on the skirt surface) and the breeches under the skirt (seen
    # through the side slits): texels more than 1.2 cm inside the nearest red skirt texel's radius, or > 8 cm from it,
    # are breeches
    from scipy.spatial import cKDTree
    up = cov & (pid == skirt_piece) & (y >= hem_y - 0.01) & ~red
    rad = np.hypot(np.nan_to_num(P[..., 0]), np.nan_to_num(P[..., 2]))
    rs = red & (pid == skirt_piece)
    tr = cKDTree(P[rs])
    dd, kk = tr.query(P[up])
    inner = (rad[up] < rad[rs][kk] - 0.012) | (dd > 0.08)
    upb = np.zeros_like(up); upb[up] = inner
    # UV islands of the skirt piece with almost no tunic red that reach below the hem are breeches in full (the surface
    # under the skirt, seen through the side slits and under the flaring hem in Running)
    isl = pos['PeasantM3#island']
    for k in np.unique(isl[cov & (pid == skirt_piece)]):
        m = cov & (isl == k)
        if os.environ.get('DBG'):
            print('ISLAND', k, int(m.sum()), 'red %.2f' % red[m].mean(), 'y %.2f..%.2f' % (y[m].min(), y[m].max()))
        if red[m].mean() < 0.15 and y[m].min() < hem_y - 0.05:
            upb |= m & ~red
        elif y[m].min() < hem_y - 0.05:
            # mixed islands (xatlas charts cross the hem: breeches below, skirt above): non-red texels below this island's
            # own lowest red that are not hem brocade (bright orange-red zigzag within 3 texels) are breeches
            rl = np.percentile(y[m & red], 2) if (m & red).any() else hem_y
            bright_or = ((h < 25) | (h > 340)) & (s > 0.5) & (v > 0.45)
            nb = ndi.uniform_filter(bright_or.astype(float), 7) > 0.02
            upb |= m & ~red & (y < rl) & ~nb
    # Meshy also painted the breeches weave onto the skirt islands (inside the side slits, a strip under the hem band):
    # non-red texels there with no orange-red within 3 texels (the hem brocade carries an orange-red zigzag, the weave
    # only dark brown and yellow) are breeches too
    orange = cov & (((h < 25) | (h > 340)) & (s > 0.5))
    near_or = ndi.uniform_filter(orange.astype(float), 7) > 0.02
    weave = up & ~near_or & (h > 30) & (h < 60)
    # within 5 cm of the hem (the skirt's lower and inner faces) the weave sits right against the brocade: no orange-red in
    # the immediate 3x3 neighbourhood is enough
    near_or1 = ndi.uniform_filter(orange.astype(float), 3) > 0.0
    weave |= cov & (pid == skirt_piece) & ~red & (np.abs(y - hem_y) < 0.05) & ~near_or1 & (h > 30) & (h < 60) & (s > 0.45)
    upb |= weave
    print('WEAVE on skirt islands', int(weave.sum()))
    breeches = clean(breeches | upb)
    print('BREECHES under the skirt', int(upb.sum()), 'of', int(up.sum()))
    if os.environ.get('DBG'):
        print('UP v hist', np.histogram(v[up], bins=10, range=(0, 1))[0].tolist())
        print('UP depth hist', np.histogram((rad[rs][kk] - rad[up]), bins=10, range=(-0.05, 0.05))[0].tolist())
        print('UP height hist', np.histogram(y[up], bins=10, range=(0.75, 1.15))[0].tolist())
        dbg = np.zeros(up.shape + (3,), np.uint8); dbg[up] = (255, 255, 0); dbg[upb] = (255, 0, 0); dbg[rs] = (80, 0, 0)
        Image.fromarray(dbg).save('/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/74ae08a0-ce66-4dda-8cb9-a8062f5327d4/scratchpad/up.png')
    masks = [soften(red, cov), soften(neck, cov), soften(breeches, cov)]
    names = ['tunic', 'neckskin', 'breeches']
    print('BODY texels', {n: int(m.sum()) for n, m in zip(names, (red, neck, breeches))}, 'covered', int(cov.sum()))
    lin = R.srgb_to_linear(base)
    lum = lin @ R.LUMA
    targetB = lin.copy()
    for n, m in zip(names, (red,)):
        qa, qb = q[n]
        rank = np.zeros_like(lum)
        vals = lum[m]
        rank[m] = np.argsort(np.argsort(vals)) / max(len(vals) - 1, 1)
        k = len(qa) - 1
        t = np.clip(rank * k, 0, k)
        i0 = np.minimum(np.floor(t).astype(int), k - 1)
        f = (t - i0)[..., None]
        targetB[m] = tier_a_colour(qb, qa, i0, f, lum)[m]     # target = skin B at the quantile x ours / skin A there
    qbr = quantiles(np.concatenate([mm9_region(skinA, [580, 340, 800, 920])]))
    vals = lum[breeches]
    qo = quantiles(base[breeches])
    rank = np.zeros_like(lum)
    rank[breeches] = np.argsort(np.argsort(vals)) / max(len(vals) - 1, 1)
    k = len(qbr) - 1
    t = np.clip(rank * k, 0, k)
    i0 = np.minimum(np.floor(t).astype(int), k - 1)
    f = (t - i0)[..., None]
    tbr = tier_a_colour(qbr, qo, i0, f, lum)
    targetB[breeches] = tbr[breeches]
    targetA = lin.copy()
    targetA[breeches] = tbr[breeches]
    ratio = R.srgb_to_linear(np.array([238, 162, 123]) / 255.0) / R.srgb_to_linear(np.array([215, 126, 92]) / 255.0)
    # the nape strip takes each tier's own head-set neck tone (fix_neck_pm3.py: cheek ref x ~0.9 toward the collar), with
    # the paint's light detail (sqrt of luminance over its mean): the A paint's strip was lighter pink than A's head neck
    nl = (lum / max(lum[neck].mean(), 1e-4)) ** 0.2   # r2d: flatter (lighter angular patches on the neck sides)
    for tgt, ref in ((targetA, (215, 126, 92)), (targetB, (238, 162, 123))):
        tgt[neck] = (R.srgb_to_linear(np.array(ref) / 255.0) * 0.82)[None, :] * nl[neck][:, None]
    tA = np.where(targetA <= 0.0031308, targetA * 12.92, 1.055 * np.clip(targetA, 0, 1) ** (1 / 2.4) - 0.055)
    tB = np.where(targetB <= 0.0031308, targetB * 12.92, 1.055 * np.clip(targetB, 0, 1) ** (1 / 2.4) - 0.055)
    ramps_body = {'pm3_a': [], 'pm3_b': []}
    report = {}
    for n, m in zip(names, (red, neck, breeches)):
        core = ndi.binary_erosion(m, iterations=1).astype(np.float64)
        r, rep = R.fit_ramps(base, {'pm3_a': tA, 'pm3_b': tB}, core)
        for k_ in ramps_body:
            ramps_body[k_].append(r[k_])
        report[n] = rep
    R.write_mask(masks, T / 'pm3_region_mask.png', N)
    cfg = {'variants': ['pm3_a', 'pm3_b'],
           'materials': [
               {'base': 'PeasantM3', 'prefix': 'PeasantM3', 'mask': 'pm3_region_mask.png', 'ramps': ramps_body}],
           'note': 'tier_pm3.py: shared paint = PEASANTM3A (row 52); B = PEASANTM3B (row 45) MM9 skin B colour at each luminance quantile x our/MM9-A luminance; heads per tier (tier_head.py)',
           'fit_report': report}
    json.dump(cfg, open(T / 'pm3_ramps.json', 'w'), indent=1, default=float)
    print('FIT', json.dumps(report, default=float)[:1500])
    Image.fromarray((np.clip(tB, 0, 1) * 255).astype(np.uint8)).save(OUT / 'body_targetB.png')
    Image.fromarray((np.stack([red, gold, np.zeros_like(red)], -1) * 255).astype(np.uint8)).save(OUT / 'body_classes.png')


if __name__ == '__main__':
    main()
