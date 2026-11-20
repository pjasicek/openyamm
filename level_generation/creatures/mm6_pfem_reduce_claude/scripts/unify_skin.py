#!/usr/bin/env python3
"""One skin over head and body (user review 2026-10-14: the face read as "a mask over her original skin", jagged
transitions, triangle artifacts). Runs after texture_r45.sh, before runtime_r45.sh.

1. Shared tone: a smooth 3D skin colour field F (1 cm voxels of robust skin samples from both texture sets, toned to
   meet halfway at the neck seam, Gaussian sigma 2 cm) replaces each set's own low frequencies: skin texel = colour x F / L, where L is the texel's own set
   smoothed the same way. Facial features and fine detail stay; head and body meet at one tone.
2. Visible skin only: hair paint stays on skin texels hidden under the hair, braid and circlet (exposure_r45.py: fewer
   than 5 % of the texel's outward rays escape); the round-2 band beside the mesh (rays reaching hair hovering up to
   4 cm in front of the temples) painted brown strips on visible skin. Head skin starts from the graded Meshy head.
3. Per UV island: each island is divided by its own low frequencies, so islands meet at one tone (no split down the
   chin, no forehead edge). Outliers outside the eye/brow/nose/mouth area (hair spill, pale slivers) are filled
   from the nearest good skin in 3D. Outside eyes/brows, nose and mouth only fine detail (Gaussian 4 texels) rides on
   the shared tone, removing Meshy's mid-scale steps (a projection seam across the forehead); painted teeth between
   the lips become mouth shadow. Scalp seen at a grazing angle under the jagged hair edge (within 1.5 cm of the hair,
   exposure < 0.45) takes the nearest hair colour with darker roots, so it reads as hairline, not bald slivers.
4. Normal maps go flat within 2 cm of the head/body seam (3D), fading to the original by 2 cm, and 70 % flat within
   5 texels of the face's UV island borders (mirrored tangent spaces meet there).
Writes textures_r45/pfem_head_basecolor_final.png, pfem_a_basecolor.png (+ _1k), pfem_head_normal_1k.png,
pfem_normal.png and textures_r45/pfem_unify_report.json; the inputs are kept as *_pre_unify.png on the first run."""
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

import compose_r45 as C

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / 'textures_r45'
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
VOXEL, SIGMA = 0.01, 0.02


def keep_input(name):
    src, pre = T / name, T / name.replace('.png', '_pre_unify.png')
    if not pre.exists():
        shutil.copy2(src, pre)
    return pre


def raster(npz, size):
    C.SIZE = size
    data = np.load(npz)
    return C.rasterise(data, tol=0.0)


def field(points, colours):
    """Robust voxel means (per-voxel median), then a Gaussian over voxel centres: returns (centres, smoothed)."""
    keys = np.floor(points / VOXEL).astype(np.int64)
    uniq, inv = np.unique(keys, axis=0, return_inverse=True)
    inv = inv.ravel()
    order = np.argsort(inv)
    bounds = np.r_[0, np.cumsum(np.bincount(inv))]
    med = np.array([np.median(colours[order[bounds[i]:bounds[i + 1]]], axis=0) for i in range(len(uniq))])
    centres = (uniq + .5) * VOXEL
    tree = cKDTree(centres)
    nbrs = tree.query_ball_point(centres, 3 * SIGMA)
    smooth = np.array([np.average(med[n], axis=0, weights=np.exp(-((centres[n] - c) ** 2).sum(1) / (2 * SIGMA ** 2)))
                       for c, n in zip(centres, nbrs)])
    return centres, smooth


def lookup(centres, values, points):
    """Inverse-distance blend of the 8 nearest voxel values (continuous across voxel boundaries)."""
    k = min(8, len(centres))
    d, i = cKDTree(centres).query(points, k=k)
    d, i = d.reshape(len(points), k), i.reshape(len(points), k)
    w = 1.0 / np.maximum(d, 1e-4) ** 2
    return (values[i] * w[..., None]).sum(1) / w.sum(1, keepdims=True)


def island_low(labels, targets, good, xyz, colours):
    """Each UV island's own low frequencies at the target texels (its good samples, field() per island; a constant
    median for small islands). Dividing by these brings every island to the shared tone (a 3D blur across islands left
    a darker island darker: the split down the chin, the forehead edge)."""
    out = np.zeros(targets.shape + (3,), np.float32)
    for lab in np.unique(labels[targets]):
        tgt = targets & (labels == lab); src = good & (labels == lab)
        if src.sum() < 40:
            pool = colours[tgt] if src.sum() == 0 else colours[src]
            out[tgt] = np.median(pool, 0)
            continue
        c, f = field(xyz[src], colours[src])
        out[tgt] = lookup(c, f, xyz[tgt])
    return out


def repad(img, valid, changed):
    """Gutter texels next to changed texels copy their nearest valid texel (mip filtering stays on the new colour)."""
    near = ndimage.binary_dilation(changed, iterations=6) & ~valid
    idx = ndimage.distance_transform_edt(~valid, return_distances=False, return_indices=True)
    out = img.copy()
    out[near] = img[idx[0][near], idx[1][near]]
    return out


def main():
    parts = [str(p) for p in np.load(ROOT / 'work/uv3d_head.npz')['parts']]
    skin_id = parts.index('Body')
    eyes = json.loads(str(np.load(ROOT / 'work/uv3d_head.npz')['eyes']))
    hpart, hxyz = raster(ROOT / 'work/uv3d_head.npz', 1024)
    bpart, bxyz = raster(ROOT / 'work/uv3d.npz', 2048)
    head_final = C.load(keep_input('pfem_head_basecolor_final.png'))
    head_graded = C.load(T / 'pfem_head_basecolor_graded.png')
    body = C.load(keep_input('pfem_a_basecolor.png'))

    hskin = hpart == skin_id
    # visible skin: rays from the texel escape past hair, braid and circlet in >= 5 % of its outer hemisphere
    # (exposure_r45.py); scalp under the hair shell keeps the hair paint
    ex = np.load(ROOT / 'work/exposure_r45.npz')
    idx = ndimage.distance_transform_edt(~ex['sample'], return_distances=False, return_indices=True)
    exposure = ex['exposure'][idx[0], idx[1]]
    hidden = hskin & (exposure < 0.05)
    cover_dist = np.load(ROOT / 'work/hair_cover_r45.npz')['distance']
    hvis = hskin & ~hidden
    h, s, v = C.hsv(body)
    bskin = (bpart == skin_id) & (h > 4) & (h < 40) & (s > 0.12) & (s < 0.7) & (v > 0.35)

    # facial feature zone: eyes/lids/brows, nose, mouth (kept, only re-toned)
    ec = np.array([eyes['EyeLeft']['centre'], eyes['EyeRight']['centre']])
    mid = ec.mean(0); front = min(eyes['EyeLeft']['front_y'], eyes['EyeRight']['front_y'])
    rel = hxyz - mid
    face_zone = hvis & (np.abs(rel[..., 0]) < 0.05) & (rel[..., 2] > -0.085) & (rel[..., 2] < 0.035) \
        & (hxyz[..., 1] < front + 0.03)

    hc = lin(head_graded); bc = lin(body)
    hl, bl = hc @ W, bc @ W
    # robust samples for the fields: skin-coloured texels, not dark/pale outliers
    hh, hs, hv = C.hsv(head_graded)
    hgood = hvis & (hh > 4) & (hh < 40) & (hs > 0.12) & (hs < 0.7) & (hv > 0.35)
    hgood &= ~(face_zone & ((hl < np.median(hl[hgood]) * 0.7) if hgood.any() else False))
    pts_h, col_h = hxyz[hgood], hc[hgood]
    pts_b, col_b = bxyz[bskin], bc[bskin]
    ch, Lh = field(pts_h, col_h)
    cb, Lb = field(pts_b, col_b)
    # one tone: both sets meet halfway at the seam (per channel, medians within 5 cm of the other set), then the
    # shared field is built from the toned samples, so the face is not a different tone with a soft edge
    near_h = cKDTree(pts_b[::8]).query(pts_h)[0] < 0.05
    near_b = cKDTree(pts_h[::4]).query(pts_b)[0] < 0.05
    gain = np.sqrt(np.median(col_b[near_b], 0) / np.maximum(np.median(col_h[near_h], 0), 1e-4))
    cf, F = field(np.concatenate([pts_h, pts_b]), np.concatenate([col_h * gain, col_b / gain]))

    out_head = head_final.copy(); out_body = body.copy()
    hlab, _ = ndimage.label(hskin, structure=np.ones((3, 3)))
    blab, _ = ndimage.label(bpart == skin_id, structure=np.ones((3, 3)))
    # head: per-island ratio transfer on visible skin
    Lisl = island_low(hlab, hvis, hgood, hxyz, hc)
    p = hxyz[hvis]
    Fh = lookup(cf, F, p); Lhh = Lisl[hvis]
    c = hc[hvis]
    ratio = (c @ W) / np.maximum(Lhh @ W, 1e-4)
    hue_far = np.abs(C.hsv(np.clip(srgb(c), 0, 1))[0] - C.hsv(np.clip(srgb(Lhh), 0, 1))[0]) > 14
    zone = face_zone[hvis]
    outlier = ~zone & (((ratio < 0.7) & hue_far) | (ratio > 1.35))
    keep = c * Fh / np.maximum(Lhh, 1e-4)
    # outside the real features only fine detail (~4 texels: pores, freckles) rides on the shared tone; Meshy's
    # mid-scale steps (a projection seam across the forehead, patches) go
    feat = np.zeros(hvis.shape, bool)
    for e in (eyes['EyeLeft']['centre'], eyes['EyeRight']['centre']):
        dx, dz = hxyz[..., 0] - e[0], hxyz[..., 2] - e[2]
        # eye and lids only (a 2.4 cm disc kept a pale Meshy streak running down from an inner corner)
        feat |= (dx ** 2 + (dz * 1.4) ** 2 < 0.017 ** 2) | ((np.abs(dx) < 0.03) & (dz > 0.008) & (dz < 0.032))
    feat |= (np.abs(rel[..., 0]) < 0.016) & (rel[..., 2] > -0.055) & (rel[..., 2] < 0.0)
    # mouth: the lip-coloured texels only (a box reached the chin, which then kept each island's own mid-tones: a
    # split down the chin)
    box = (np.abs(rel[..., 0]) < 0.03) & (rel[..., 2] > -0.08) & (rel[..., 2] < -0.045)
    lips = box & hvis & ((hh < 12) | (hh > 330)) & (hs > 0.25)
    mouth = ndimage.binary_dilation(lips, iterations=4) & box
    feat |= mouth
    feat &= hvis & (hxyz[..., 1] < front + 0.03)
    # features count fully inside their zone and fade out over 12 texels outside it (a Gaussian of the zone diluted a
    # brow on a smaller UV island into the ±10 % skin path: her left brow and eye washed out, user review 2026-10-14)
    soft = np.clip(1 - ndimage.distance_transform_edt(~feat) / 12.0, 0, 1)[hvis][:, None]
    m = hvis.astype(np.float32)
    blur = np.stack([ndimage.gaussian_filter(hc[..., k] * m, 4.0) for k in range(3)], -1) \
        / np.maximum(ndimage.gaussian_filter(m, 4.0), 1e-4)[..., None]
    fine = np.clip(c / np.maximum(blur[hvis], 1e-4), 0.9, 1.1)
    # skin-coloured texels inside a feature zone keep only their brightness ratio, coloured by the shared skin (an
    # island's warmer hue left an orange socket around one eye); iris, lashes, brows and lips keep their own colour
    skinlike = hgood[hvis]
    lum_ratio = np.clip((c @ W) / np.maximum(Lhh @ W, 1e-4), 0.3, 1.6)[:, None]
    keep = np.where(skinlike[:, None], Fh * lum_ratio, keep)
    new = keep * soft + Fh * fine * (1 - soft)
    # Meshy painted teeth between the lips: the pale shape at the mouth corners becomes mouth shadow
    teeth = (mouth & hvis & (hv > 0.7) & (hs < 0.3))[hvis]
    new[teeth] = Fh[teeth] * np.array([0.42, 0.26, 0.24], np.float32)
    head_lin = lin(head_final).astype(np.float32)
    head_lin[hvis] = np.clip(new, 0, 1)
    # outliers (hair spill, pale slivers): filled from the nearest good skin in 3D (UV inpaint left small islands black)
    bad = np.zeros_like(hvis); bad[np.nonzero(hvis)[0][outlier], np.nonzero(hvis)[1][outlier]] = True
    if bad.any():
        head_lin = C.fill3d(head_lin, bad, hvis & ~bad, hxyz)
    # scalp seen at a grazing angle under the jagged hair edge: hair colour (darker roots), weighted by how little
    # of it can be seen and how close the hair is, so the hairline reads as hair instead of bald slivers
    dist = cover_dist
    edge = hvis & ~face_zone & (dist >= 0) & (dist < 0.015) & (exposure < 0.45)
    hair_tex = hpart == parts.index('Hair')
    if edge.any() and hair_tex.any():
        ht = cKDTree(hxyz[hair_tex]); _, nb = ht.query(hxyz[edge], k=8)
        hair_col = lin(head_final)[hair_tex][nb].mean(1) * 0.8
        w = (np.clip((0.45 - exposure[edge]) / 0.35, 0, 1) * np.clip((0.015 - dist[edge]) / 0.007, 0, 1))[:, None]
        head_lin[edge] = head_lin[edge] * (1 - w) + hair_col * w
    out_head = np.clip(srgb(np.clip(head_lin, 0, 1)), 0, 1).astype(np.float32)
    # body skin: same per-island transfer
    Lb_isl = island_low(blab, bskin, bskin, bxyz, bc)
    q = bxyz[bskin]
    Fb = lookup(cf, F, q)
    keep_b = bc[bskin] * Fb / np.maximum(Lb_isl[bskin], 1e-4)
    # neck and upper chest (within 12 cm of the head skin): fine detail only, as the face (round-2 patch fills and
    # Meshy's mid-scale blotches read as pale facets under the chin)
    mb = bskin.astype(np.float32)
    bblur = np.stack([ndimage.gaussian_filter(bc[..., k] * mb, 8.0) for k in range(3)], -1) \
        / np.maximum(ndimage.gaussian_filter(mb, 8.0), 1e-4)[..., None]
    bfine = np.clip(bc[bskin] / np.maximum(bblur[bskin], 1e-4), 0.85, 1.15)
    near_head = np.clip(1 - (cKDTree(hxyz[hvis][::4]).query(q)[0] - 0.08) / 0.04, 0, 1)[:, None]
    out_body[bskin] = np.clip(srgb(np.clip(keep_b * (1 - near_head) + Fb * bfine * near_head, 0, 1)), 0, 1)

    out_head = repad(out_head, hpart >= 0, hvis)
    out_body = repad(out_body, bpart >= 0, bskin)
    Image.fromarray((out_head * 255 + .5).astype(np.uint8)).save(T / 'pfem_head_basecolor_final.png')
    Image.fromarray((out_body * 255 + .5).astype(np.uint8)).save(T / 'pfem_a_basecolor.png')
    Image.fromarray((out_body * 255 + .5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(
        T / 'pfem_a_basecolor_1k.png', optimize=True)

    # normal maps flat near the seam (3D distance from a head skin texel to body skin and the reverse)
    tb, th = cKDTree(bxyz[bskin][::4]), cKDTree(hxyz[hskin][::2])
    for name, part_map, xyz, skin, other in [('pfem_head_normal_1k.png', hpart, hxyz, hskin, tb),
                                              ('pfem_normal.png', bpart, bxyz, bskin, th)]:
        src = keep_input(name)
        nm = C.load(src)
        if nm.shape[0] != part_map.shape[0]:
            raise ValueError(f'{name}: normal map size {nm.shape} does not match its raster {part_map.shape}')
        d, _ = other.query(xyz[skin])
        w = np.clip(1 - d / 0.02, 0, 1)
        if part_map is hpart:
            # face UV island borders: the mirrored halves' tangent spaces meet there; 70 % flat within 5 texels
            border = ndimage.distance_transform_edt(hskin)[skin]
            w = np.maximum(w, 0.7 * np.clip(1 - border / 5.0, 0, 1) * hvis[skin])
        w = w[:, None]
        flat = np.array([0.5, 0.5, 1.0], np.float32)
        nm[skin] = nm[skin] * (1 - w) + flat * w
        nm = repad(nm, part_map >= 0, skin)
        Image.fromarray((np.clip(nm, 0, 1) * 255 + .5).astype(np.uint8)).save(T / name)

    # measurements: tone of the final skin either side of the seam (5 cm band) and of the face vs the neck
    fh, fb = lin(out_head), lin(out_body)
    dh, _ = tb.query(hxyz[hvis]); db, _ = th.query(bxyz[bskin])
    report = {'gain_head_to_shared': gain.round(4).tolist(), 'head_seam_band': np.median(fh[hvis][dh < 0.05], 0).round(4).tolist(),
              'body_seam_band': np.median(fb[bskin][db < 0.05], 0).round(4).tolist(),
              'head_visible_texels': int(hvis.sum()), 'hidden_under_hair': int(hidden.sum()),
              'outliers_repainted': int(outlier.sum()), 'feature_texels': int(feat.sum()), 'teeth_texels': int(teeth.sum()), 'hair_edge_texels': int(edge.sum()), 'face_zone_texels': int(face_zone.sum()),
              'body_skin_texels': int(bskin.sum())}
    (T / 'pfem_unify_report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
