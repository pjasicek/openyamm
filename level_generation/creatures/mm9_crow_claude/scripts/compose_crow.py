#!/usr/bin/env python3
"""Shared texture set, region mask and ramps for the MM9 crow ("Bird" rows 93-95; ported from
mm9_wolf_claude/scripts/compose_wolf.py). Usage: compose_crow.py

All three MM9 Bird rows name crow.dtx (Bird C names a missing drow.dtx; MM9 then shows the model default crow.dtx,
devdocs/mm9/MM9_MONSTER_LEGACY_SPRITE_MAPPING.md). User decision 2026-10-30: Bird A stays the crow (crow_a, identity
ramps) and Bird B/C take MM9's unused eagle skin BIRD.dtx (crow_b): per region, the eagle palette from BIRD.dtx is
carried by the ramps (our luminance rank, the eagle's chroma bands and brightness). BIRD.dtx was painted for another
layout: on CROW.abc's UVs its legs fall on black and the body partly on background, so its regions are sampled from
the skin art itself (feathers, beak triangles, the amber eye, the yellow leg strip), not through the crow UVs.
The tiers differ by size as well (MONSTERS.txt Scale 1, 1.25, 1.5). Regions:
  R plumage - every texel outside the other regions;  G beak - head texels mostly Xbeak weighted;
  B eyes    - the two separate eye pieces;            A legs - legs and feet (below the body in the bind pose).
Outputs in textures/: crow_basecolor.png (2K, padded; graded by grade_basecolor.py), crow_normal_1k.png,
crow_metal_rough_1k.png (R AO, G roughness, B metallic 0), crow_material_classes.png, crow_region_mask.png,
crow_ramps.json.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV

T = HERE / 'textures'
M = HERE / 'meshy' / 'crow_retexture_v2'   # 4K paint on the xatlas UVs (texture-quality pass, 2026-10-30)
W = np.array([0.2126, 0.7152, 0.0722])
TIERS = {'crow_a': 'crow/skins/crow.png', 'crow_b': 'bird/skins/bird.png'}
TIER_A = 'crow_a'
REGIONS = ('plumage', 'beak', 'eyes', 'legs')
IDENTITY = set()     # tier A is always identity (chroma_targets); the eagle recolours every region
MAT = 'Crow'


def lin(c):
    return RV.srgb_to_linear(c)


def encode(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, d / (mx + 1e-9), mx


def raster(npz, size, fields):
    d = np.load(npz)
    uv = d['uv'] * size
    tri = np.full((size, size), -1, np.int32)
    out = {f: np.zeros((size, size), np.float32) for f in fields}
    for t in range(len(uv)):
        p = uv[t]
        x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), size - 1)
        y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        l3 = 1 - l1 - l2
        inside = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
        if not inside.any():
            continue
        iy, ix = np.nonzero(inside)
        rows, cols = size - 1 - (iy + y0), ix + x0
        tri[rows, cols] = t
        for f in fields:
            v = d[f][t]
            out[f][rows, cols] = l1[inside] * v[0] + l2[inside] * v[1] + l3[inside] * v[2]
    return tri, out, d


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def feather(m, covered):
    m = pad(m.astype(np.float32), covered)
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)),
                      np.float32) / 255


# ---------------- our texel classes (1K)
S = 1024
tri, f, dbody = raster(HERE / 'work' / 'uv3d_crow.npz', S, ['head'])
covered = tri >= 0
ti = np.maximum(tri, 0)
part = np.where(covered, dbody['part'][ti], -1)
cen = dbody['xyz'].mean(1)[ti]
base2k = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((2048, 2048), Image.LANCZOS),
                    np.float32) / 255   # 4K -> 2K once (the creature cook caps colour at 2048)
base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
eyes = covered & (part % 10 == 2)
beak = covered & ~eyes & (f['head'] > 0.5)
legs = covered & ~eyes & (cen[..., 2] < -0.07) & (np.abs(cen[..., 0]) < 0.12)
plumage = covered & ~(eyes | beak | legs)
classes = np.zeros((S, S), np.uint8)
for k, m in enumerate((plumage, beak, eyes, legs)):
    classes[m] = k + 1
regions = [feather(m, covered) for m in (plumage, beak, eyes, legs)]
RV.write_mask(regions, T / 'crow_region_mask.png')
Image.fromarray(classes * 60).save(T / 'crow_material_classes.png')
tri2, _, _ = raster(HERE / 'work' / 'uv3d_crow.npz', 2048, [])
Image.fromarray((pad(base2k, tri2 >= 0) * 255).astype(np.uint8)).save(T / 'crow_basecolor.png')
nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((2048, 2048), Image.LANCZOS), np.float32) / 255
Image.fromarray((pad(nrm, tri2 >= 0) * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS).save(T / 'crow_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
# matt feathers, horn beak, wet eyes, scaly legs. Plumage was 0.45-0.7 ("glossy black"): on black paint nearly all the
# light is the specular lobe, so at that roughness every patch of the low-poly shell that faced a viewer light flared
# into a pale grey blotch with the feather normals in it (viewer 2026-10-30, wings and the breast)
rough = np.where(plumage, 0.82 + 0.4 * (np.clip(rough, 0.45, 0.7) - 0.45), np.where(beak, 0.4, np.where(eyes, 0.15, 0.6)))
rough = pad(rough, covered)
ao = np.asarray(Image.open(T / 'crow_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'crow_metal_rough_1k.png')

# ---------------- MM9 skins: region texels per skin (128 x 128, the CROW.abc UV layout)
skins = {k: np.asarray(Image.open(HERE / 'source' / p).convert('RGB'), np.float32) / 255 for k, p in TIERS.items()}
EYE = {'crow_a': (51.0, 17.0, 4.5), 'crow_b': (48.0, 20.5, 6.5)}     # eye circles (x, y, radius) in skin pixels
LEG_STRIP = (108, 2, 126, 40)                                       # BIRD.dtx yellow leg strip (x0, y0, x1, y1)
KNEE_GAIN = 0.35  # plumage highlights above the 75th percentile keep this share of their excess luminance
HEAD_MATCH = 0.85    # share of the rank colour transfer from the body plumage onto the head plumage
SEAM_FADE = 0.02     # m: the body neck darkens towards the head's paint this far from the head faces
BEAK_DARKEN = 0.4   # the head retexture's pale silver bill -> the references' grey-black horn (linear factor)
ALBEDO = 1.35    # skins carry baked shading: albedo ~1.3-1.45 x the native colour (CLAUDE_CREATURE_TEXTURES.md)


def mm9_region_sets(tier):
    sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
    from glb_pose import Glb
    g = Glb(HERE / 'source' / 'crow' / 'crow.glb')
    d = g.json
    prim = d['meshes'][0]['primitives'][0]
    a = prim['attributes']
    uv = g.accessor(a['TEXCOORD_0'])
    jn = [d['nodes'][j]['name'] for j in d['skins'][0]['joints']]
    jj, ww = g.accessor(a['JOINTS_0']).astype(int), g.accessor(a['WEIGHTS_0'])
    dom = [jn[jj[i][int(np.argmax(ww[i]))]] for i in range(len(uv))]
    n = skins[tier].shape[0]
    layers = {r: Image.new('L', (n, n), 0) for r in ('beak', 'legs', 'body')}
    from PIL import ImageDraw
    for t in g.accessor(prim['indices']).reshape(-1, 3).astype(int):
        labs = [dom[i] for i in t]
        lab = sorted(set(labs), key=lambda x: (-labs.count(x), x))[0]   # deterministic ties
        r = 'beak' if lab in ('Xbeak', 'Xjawpiv') else 'legs' if lab.startswith(('Xleg', 'Xfoot', 'Xtoe')) else 'body'
        ImageDraw.Draw(layers[r]).polygon([tuple(uv[i] * n) for i in t], fill=255)
    lay = {r: np.asarray(m) > 0 for r, m in layers.items()}
    yy, xx = np.mgrid[:n, :n] + 0.5
    cx, cy, rad = EYE[tier]
    eye = (xx - cx) ** 2 + (yy - cy) ** 2 < rad ** 2
    lum = skins[tier] @ W
    beak = lay['beak'] & ~eye
    if tier == 'crow_b':
        strip = np.zeros((n, n), bool)
        x0, y0, x1, y1 = LEG_STRIP
        strip[y0:y1, x0:x1] = True
        legs = strip & (lum > 0.25)
        plumage = (lum > 0.06) & ~beak & ~eye & ~strip
    else:
        legs = lay['legs'] & (lum > 0.03)
        plumage = (lay['body'] | lay['legs']) & ~lay['legs'] & ~beak & ~eye & (lum > 0.03)
    return {'plumage': plumage, 'beak': beak, 'eyes': eye, 'legs': legs}


mm9_sets_by_tier = {k: mm9_region_sets(k) for k in TIERS}
counts = {k: {r: int(m.sum()) for r, m in v.items()} for k, v in mm9_sets_by_tier.items()}


def fit_or_empty(graded, targets, weight):
    """fit_ramps, or a neutral ramp for a region this material does not use (the body lost its beak to the graft)"""
    if (weight >= 0.9).sum() < 100:
        neutral = {'range': [0.0, 1.0], 'colors': [[i / 15] * 3 for i in range(16)]}
        return {k: dict(neutral) for k in TIERS}, {'unused': True}
    return RV.fit_ramps(graded, targets, weight)


def chroma_targets(graded, weight, name):
    core = weight > 0.5
    targets = {TIER_A: graded.copy()}
    if name in IDENTITY or min(v[name].sum() for v in mm9_sets_by_tier.values()) < 12 or core.sum() < 12:
        for k in TIERS:
            targets[k] = graded.copy()
        return targets
    glum = lin(graded[core]) @ W
    rank = np.empty(glum.size)
    rank[np.argsort(glum)] = (np.arange(glum.size) + 0.5) / glum.size
    if name == 'plumage':
        # the 4K Meshy paint flecks the black plumage with pale specks (a starling look, read as blotches next to the
        # glossy MM9 crow): luminance above the region's 75th percentile is compressed (soft knee) for tier A, and
        # the eagle takes the upper palette ranks at half rate (no golden speckle)
        knee = float(np.percentile(glum, 75))
        soft = np.where(glum > knee, knee + (glum - knee) * KNEE_GAIN, glum)
        tA = graded.copy()
        tA[core] = encode(np.clip(lin(graded[core]) * (soft / np.maximum(glum, 1e-6))[:, None], 0, 1))
        targets[TIER_A] = tA
        rank = np.where(rank > 0.75, 0.75 + (rank - 0.75) * 0.5, rank)

    # histogram transfer by luminance rank: our texel at rank r takes the colour of the MM9 skin texel at rank r
    # (window-averaged), so the detail order stays ours and the colours and brightness are the skin's own
    for k in TIERS:
        if k == TIER_A:
            continue
        pal = lin(skins[k][mm9_sets_by_tier[k][name]])
        pal = pal[np.argsort(pal @ W)]
        win = max(1, len(pal) // 25)
        csum = np.concatenate([np.zeros((1, 3)), np.cumsum(pal, 0)])
        q = np.clip((rank * len(pal)).astype(int), 0, len(pal) - 1)
        lo, hi = np.clip(q - win, 0, len(pal)), np.clip(q + win + 1, 0, len(pal))
        tgt = graded.copy()
        tgt[core] = encode(np.clip((csum[hi] - csum[lo]) / (hi - lo)[:, None] * ALBEDO, 0, 1))
        targets[k] = tgt
    return targets


graded = RV.load_srgb(T / 'crow_basecolor_graded.png', S) if (T / 'crow_basecolor_graded.png').exists() else base
report, ramps = [], {k: [] for k in TIERS}
previews = {k: graded.copy() for k in TIERS}
for name, weight in zip(REGIONS, regions):
    targets = chroma_targets(graded, weight, name)
    fitted, rep = fit_or_empty(graded, targets, weight)
    for k in TIERS:
        ramps[k].append(fitted[k])
        core = weight > 0.5
        previews[k][core] = targets[k][core]
    report.append({'region': name, **{k: v.get('mean_abs_8bit') if isinstance(v, dict) else v for k, v in rep.items()}})
materials = [{'base': MAT, 'prefix': MAT, 'mask': 'crow_region_mask.png', 'ramps': ramps}]

# ---------------- grafted head (2026-10-30 head rework): its own 1K set from the 4K head retexture on its own UVs
HEAD_NPZ, MH, GRAFT = HERE / 'work' / 'uv3d_head.npz', HERE / 'meshy' / 'head_retexture_v1', HERE / 'work' / 'graft_v6.json'
head_report = None
if HEAD_NPZ.exists() and MH.exists() and GRAFT.exists():
    g = json.load(open(GRAFT))
    SH = 1024
    triH, _, dH = raster(HEAD_NPZ, SH, [])
    covH = triH >= 0
    tiH = np.maximum(triH, 0)
    partH = np.where(covH, dH['part'][tiH], -1)
    cenH = dH['xyz'].mean(1)[tiH]
    src4 = Image.open(MH / 'texture_urls_0_base_color.png').convert('RGB')
    baseH = np.asarray(src4.resize((SH, SH), Image.LANCZOS), np.float32) / 255
    tipb = np.array(g['placement']['beak_tip']); gape = np.array(g['mm9_beak']['base'])
    ax = tipb - gape; Lb = float(np.linalg.norm(ax)); axn = ax / Lb
    rel = cenH - gape
    proj = rel @ axn / Lb
    rad = np.linalg.norm(rel - (rel @ axn)[..., None] * axn, axis=-1) / Lb
    hH, sH, vH = hsv(baseH)
    eyesH = covH & (partH % 10 == 2)
    # the beak: in front of the gape corner, near the beak axis, and painted as horn (pale, unsaturated)
    geo = covH & ~eyesH & (proj > -0.08) & (rad < 0.5)
    beakH = geo & (((vH > 0.32) & (sH < 0.3)) | (proj > 0.3))
    beakH = ndimage.binary_opening(beakH, iterations=1) | (geo & (proj > 0.45))
    plumH = covH & ~eyesH & ~beakH
    colH = baseH.copy()
    # Meshy painted the bill pale silver; the references (and the user's raven) have a grey-black horn bill
    colH[beakH] = encode(lin(colH[beakH]) * BEAK_DARKEN)
    # tone match of the head plumage to the body plumage at the neck seam (luminance percentiles 5/50/95)
    ring_c = np.array(g['body_ring']['centre'])
    seam_b = plumage & (np.linalg.norm(cen - ring_c, axis=-1) < 0.05)
    seam_h = plumH & (np.linalg.norm(cenH - ring_c, axis=-1) < 0.06)
    lb = lin(graded[seam_b]) @ W
    lh = lin(colH[seam_h]) @ W
    qs = (5, 50, 95)
    pb, ph = np.percentile(lb, qs), np.percentile(lh, qs)
    # the head's plumage takes the body plumage's colours by luminance rank (texels of the body's neck and shoulders,
    # 3-15 cm from the neck ring): its own feather pattern stays, its tone, blue tint and pale flecks become the body's,
    # so the head is neither darker nor smoother than the body where they meet (HEAD_MATCH of the transfer)
    ref = plumage & (np.linalg.norm(cen - ring_c, axis=-1) > 0.03) & (np.linalg.norm(cen - ring_c, axis=-1) < 0.15)
    palb = lin(graded[ref])
    palb = palb[np.argsort(palb @ W)]
    lh_all = lin(colH[plumH]) @ W
    rk = np.empty(lh_all.size); rk[np.argsort(lh_all)] = (np.arange(lh_all.size) + 0.5) / lh_all.size
    win = max(1, len(palb) // 40)
    cs = np.concatenate([np.zeros((1, 3)), np.cumsum(palb, 0)])
    q = np.clip((rk * len(palb)).astype(int), 0, len(palb) - 1)
    lo_, hi_ = np.clip(q - win, 0, len(palb)), np.clip(q + win + 1, 0, len(palb))
    tgt = (cs[hi_] - cs[lo_]) / (hi_ - lo_)[:, None]
    colH[plumH] = encode(np.clip(lin(colH[plumH]) * (1 - HEAD_MATCH) + tgt * HEAD_MATCH, 0, 1))
    gain = float(HEAD_MATCH)
    # the loft between the body ring and the head's neck ring was painted by Meshy without a reference view (pale grey
    # feathers: a light collar in the review viewer); it takes the colours of the head's own neck stub just in front of
    # it, sampled at the same place around the neck (each loft texel shifted along the neck axis into the stub)
    from scipy.spatial import cKDTree as _KD
    loftH = covH & ~eyesH & ~beakH & (partH % 10 == 1)     # neck_fair.py marks the loft vertices (piece 1)
    restH = covH & ~eyesH & ~beakH & ~loftH
    stubH = np.zeros_like(covH)
    if loftH.any():
        ds, _ = _KD(cenH[loftH][::7]).query(cenH[restH])
        stubH[restH] = ds < 0.035
    if loftH.any() and stubH.any():
        # by luminance rank (the loft keeps Meshy's continuous feather pattern; copying stub texels made a patchwork)
        pals = lin(colH[stubH]); pals = pals[np.argsort(pals @ W)]
        ll = lin(colH[loftH]) @ W
        rkl = np.empty(ll.size); rkl[np.argsort(ll)] = (np.arange(ll.size) + 0.5) / ll.size
        cs2 = np.concatenate([np.zeros((1, 3)), np.cumsum(pals, 0)])
        q2 = np.clip((rkl * len(pals)).astype(int), 0, len(pals) - 1)
        w2 = max(1, len(pals) // 40)
        a2, b2 = np.clip(q2 - w2, 0, len(pals)), np.clip(q2 + w2 + 1, 0, len(pals))
        colH[loftH] = encode(np.clip((cs2[b2] - cs2[a2]) / (b2 - a2)[:, None], 0, 1))
    loft_texels = int(loftH.sum())
    Image.fromarray((pad(colH, covH) * 255).astype(np.uint8)).save(T / 'crow_head_basecolor.png')
    nrmH = np.asarray(Image.open(MH / 'texture_urls_0_normal.png').convert('RGB').resize((SH, SH), Image.LANCZOS),
                      np.float32) / 255
    Image.fromarray((pad(nrmH, covH) * 255).astype(np.uint8)).save(T / 'crow_head_normal_1k.png')
    roughH = np.asarray(Image.open(MH / 'texture_urls_0_roughness.png').convert('L').resize((SH, SH), Image.LANCZOS),
                        np.float32) / 255
    roughH = np.where(plumH, 0.82 + 0.4 * (np.clip(roughH, 0.45, 0.7) - 0.45), np.where(beakH, 0.35, np.where(eyesH, 0.15, 0.6)))
    roughH = pad(roughH, covH)
    Image.merge('RGB', [Image.new('L', (SH, SH), 255), Image.fromarray((roughH * 255).astype(np.uint8)),
                        Image.new('L', (SH, SH), 0)]).save(T / 'crow_head_metal_rough_1k.png')
    regionsH = [feather(m, covH) for m in (plumH, beakH, eyesH)]
    RV.write_mask(regionsH, T / 'crow_head_region_mask.png')
    gradedH = RV.load_srgb(T / 'crow_head_basecolor.png', SH)
    rampsH, repH = {k: [] for k in TIERS}, []
    for name, weight in zip(REGIONS[:3], regionsH):
        targets = chroma_targets(gradedH, weight, name)
        fitted, rp = fit_or_empty(gradedH, targets, weight)
        for k in TIERS:
            rampsH[k].append(fitted[k])
        repH.append({'region': name, **{k: v.get('mean_abs_8bit') if isinstance(v, dict) else v for k, v in rp.items()}})
    materials.append({'base': 'CrowHead', 'prefix': 'CrowHead', 'mask': 'crow_head_region_mask.png', 'ramps': rampsH})
    # seam: the body's neck fades into the head's paint over SEAM_FADE (m from the head's neck ring): each body texel
    # there takes the colour of the nearest head texel in 3D, so the speckled body neck meets the smooth head neck
    # without a line (written as crow_basecolor_final.png, which the export uses)
    gpath = T / 'crow_basecolor_graded.png'
    if gpath.exists():
        from scipy.spatial import cKDTree
        g2 = np.asarray(Image.open(gpath).convert('RGB'), np.float32) / 255
        n2 = g2.shape[0]
        tri2b, _, _ = raster(HERE / 'work' / 'uv3d_crow.npz', n2, [])
        cov2 = tri2b >= 0
        cen2 = dbody['xyz'].mean(1)[np.maximum(tri2b, 0)]
        hc = np.array(g['placement']['head_ring_centre'])
        d2 = np.linalg.norm(cen2 - ring_c, axis=-1)
        band = cov2 & (d2 < 0.11)                  # the neck around the ring (ring radius ~5 cm)
        kd = cKDTree(cenH[covH])
        dist, ii = kd.query(cen2[band])
        hcol = colH[covH][ii]
        w = np.clip(1 - dist / SEAM_FADE, 0, 1)
        w = w * w * (3 - 2 * w)
        out = g2.copy()
        # towards the darker of the two per texel: averaging two unrelated feather patterns flattens them to mid grey,
        # which read as a pale band along the join in the review viewer
        out[band] = out[band] * (1 - w[:, None]) + np.minimum(out[band], hcol) * w[:, None]
        Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(T / 'crow_basecolor_final.png')
        head_report_seam = {'texels': int((w > 0.01).sum()), 'fade_m': SEAM_FADE}
    else:
        head_report_seam = None
    head_report = {'fit': repH, 'texels': {'plumage': int(plumH.sum()), 'beak': int(beakH.sum()), 'eyes': int(eyesH.sum())},
                   'seam_lum_body': pb.round(4).tolist(), 'seam_lum_head_before': ph.round(4).tolist(),
                   'seam_gain': gain, 'seam_fade': head_report_seam, 'loft_repainted_texels': loft_texels}
json.dump({'variants': list(TIERS), 'mm9_region_texels': counts, 'report': report, 'head_report': head_report,
           'sources': {k: f'source/{p}' for k, p in TIERS.items()}, 'materials': materials},
          open(T / 'crow_ramps.json', 'w'), indent=1)
prev = np.zeros((S, S, 3))
prev[plumage] = (0.3, 0.3, 0.5)
prev[beak] = (0.9, 0.6, 0.2)
prev[eyes] = (1.0, 0.9, 0.1)
prev[legs] = (0.2, 0.8, 0.5)
(HERE / 'review').mkdir(exist_ok=True)
row = [prev] + [previews[k] for k in TIERS]
Image.fromarray((np.concatenate(row, 1) * 255).astype(np.uint8)).resize((512 * len(row), 512)).save(
    HERE / 'review' / 'crow_texture_classes_tiers.png')
print('COMPOSED', json.dumps({'mm9_texels': counts, 'fit': report, 'head': head_report,
                              'our_texels': {k: int(m.sum()) for k, m in zip(REGIONS, (plumage, beak, eyes, legs))}}))
