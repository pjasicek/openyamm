#!/usr/bin/env python3
"""Body texture set of the 45 % peasant (mm6_pfem_claude/scripts/compose_textures_v2.py with this project's paths:
RETEX_JOB=retexture_r45, TEXOUT=textures_r45; work/uv3d.npz holds the body set only, so the head-part repairs find
nothing to do here and the head set is composed by compose_head_r45.py).

Original notes:

- Per-part colour repair: skin-coloured texels on the hair and hair-coloured texels on face/neck skin are
  inpainted from their correctly coloured neighbours inside the same part (retexture projection spill).
- Procedural knife (wood grip, iron guard, steel blade); metallic forced to zero on skin/cloth/hair.
- B/C skins: green garment texels mapped through affine fits of the original palettes 786 -> 787 / 788.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
PAL = ROOT.parent / 'new_sorpigal_3d_stage1_20261006/pfem/source/palettes'
import os
SRC = ROOT / 'meshy' / os.environ.get('RETEX_JOB', 'retexture_r45') / 'texture_urls_0'
OUT = ROOT / os.environ.get('TEXOUT', 'textures_r45')
SIZE = 2048


def load(path, mode='RGB'):
    return np.asarray(Image.open(path).convert(mode), dtype=np.float32) / 255.0


def rasterise(data, tol=0.03, values=None):
    uv, xyz, part = data['uv'], data['xyz'], data['part']
    values = part if values is None else values
    part_map = np.full((SIZE, SIZE), -1, dtype=np.int32)
    xyz_map = np.zeros((SIZE, SIZE, 3), dtype=np.float32)
    for t in range(len(uv)):
        p = uv[t] * SIZE
        p[:, 1] = SIZE - p[:, 1]
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, SIZE - 1), min(y1, SIZE - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / d
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= -tol) & (w1 >= -tol) & (w2 >= -tol)
        ys, xs = np.nonzero(inside)
        part_map[y0 + ys, x0 + xs] = values[t]
        xyz_map[y0 + ys, x0 + xs] = (w0[inside, None] * xyz[t][0] + w1[inside, None] * xyz[t][1]
                                     + w2[inside, None] * xyz[t][2])
    return part_map, xyz_map


def hsv(rgb):
    mx = rgb.max(-1); mn = rgb.min(-1); delta = mx - mn
    sat = np.where(mx > 1e-4, delta / np.maximum(mx, 1e-4), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    safe = np.maximum(delta, 1e-5)
    h = np.where(mx == r, ((g - b) / safe) % 6, np.where(mx == g, (b - r) / safe + 2, (r - g) / safe + 4)) * 60
    return np.where(delta > 1e-5, h, 0), sat, mx


def inpaint(img, bad, region, iterations=400, keep_detail=True):
    """Diffuse good texels of `region` into `bad` texels (bad must lie inside region)."""
    out = img.copy()
    known = region & ~bad
    out[~known] = 0
    weight = known.astype(np.float32)
    kernel = np.array([[0.5, 1, 0.5], [1, 0, 1], [0.5, 1, 0.5]], dtype=np.float32)
    for _ in range(iterations):
        todo = bad & (weight == 0)
        if not todo.any():
            break
        acc = np.stack([ndimage.convolve(out[..., c] * weight, kernel, mode='constant') for c in range(3)], -1)
        wsum = ndimage.convolve(weight, kernel, mode='constant')
        fill = todo & (wsum > 0) & region
        out[fill] = acc[fill] / wsum[fill, None]
        weight[fill] = 1.0
    # keep a little of the original luminance variation so the patch does not look flat
    lum_old = img.mean(-1, keepdims=True); lum_new = out.mean(-1, keepdims=True)
    detail = np.clip(lum_old / np.maximum(lum_new, 1e-3), 0.85, 1.15) if keep_detail else np.ones_like(lum_old)
    out[bad] = np.clip(out[bad] * detail[bad], 0, 1)
    res = img.copy(); res[bad] = out[bad]
    return res


def fill3d(img, bad, good, xyz, k=16, keep_detail=True):
    """Surface-space repair: each bad texel takes the mean of its k nearest good texels in 3D. UV-space inpaint
    leaves small islands that are bad throughout black (no good neighbour in their island)."""
    from scipy.spatial import cKDTree
    out = img.copy()
    gy, gx = np.nonzero(good & ~bad); by, bx = np.nonzero(bad)
    if not len(by) or not len(gy):
        return out
    sel = np.random.default_rng(5).choice(len(gy), min(len(gy), 200000), replace=False)
    _, nn = cKDTree(xyz[gy[sel], gx[sel]]).query(xyz[by, bx], k=k)
    fill = img[gy[sel][nn], gx[sel][nn]].mean(1)
    if keep_detail:
        lum = img[by, bx].mean(-1, keepdims=True); flum = fill.mean(-1, keepdims=True)
        fill = fill * np.clip(lum / np.maximum(flum, 1e-3), 0.9, 1.1)
    out[by, bx] = np.clip(fill, 0, 1)
    return out


def palette(pid):
    raw = (PAL / f'pal{pid}.act').read_bytes()
    return np.array([tuple(raw[i * 3:i * 3 + 3]) for i in range(256)], dtype=np.float32) / 255.0


def fit_palette(target):
    src = palette(786); dst = palette(target)
    differ = np.abs(src - dst).sum(1) > 0.02
    M, *_ = np.linalg.lstsq(np.c_[src[differ], np.ones(differ.sum())], dst[differ], rcond=None)
    return M


def main():
    OUT.mkdir(exist_ok=True)
    data = np.load(ROOT / 'work/uv3d.npz')
    parts = [str(p) for p in data['parts']]
    P = {n: i for i, n in enumerate(parts)}
    part_map, xyz = rasterise(data)
    strict, _ = rasterise(data, tol=0.0)
    interior = ndimage.binary_erosion(strict >= 0, iterations=2)
    _, (iy, ix) = ndimage.distance_transform_edt(~interior, return_indices=True)

    def pad(arr):
        """Replace island borders and margins by the nearest clean interior texel (Meshy edges bleed)."""
        out = arr[iy, ix]
        out[interior] = arr[interior]
        return out
    base = pad(load(str(SRC) + '_base_color.png'))
    normal = pad(load(str(SRC) + '_normal.png'))
    rough = pad(load(str(SRC) + '_roughness.png', 'L'))
    metal = pad(load(str(SRC) + '_metallic.png', 'L'))
    h, s, v = hsv(base)
    z = xyz[..., 2]; y = xyz[..., 1]
    skin_like = (h > 8) & (h < 38) & (s > 0.18) & (s < 0.55) & (v > 0.62)
    hair_like = (h > 5) & (h < 40) & (s > 0.45) & (v < 0.62)
    hair = (part_map == P['Hair']) | (part_map == P['Braid'])
    body = part_map == P['Body']
    from scipy.spatial import cKDTree
    tri_xyz = data['xyz']; tri_part = data['part']
    body_pts = tri_xyz[tri_part == P['Body']].reshape(-1, 3)
    hair_idx = np.nonzero(part_map == P['Hair'])
    dist, _ = cKDTree(body_pts).query(xyz[hair_idx], k=1)
    near_skin = np.zeros(part_map.shape, bool); near_skin[hair_idx] = dist < 0.007
    bad_hair = (ndimage.binary_dilation(hair & skin_like, iterations=2) & hair) | near_skin
    face_neck = body & (z > 1.27) & (z < 1.47) & (y < 0.06)
    bad_skin = ndimage.binary_dilation(face_neck & hair_like & (z < 1.42), iterations=2) & face_neck & (z < 1.42)
    fixed = inpaint(base, bad_hair, hair)
    fixed = inpaint(fixed, bad_skin, body & (z > 1.2) & (z < 1.47))
    # r45: the back view projected the hanging braid onto the nape skin (dark patch under the braid); the nape is
    # head-set skin above the seam and body skin below it, so the body side is repaired here
    # (a wider region took in the dress straps and painted them skin; keep it to the bare nape)
    nape = body & (z > 1.24) & (z < 1.42) & (y > -0.01) & (np.abs(xyz[..., 0]) < 0.09)
    nh, ns, nv = hsv(fixed)
    nape_skin = nape & (nh > 6) & (nh < 40) & (ns > 0.15) & (ns < 0.6) & (nv > 0.55)
    garment = nape & (((nh > 60) & (nh < 180) & (ns > 0.15)) | ((ns < 0.12) & (nv > 0.75)))
    nape_bad = nape & ~nape_skin & ~garment & (nv < np.median(nv[nape_skin]) * 0.85)
    nape_bad = ndimage.binary_dilation(nape_bad, iterations=2) & nape
    fixed = fill3d(fixed, nape_bad, nape_skin & ~nape_bad, xyz, keep_detail=False)
    bad_skin = bad_skin | nape_bad
    # Neck: projected reference chin shadow lands as jagged dark blotches; lift them to the local skin tone.
    x = xyz[..., 0]
    neck = body & (z > 1.32) & (z < 1.405) & (y < 0.02) & (np.abs(x) < 0.07)
    lum = fixed.mean(-1)
    med = np.median(fixed[neck], axis=0); med_l = med.mean()
    dark = neck & (lum < med_l * 0.985)
    k = np.clip((med_l * 1.0 - lum) / (med_l * 0.12), 0, 1)[..., None]
    fixed = np.where(dark[..., None], fixed * (1 - k) + med * k, fixed)
    # Skirt: reference hands hanging beside the skirt were projected into the white cloth; inpaint them.
    skirt = part_map == P['Skirt']
    hs, ss, vs = hsv(fixed)
    green_band = skirt & (hs > 65) & (hs < 175) & (ss > 0.25) & (z < 0.445)   # hem bands end at 0.445 m
    lum = fixed.mean(-1)
    cloth = skirt & ~ndimage.binary_dilation(green_band, iterations=3)
    local = np.zeros_like(lum)
    zbins = np.clip(((z - 0.15) / 0.02).astype(int), 0, 60)
    for b in np.unique(zbins[cloth]):
        sel = cloth & (zbins == b)
        local[sel] = np.median(lum[sel])
    sides = np.abs(xyz[..., 0]) > 0.10
    stains = cloth & ((sides & (lum < local - 0.13)) | ((hs > 15) & (hs < 45) & (ss > 0.25))
                      | ((z >= 0.445) & (hs > 60) & (hs < 180) & (ss > 0.12)))
    stains = ndimage.binary_closing(stains, iterations=2)
    stains = ndimage.binary_dilation(stains, iterations=4) & cloth
    fixed = inpaint(fixed, stains, cloth, keep_detail=False)
    # grey streaks crossing the hem bands: neither band green nor stripe white
    band_zone = skirt & (z < 0.445)
    grey = band_zone & (ss < 0.22) & (lum > 0.30) & (lum < 0.70)
    grey = ndimage.binary_dilation(ndimage.binary_opening(grey, iterations=1), iterations=3) & band_zone
    fixed = inpaint(fixed, grey, band_zone, keep_detail=False)
    stains |= grey
    normal = np.where(stains[..., None], normal * 0.0 + np.array([0.5, 0.5, 1.0]), normal)
    report_skirt = {'skirt_stain_texels': int(stains.sum())}
    # UV-overlap repairs: moved hidden copies (1) and their formerly shared visible partners (2) take the
    # colour of the nearest clean skin texels in 3D.
    if 'uvfix' in data.files:
        fixmap, _ = rasterise(data, values=data['uvfix'])
        need = body & (fixmap > 0)
        clean = body & (fixmap <= 0) & ~need
        cy, cx = np.nonzero(clean)
        sel = np.random.default_rng(1).choice(len(cy), min(len(cy), 400000), replace=False)
        tree = cKDTree(xyz[cy[sel], cx[sel]])
        ny, nx = np.nonzero(need)
        _, nn = tree.query(xyz[ny, nx], k=12)
        fixed[ny, nx] = fixed[cy[sel][nn], cx[sel][nn]].mean(1)
        normal[need] = (0.5, 0.5, 1.0)
        rough[need] = np.median(rough[clean])
        report_fix = {'uvfix_texels': int(need.sum())}
    else:
        report_fix = {}
    # Neck seam: blend skin across the head/torso UV seam by smoothing in 3D (5 mm voxels, 3x3x3 neighbourhood).
    band = body & (z > 1.24) & (z < 1.415) & (y < 0.05) & (np.abs(x) < 0.13)
    pts3 = xyz[band]; cols = fixed[band]
    vox = np.floor(pts3 / 0.005).astype(np.int64)
    keys, inv = np.unique(vox, axis=0, return_inverse=True); inv = inv.ravel()
    sums = np.zeros((len(keys), 3)); cnt = np.zeros(len(keys))
    np.add.at(sums, inv, cols); np.add.at(cnt, inv, 1)
    index = {tuple(k): i for i, k in enumerate(keys)}
    acc = np.zeros_like(sums); acc_n = np.zeros_like(cnt)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                nb = [index.get((k[0] + dx, k[1] + dy, k[2] + dz), -1) for k in keys]
                nb = np.array(nb); ok = nb >= 0
                acc[ok] += sums[nb[ok]]; acc_n[ok] += cnt[nb[ok]]
    smooth = acc[inv] / acc_n[inv, None]
    edge_w = np.clip(np.minimum((pts3[:, 2] - 1.24) / 0.02, (1.415 - pts3[:, 2]) / 0.02), 0, 1)[:, None] * 0.75
    fixed[band] = cols * (1 - edge_w) + smooth * edge_w
    # Eyes: the Meshy eyeball shells were removed (face_repair.py); erase Meshy's offset painted eyes from the
    # skin and paint a clean almond eye centred on each socket, in the frontal (x, z) plane.
    eyes = json.loads(str(data['eyes'])) if 'eyes' in data.files else {}
    for eye in eyes.values():
        cx, cy, cz = eye['centre']
        side = 1.0 if cx > -0.0075 else -1.0                 # outward direction (character left = +x)
        du = (xyz[..., 0] - cx) * side; dv = xyz[..., 2] - cz
        front = body & (xyz[..., 1] < cy + 0.02)
        erase = front & ((du / 0.020) ** 2 + (dv / 0.013) ** 2 < 1.0)
        ring = front & ~erase & ((du / 0.030) ** 2 + (dv / 0.020) ** 2 < 1.0)
        fixed = inpaint(fixed, erase, erase | ring, keep_detail=False)
        lid = erase & ~((du / 0.0125) ** 2 + (dv / 0.0055) ** 2 < 1.0)
        shade = np.clip(1 - ((du / 0.020) ** 2 + (dv / 0.013) ** 2), 0, 1)[..., None]
        fixed = np.where(lid[..., None], fixed * (1 - 0.10 * shade), fixed)
        a_w = 0.0118                                         # half width of the opening
        dv_t = dv - 0.08 * du                                # outer corner slightly raised
        t = np.clip(1 - (du / a_w) ** 2, 0, 1)
        up = 0.0048 * t ** 0.75; lo = -0.0034 * t ** 0.95
        inside = front & (np.abs(du) < a_w) & (dv_t < up) & (dv_t > lo)
        r = np.hypot(du + 0.0006, dv - 0.0004)
        sclera = np.array([0.80, 0.76, 0.72]); iris_c = np.array([0.36, 0.42, 0.32]); pupil = np.array([0.04, 0.04, 0.04])
        col = np.where((r < 0.0016)[..., None], pupil,
              np.where((r < 0.0047)[..., None], iris_c * (0.7 + 0.3 * (r / 0.0047))[..., None],
              np.where((r < 0.0052)[..., None], iris_c * 0.55, sclera)))
        lid_shadow = np.clip((dv_t - (up - 0.0022)) / 0.0022, 0, 1)[..., None]
        col = col * (1 - 0.35 * lid_shadow)
        edge = np.clip(np.minimum(up - dv_t, dv_t - lo) / 0.0005, 0, 1)[..., None]
        fixed = np.where(inside[..., None], fixed * (1 - edge) + col * edge, fixed)
        lash = front & (np.abs(du) < a_w * 1.08) & (np.abs(dv_t - up - 0.0004) < 0.0007 + 0.0003 * t)
        fixed = np.where(lash[..., None], fixed * 0.25 + np.array([0.12, 0.07, 0.05]) * 0.75, fixed)
        lower = front & (np.abs(du) < a_w * 0.9) & (np.abs(dv_t - lo + 0.0003) < 0.0004)
        fixed = np.where(lower[..., None], fixed * 0.75, fixed)
        rough[inside] = 0.25
    # Lips: soft shading instead of a painted line; slightly richer lip colour.
    mx_ = xyz[..., 0] + 0.0075
    mouth = body & (np.abs(mx_) < 0.024) & (xyz[..., 1] < -0.06) & (np.abs(xyz[..., 2] - 1.411) < 0.012)
    seam_z = 1.4105 + 0.004 * (mx_ / 0.020) ** 2
    fall = np.exp(-((xyz[..., 2] - seam_z) / 0.0011) ** 2) * np.clip(1 - (np.abs(mx_) / 0.022) ** 4, 0, 1)
    corner = np.exp(-((np.abs(mx_) - 0.019) / 0.0025) ** 2 - ((xyz[..., 2] - seam_z) / 0.002) ** 2)
    k = (0.20 * fall + 0.18 * corner)[..., None]
    fixed = np.where(mouth[..., None], fixed * (1 - k), fixed)
    lip_h, lip_s, lip_v = hsv(fixed)
    lips = mouth & ((lip_h < 14) | (lip_h > 340)) & (lip_s > 0.32)
    lips = ndimage.gaussian_filter(lips.astype(np.float32), 2.0)[..., None]
    fixed = np.where(mouth[..., None], fixed * (1 - 0.12 * lips) + fixed * np.array([1.06, 0.93, 0.93]) * 0.12 * lips, fixed)
    # Headband: Meshy painted the reference circlet onto the hair/forehead; remove cream texels there.
    hb_h, hb_s, hb_v = hsv(fixed)
    cream_hair = hair & (hb_v > 0.62) & (hb_s < 0.45)
    fixed = inpaint(fixed, ndimage.binary_dilation(cream_hair, iterations=2) & hair, hair, keep_detail=False)
    forehead = body & (xyz[..., 2] > 1.485) & (xyz[..., 1] < 0.0)
    cream_skin = forehead & (hb_v > 0.85) & (hb_s < 0.25)
    fixed = inpaint(fixed, ndimage.binary_dilation(cream_skin, iterations=2) & forehead, forehead, keep_detail=False)
    face_ref = body & (xyz[..., 2] > 1.44) & (xyz[..., 2] < 1.48) & (xyz[..., 1] < -0.05)
    strip = body & (xyz[..., 2] > 1.478) & (xyz[..., 1] < 0.0)
    gain = np.median(fixed[face_ref].mean(-1)) / max(np.median(fixed[strip].mean(-1)), 1e-3)
    ramp = np.clip((xyz[..., 2] - 1.478) / 0.01, 0, 1)[..., None]
    fixed = np.where(strip[..., None], fixed * (1 + (min(gain, 1.0) - 1) * ramp), fixed)
    # Ponytail (braid_v2.py geometry): hair colour with fine strands running along each strip (UV v = image y),
    # a darker wrapped tie; plait relief and contact shading come from geometry and the AO bake.
    braid = part_map == P['Braid']
    hair_clean = (part_map == P['Hair']) & ~bad_hair
    hair_col = np.median(fixed[hair_clean], axis=0)
    braid_info = json.loads(str(data['braid'])) if 'braid' in data.files else {'z_tie': 1.334, 'z_tie_bottom': 1.322}
    rng = np.random.default_rng(7)
    streak = ndimage.gaussian_filter(rng.standard_normal((SIZE, SIZE)).astype(np.float32), sigma=(10.0, 0.9))
    streak /= max(float(np.abs(streak[braid]).max()) if braid.any() else 1.0, 1e-6)
    lum = 0.92 + 0.16 * streak
    col = np.clip(hair_col[None, None, :] * lum[..., None], 0, 1)
    bz = xyz[..., 2]
    tie = braid & (bz > braid_info['z_tie_bottom'] - 0.0025) & (bz < braid_info['z_tie'] + 0.0025)
    col = np.where(tie[..., None], hair_col * 0.62, col)
    fixed = np.where(braid[..., None], col, fixed)
    normal[braid] = (0.5, 0.5, 1.0); rough[braid] = 0.62
    # Headband: thin brass circlet.
    band = part_map == P['Headband']
    fixed[band] = (0.78, 0.64, 0.38); rough[band] = 0.35; metal[band] = 0.85; normal[band] = (0.5, 0.5, 1.0)
    report_extra = {'neck_lifted_texels': int(dark.sum()), 'hair_edge_texels': int(near_skin.sum())}
    rough_out = rough.copy(); metal_out = metal.copy()
    metal_out[band] = 0.85
    knife = part_map == P['Knife']
    along = ((xyz - data['grip']) * data['blade']).sum(-1)
    for mask, rgb, r, m in ((knife & (along < 0.049), (0.28, 0.17, 0.10), 0.75, 0.0),
                            (knife & (along >= 0.049) & (along < 0.061), (0.30, 0.30, 0.32), 0.45, 0.85),
                            (knife & (along >= 0.061), (0.70, 0.71, 0.73), 0.28, 1.0)):
        fixed[mask] = rgb; rough_out[mask] = r; metal_out[mask] = m; normal[mask] = (0.5, 0.5, 1.0)
    for name in ('Body', 'Skirt', 'Hair', 'Braid', 'LegLeft', 'LegRight', 'Belt'):
        metal_out[part_map == P[name]] = 0.0
    eyes_mask = (part_map == P['EyeLeft']) | (part_map == P['EyeRight'])
    rough_out[eyes_mask] = 0.2; metal_out[eyes_mask] = 0.0

    def save(arr, name):
        Image.fromarray(np.clip(arr * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / name, optimize=True)

    # Material roughness (glTF G channel) by part and colour class, and baked ambient occlusion in base colour.
    hh, ss_, vv = hsv(fixed)
    skin_c = (hh > 5) & (hh < 40) & (ss_ > 0.18) & (ss_ < 0.65) & (vv > 0.45)
    green_c = (hh > 65) & (hh < 180) & (ss_ > 0.15)
    linen_c = (ss_ < 0.18) & (vv > 0.55)
    legs = (part_map == P['LegLeft']) | (part_map == P['LegRight'])
    rough_out = np.where(body & skin_c, 0.52, rough_out)
    rough_out = np.where((body | skirt) & green_c, 0.86, rough_out)
    rough_out = np.where((body | skirt) & linen_c, 0.93, rough_out)
    rough_out = np.where(hair, 0.58, rough_out)
    rough_out = np.where(braid, 0.62, rough_out)
    rough_out = np.where(part_map == P['Belt'], 0.55, rough_out)
    rough_out = np.where(legs & (vv < 0.45), 0.55, rough_out)
    lips_mask = mouth & (lips[..., 0] > 0.3)
    rough_out = np.where(lips_mask, 0.40, rough_out)
    buckle = part_map == P['Buckle']
    rough_out[buckle] = 0.35; metal_out[buckle] = 0.85; fixed[buckle] = np.clip(fixed[buckle] * 1.1, 0, 1)
    rough_out[eyes_mask] = 0.2
    ao = np.asarray(Image.open(ROOT / 'work/ao.png').convert('L'), dtype=np.float32) / 255.0
    ao = pad(np.repeat(ao[..., None], 3, -1))[..., 0]
    ao_k = np.where(body & skin_c, 0.45, np.where(braid, 0.40, 0.55))
    ao_k = np.where(eyes_mask | (part_map == P['Headband']) | (part_map == P['Knife']), 0.0, ao_k)
    # r45: no AO on the nape skin; the rest-pose braid/hair shell darkened a square there that the swinging braid
    # does not justify (the installed model's nape was in the AO-free head set)
    # (a hard no-AO region left a pale band; the nape now fades to a third of the AO with a floor on its darkness)
    nape_fade = np.clip(np.minimum.reduce([(z - 1.22) / 0.04, (y + 0.03) / 0.04, (0.12 - np.abs(xyz[..., 0])) / 0.04]), 0, 1)
    ao_k = np.where(body, ao_k * (1 - 0.65 * nape_fade), ao_k)
    ao = np.where(body & (nape_fade > 0), np.maximum(ao, 0.55), ao)
    # round 2: the rest-pose fingers touch, so the bake darkened a spot between them that showed in the clasp
    hands = body & (np.abs(xyz[..., 0]) > 0.33) & (z < 1.05)
    ao_k = np.where(hands, 0.12, ao_k)
    fixed = fixed * (1 - ao_k[..., None] * (1 - np.clip(ao, 0, 1) ** 0.8)[..., None])
    # dark hand texels left by Meshy between the fingers (lum below 70 % of the hand's median) take nearby hand skin
    hl = fixed.mean(-1); hmed = np.median(hl[hands])
    dark_hand = ndimage.binary_dilation(hands & (hl < hmed * 0.7), iterations=2) & hands
    fixed = fill3d(fixed, dark_hand, hands & ~dark_hand, xyz)
    report_extra['dark_hand_texels'] = int(dark_hand.sum())
    fixed = pad(fixed)
    save(fixed, 'pfem_a_basecolor.png')
    save(normal, 'pfem_normal.png')
    save(np.stack([np.ones_like(rough_out), rough_out, metal_out], -1), 'pfem_metal_rough.png')
    hf, sf, vf = hsv(fixed)
    garment = ((part_map == P['Body']) | (part_map == P['Skirt'])) & (hf > 65) & (hf < 175) & (sf > 0.12)
    w = (garment * np.clip((sf - 0.10) / 0.12, 0, 1))[..., None]
    report = {'repaired_hair_texels': int(bad_hair.sum()), 'repaired_skin_texels': int(bad_skin.sum()),
              'garment_texels': int(garment.sum()), **report_extra, **report_fix, **report_skirt}
    for skin, pid in (('b', 787), ('c', 788)):
        M = fit_palette(pid)
        mapped = np.clip(np.c_[fixed.reshape(-1, 3), np.ones(SIZE * SIZE)] @ M, 0, 1).reshape(SIZE, SIZE, 3)
        save(fixed * (1 - w) + mapped * w, f'pfem_{skin}_basecolor.png')
    (OUT / 'compose_report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
