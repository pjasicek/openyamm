"""Compose the retextured Wyrm (revision 04: retopology) into the Wyrm project's runtime texture names.

Body set (meshy/body_texture_v2, work/uv3d_v3.npz) and head set (meshy/head_texture_v2, work/head_uv3d_v3.npz).
Same material contract as compose_wyrm.py/compose_head.py: graded base colour (AO), normal, specular/roughness
(R = openyamm_specular_mask), hide/gold region mask and native green/blue/red ramps, material classes.
Head corrections: horns, crest and cheek spikes recoloured by position/part; eyes repainted (yellow iris, dark rim,
vertical slit pupil, user review: the bake was smudged); generated teeth painted ivory.
Head part ids: 0 skin, 1 tongue, 3 cheek spikes, 4 teeth, 5/6 eyes (source ids kept)."""
import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

P = Path(__file__).resolve().parents[2] / 'mm6_drr1_claude'
T = P / 'textures'; N = P.parent / 'mm6_drr1'
sys.path.insert(0, str(P.parent / 'mm6_gob_claude/scripts'))
sys.path.insert(0, str(P.parent / 'claude_shared'))
import compose_textures_v2 as C  # noqa: E402
import region_variants as R  # noqa: E402

PALETTES = {'wyrm_a': 697, 'wyrm_b': 696, 'wyrm_c': 695}
FRAMES = ['drr1wka0', 'drr1wka1', 'drr1wka2', 'drr1wka3', 'drr1wka4']
samples = {k: [[], []] for k in PALETTES}
for frame in FRAMES:
    a = C.load(N / 'native_variants' / f'{frame}_697.png', 'RGBA'); nh, ns, nv = C.hsv(a[..., :3]); alpha = a[..., 3] > .5
    masks = [alpha & (nh > 78) & (a[..., 1] > a[..., 0] + .005) & (a[..., 1] > a[..., 2] + .005),
             alpha & (nh > 12) & (nh < 78) & (ns > .25) & (nv > .05)]
    for k, pid in PALETTES.items():
        rgb = C.load(N / 'native_variants' / f'{frame}_{pid}.png')[..., :3]
        for i, m in enumerate(masks):
            samples[k][i].append(rgb[m])


from scipy.spatial import cKDTree  # noqa: E402
OLD = np.load(Path(__file__).resolve().parents[1] / 'work' / 'old_uv3d.npz')
OLD_TEX = {0: P / 'review/pre_retopo/wyrm_basecolor_graded.png', 1: P / 'review/pre_retopo/wyrm_head_basecolor_graded.png'}
BARY = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1 / 3, 1 / 3, 1 / 3], [.5, .5, 0], [0, .5, .5], [.5, 0, .5]])


def old_reference(slot, xyz, valid):
    """Per texel: fraction of the 8 nearest revision-02 surface samples that were gold / green, and distance."""
    sel = OLD['mat'] == slot
    pts = np.einsum('kj,tjc->tkc', BARY, OLD['xyz'][sel]).reshape(-1, 3)
    uvs = np.einsum('kj,tjc->tkc', BARY, OLD['uv'][sel]).reshape(-1, 2)
    tex = C.load(OLD_TEX[slot]); n = tex.shape[0]
    px = np.clip((uvs[:, 0] * n).astype(int), 0, n - 1); py = np.clip(((1 - uvs[:, 1]) * n).astype(int), 0, n - 1)
    col = tex[py, px]; h, s_, v = C.hsv(col)
    gold = (h > 20) & (h < 80) & (s_ > .25); green = (h >= 80) & (h < 170) & (s_ > .2)
    tree = cKDTree(pts); q = xyz[valid]
    d, idx = tree.query(q, k=8)
    out_g = np.zeros(valid.shape); out_n = np.zeros(valid.shape); out_d = np.full(valid.shape, 9.0)
    out_c = np.zeros(valid.shape + (3,), np.float32)
    out_g[valid] = gold[idx].mean(1); out_n[valid] = green[idx].mean(1); out_d[valid] = d[:, 0]
    out_c[valid] = col[idx].mean(1)
    return out_g, out_n, out_d, out_c


def patch_copy(base, bad, good, max_shift=120):
    """Fill each connected bad component with texels copied from the nearest offset where all are `good`
    (keeps the scale pattern); 2-texel feather; diffusion fill as the fallback. Returns (base, copied, diffused)."""
    lab, n = ndimage.label(bad)
    out = base.copy(); copied = diffused = 0
    offsets = sorted(((dx, dy) for dx in range(-max_shift, max_shift + 1, 3) for dy in range(-max_shift, max_shift + 1, 3)
                      if (dx, dy) != (0, 0)), key=lambda o: o[0] ** 2 + o[1] ** 2)
    for comp in range(1, n + 1):
        ys, xs = np.nonzero(lab == comp)
        dil = ndimage.binary_dilation(lab == comp, iterations=2); rys, rxs = np.nonzero(dil)
        done = False
        for dx, dy in offsets:
            sy, sx = rys + dy, rxs + dx
            if sy.min() < 0 or sx.min() < 0 or sy.max() >= base.shape[0] or sx.max() >= base.shape[1]:
                continue
            if good[sy, sx].all():
                ring = dil[rys, rxs] & ~(lab[rys, rxs] == comp)
                w = np.where(ring, .5, 1.0)[:, None]
                out[rys, rxs] = out[rys, rxs] * (1 - w) + base[sy, sx] * w
                copied += 1; done = True
                break
        if not done:
            region = good | (lab == comp)
            out = C.inpaint(out, lab == comp, region); diffused += 1
    return out, copied, diffused


def compose(uv3d, source, ao_file, prefix, base_size, head):
    D = np.load(P / 'work' / uv3d); part, xyz = C.rasterise(D, tol=0)
    valid = part >= 0; inside = ndimage.binary_erosion(valid, iterations=1)
    _, ix = ndimage.distance_transform_edt(~inside, return_indices=True)
    pad = lambda a: a[tuple(ix)]

    def save(a, name, size=None, nearest=False):
        im = Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + .5))
        if size:
            im = im.resize((size, size), Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS)
        im.save(T / name)

    base = pad(C.load(P / 'meshy' / source / 'texture_urls_0_base_color.png'))
    x, y, z = xyz[..., 0], xyz[..., 1], xyz[..., 2]
    eye = valid & np.isin(part, [5, 6]); mouth = valid & (part == 1); tooth = valid & (part == 4)
    cheek = valid & (part == 3)
    # Reference repair (user review): gold painted where revision 02 was clearly green, and the reverse.
    og, on, od, oc = old_reference(1 if head else 0, xyz, valid)
    patch = valid & (part == 7)
    base[patch] = oc[patch]                       # closed holes: the revision-02 colour at the same point
    # faces moved out of UV overlaps: the colour of the nearest correctly mapped texel in 3D (keeps scale detail)
    moved = valid & (part == 8)
    if moved.any():
        src = valid & ~np.isin(part, [7, 8])
        sy, sx = np.nonzero(src); my, mx = np.nonzero(moved)
        _, k = cKDTree(xyz[sy, sx]).query(xyz[my, mx])
        base[my, mx] = base[sy[k], sx[k]]
    part = np.where(moved, 0, part)               # repainted moved faces then count as ordinary skin
    h0, s0, v0 = C.hsv(base)
    new_gold = valid & (h0 > 20) & (h0 < 80) & (s0 > .25); new_green = valid & (h0 >= 80) & (h0 < 170) & (s0 > .2)
    skin = valid & (part == 0) & (od < .006)
    keep = lambda m, it: ndimage.binary_opening(m, iterations=it) & m
    wrong_gold = keep(skin & new_gold & (on > .85), 1)
    # green->gold only for solid blobs: thin strips are seams/plate lines (they turned into gold streaks)
    wrong_green = keep(skin & new_green & (og > .95), 3)
    lab, n = ndimage.label(wrong_gold); sizes = ndimage.sum(wrong_gold, lab, range(1, n + 1))
    wrong_gold = np.isin(lab, 1 + np.nonzero(sizes >= 12)[0])
    lab, n = ndimage.label(wrong_green); sizes = ndimage.sum(wrong_green, lab, range(1, n + 1))
    wrong_green = np.isin(lab, 1 + np.nonzero(sizes >= 150)[0])
    base, c1, d1 = patch_copy(base, wrong_gold, new_green & ~wrong_green & valid)
    base, c2, d2 = patch_copy(base, wrong_green, new_gold & ~wrong_gold & valid)
    # Islands, per texel and across UV islands: a texel whose 3D surroundings (about 1 cm, 40 nearest surface samples)
    # are almost all the other colour (a green diamond inside the yellow chest plates, gold flecks on green legs).
    # Gold only turns green where revision 02 was not gold, which protects the spines.
    h1, s1, v1 = C.hsv(base)
    body = valid & (part == 0)          # no old-distance limit: the old model had holes where we now have surface
    g1 = body & (h1 > 20) & (h1 < 80) & (s1 > .25); n1 = body & (h1 >= 80) & (h1 < 170) & (s1 > .2)
    ys_, xs_ = np.nonzero(valid)
    sel = slice(None, None, 20)
    tree3 = cKDTree(xyz[ys_[sel], xs_[sel]])
    cls = np.where(g1[ys_[sel], xs_[sel]], 1, np.where(n1[ys_[sel], xs_[sel]], 2, 0))
    cand = g1 | n1; cy_, cx_ = np.nonzero(cand)
    _, nb = tree3.query(xyz[cy_, cx_], k=40)
    gold_frac = (cls[nb] == 1).mean(1); green_frac = (cls[nb] == 2).mean(1)
    island = np.zeros(valid.shape, bool)
    oc_, on_, od_ = og[cy_, cx_], on[cy_, cx_], od[cy_, cx_]
    # lateral leg zone: the old texture had gold flecks there too, so position decides; claws (z < 3 cm) and the
    # midline spine/belly rows stay protected
    legs = (np.abs(x) > .02) & (z > .03) & (z < .2) & (not head)
    # lower lateral legs: no gold belongs there on the Wyrm (belly plates within 3 cm of the midline, claws below 3 cm)
    legs_low = (np.abs(x) > .03) & (z > .03) & (z < .12) & (not head)
    island[cy_, cx_] = ((n1[cy_, cx_] & (gold_frac > .6) & ((oc_ > .3) | (od_ > .006)))
                        | (g1[cy_, cx_] & (green_frac > .6) & (((on_ > .5) & (oc_ < .2)) | legs[cy_, cx_]))
                        | (g1[cy_, cx_] & legs_low[cy_, cx_]))
    # Explicit repaint zones (user review of revision 05; located with gold_faces.py): gold on the upper front of
    # the shoulders and the upper hind thighs, outside the belly-plate edge (|x| > 4.2 cm).
    if not head:
        zones = (np.abs(x) > .042) & (z > .04) & (z < .18) & (((y > -.37) & (y < -.30)) | ((y > -.19) & (y < -.10)))
        island |= g1 & zones
    # size filter, not an opening: flecks are thin UV slivers that an opening erases
    lab, n = ndimage.label(island, structure=np.ones((3, 3)))
    sizes = ndimage.sum(island, lab, range(1, n + 1))
    island = np.isin(lab, 1 + np.nonzero(sizes >= 8)[0])
    base, c3, d3 = patch_copy(base, island & n1, g1 & ~island & valid)
    base, c4, d4 = patch_copy(base, island & g1, n1 & ~island & valid)
    print(prefix, 'islands', int(island.sum()), 'texels', c3 + c4, 'copied', d3 + d4, 'diffused')
    print(prefix, 'repaired gold->green', int(wrong_gold.sum()), 'texels', c1, 'copied', d1, 'diffused;',
          'green->gold', int(wrong_green.sum()), c2, 'copied', d2, 'diffused')
    np.save(Path(__file__).resolve().parents[1] / 'work' / f'{prefix}_repair_mask.npy', wrong_gold | wrong_green)
    if head:
        horns = np.zeros(valid.shape, bool)
        axis = np.array([[.010, -.452, .339], [.016, -.434, .355], [.019, -.422, .370], [.024, -.405, .386],
                         [.025, -.392, .408], [.021, -.379, .433]])
        for sign in [1, -1]:
            curve = axis.copy()
            if sign < 0:
                curve[:, 0] = -curve[:, 0] - .009
            for i, (a, b) in enumerate(zip(curve, curve[1:])):
                d = b - a; t = np.clip(((xyz - a) * d).sum(-1) / (d @ d), 0, 1)
                radius = [.012, .010, .008, .007, .006][i]
                horns |= valid & (np.linalg.norm(xyz - (a + t[..., None] * d), axis=-1) < radius)
        horns &= ~(eye | tooth | mouth)
        crest = valid & (z > .354) & (np.abs(x + .0045) < .010) & (y > -.464) & (y < -.35) & ~horns
        noise = .5 + .5 * np.sin(x * 1743 + y * 1117 + np.sin(z * 1931)) * np.sin(z * 2311 - y * 1307)
        base[horns] = np.stack([.77 + .13 * noise, .82 + .12 * noise, .86 + .11 * noise], -1)[horns]
        lum0 = base @ np.array([.2126, .7152, .0722])
        base[crest | cheek] = ((.60 + .35 * lum0[..., None]) * np.array([.82, .68, .32]))[crest | cheek]
        # teeth: ivory, slightly darker toward the gum
        base[tooth] = (np.array([.90, .86, .74]) * (.88 + .12 * noise[..., None]))[tooth]
        # eyes: whole repaint per eye (iris gradient, dark rim, vertical slit pupil)
        for pid in (5, 6):
            m = valid & (part == pid)
            if not m.any():
                continue
            cy, cz = float(y[m].mean()), float(z[m].mean())
            ry, rz = max(float(np.ptp(y[m])) / 2, 1e-4), max(float(np.ptp(z[m])) / 2, 1e-4)
            dy, dz = (y - cy) / ry, (z - cz) / rz
            rr = np.sqrt(dy ** 2 + dz ** 2)
            iris = (np.array([.95, .86, .22])[None, None] * (1 - rr[..., None] * .45)
                    + np.array([.30, .42, .05])[None, None] * rr[..., None] * .45)
            rim = np.clip((rr - .72) / .2, 0, 1)[..., None]
            col = iris * (1 - rim) + np.array([.06, .08, .03]) * rim
            pupil = (np.abs(dy) < .16 * np.sqrt(np.clip(1 - dz ** 2, 0, 1))) & (rr < .8)
            col[pupil] = (.02, .02, .015)
            base[m] = col[m]
    h, s, v = C.hsv(base)
    neutral = valid & (((s < .25) & (v > .42)) | ((h > 170) & (h < 290))) & ~eye & ~mouth & ~tooth
    gold = valid & (h > 20) & (h < 80) & (s > .25) & ~eye & ~mouth & ~tooth & ~neutral
    hide = valid & ~(eye | mouth | tooth | neutral | gold)
    classes = np.zeros(valid.shape, np.uint8); classes[valid] = 1; classes[gold] = 4; classes[neutral] = 4
    classes[tooth] = 5; classes[mouth] = 7; classes[eye] = 6
    save(pad(classes) / 255, f'{prefix}_material_classes.png', 1024, True)
    save(base, f'{prefix}_basecolor.png')
    ao = pad(C.load(T / ao_file, 'L'))
    graded = np.clip(base * (1 - .45 * (1 - ndimage.gaussian_filter(ao, 2)))[..., None], 0, 1)
    graded[eye | tooth] = base[eye | tooth]          # painted parts: no AO darkening
    save(graded, f'{prefix}_basecolor_graded.png', base_size)
    save(pad(C.load(P / 'meshy' / source / 'texture_urls_0_normal.png')), f'{prefix}_normal_1k.png', 1024)
    rough = np.full(valid.shape, .83); rough[gold] = .72; rough[neutral] = .48; rough[tooth] = .42
    rough[eye] = .20; rough[mouth] = .65
    spec = np.full(valid.shape, .08); spec[gold] = .12; spec[neutral] = .35; spec[tooth] = .45; spec[eye] = .65
    save(pad(np.stack([spec, rough, np.zeros_like(rough)], -1)), f'{prefix}_metal_rough_1k.png', 1024)
    weights = []
    for mask in [hide, gold]:
        im = Image.fromarray(np.uint8(pad(mask) * 255)).filter(ImageFilter.GaussianBlur(.6)).resize(
            (1024, 1024), Image.Resampling.LANCZOS)
        weights.append(np.asarray(im, dtype=float) / 255)
    R.write_mask(weights, T / f'{prefix}_region_mask.png')
    base1 = R.load_srgb(T / f'{prefix}_basecolor_graded.png', 1024)
    lum = R.srgb_to_linear(base1) @ np.array([.2126, .7152, .0722])
    ramps = {k: [] for k in PALETTES}; report = []
    for region, w in enumerate(weights):
        core = w > .8; targets = {}
        assert core.sum() > 100
        for tier in PALETTES:
            native = R.srgb_to_linear(np.concatenate(samples[tier][region]))
            nl = native @ np.array([.2126, .7152, .0722]); order = np.argsort(nl)
            middle = native[order[int(len(order) * .15):int(len(order) * .95)]]
            gain = middle.mean(0) / max(float(lum[core].mean()), 1e-5) * 1.5
            linear = np.clip(lum[..., None] * gain, 0, 1)
            targets[tier] = np.where(linear <= .0031308, 12.92 * linear, 1.055 * linear ** (1 / 2.4) - .055)
        fitted, rep = R.fit_ramps(base1, targets, w)
        for tier in PALETTES:
            ramps[tier].append(fitted[tier])
        report.append(rep)
    return ramps, report, {str(i): int((classes == i).sum()) for i in np.unique(classes)}


body_ramps, body_rep, body_classes = compose('uv3d_v3.npz', 'body_texture_v2', 'wyrm_ao_v3_2k.png', 'wyrm', None, False)
head_ramps, head_rep, head_classes = compose('head_uv3d_v3.npz', 'head_texture_v2', 'wyrm_head_ao_v3_2k.png',
                                             'wyrm_head', 1024, True)
(T / 'wyrm_ramps.json').write_text(json.dumps({
    'variants': list(PALETTES), 'palettes': PALETTES, 'report': {'body': body_rep, 'head': head_rep},
    'materials': [{'base': 'Wyrm', 'prefix': 'Wyrm', 'mask': 'wyrm_region_mask.png', 'ramps': body_ramps},
                  {'base': 'WyrmHead', 'prefix': 'WyrmHead', 'mask': 'wyrm_head_region_mask.png',
                   'ramps': head_ramps}]}, indent=2) + '\n')
(P / 'checks/materials_v4.json').write_text(json.dumps({'body_classes': body_classes, 'head_classes': head_classes},
                                                       indent=2) + '\n')
print('COMPOSED body', body_rep, 'head', head_rep)
