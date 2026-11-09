#!/usr/bin/env python3
"""Head texture set of the 45 % peasant, after claude_shared/compose_head_set.py (grade + luminance seam gain):

1. Colour match: the head-retexture skin was redder and brighter than the body retexture's (user: the head should not
   "fight" the body skin). Per-channel linear gain = median body skin / median head skin, both measured within 5 cm of
   the neck seam in 3D; applied to every head skin texel, so the face keeps its detail but takes the body's tone.
2. Seam blend: head skin within 3 cm above the seam fades toward the local body skin colour (surface-space average
   of the nearest body skin texels), removing any remaining step at the neck.
3. Projection spill: skin-coloured texels on hair/braid and hair-coloured texels on the lower face/neck are inpainted
   from their own part (as compose_textures_v2.py did on the body atlas); the circlet is flat brass.
Writes textures_r45/pfem_head_basecolor_final.png (+ metal-rough with the brass circlet) and pfem_head_match.json."""
import json
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


def raster(npz, size):
    C.SIZE = size
    data = np.load(npz)
    part, xyz = C.rasterise(data, tol=0.0)
    return data, part, xyz


def skin_mask(rgb, part, skin_id):
    h, s, v = C.hsv(rgb)
    return (part == skin_id) & (h > 4) & (h < 40) & (s > 0.15) & (s < 0.65) & (v > 0.45)


def main():
    hdata, hpart, hxyz = raster(ROOT / 'work/uv3d_head.npz', 1024)
    parts = [str(p) for p in hdata['parts']]; P = {n: i for i, n in enumerate(parts)}
    bdata, bpart, bxyz = raster(ROOT / 'work/uv3d.npz', 2048)
    head = C.load(T / 'pfem_head_basecolor_graded.png')
    body = C.load(T / 'pfem_a_basecolor.png')
    hskin = skin_mask(head, hpart, P['Body']); bskin = skin_mask(body, bpart, P['Body'])
    # the seam: head skin's lowest band meets the body; measure both sides within 5 cm in 3D
    skin_pts = hxyz[hpart == P['Body']]
    seam_z = float(np.percentile(skin_pts[:, 2], 1.0))
    hz, bz = hxyz[..., 2], bxyz[..., 2]
    hband = hskin & (hz < seam_z + 0.05) & (hxyz[..., 1] < 0.05)
    bband = bskin & (bz > seam_z - 0.05) & (bz < seam_z + 0.01) & (np.abs(bxyz[..., 0]) < 0.12) & (bxyz[..., 1] < 0.05)
    hmed = np.median(lin(head[hband]), axis=0); bmed = np.median(lin(body[bband]), axis=0)
    full_gain = np.clip(bmed / np.maximum(hmed, 1e-4), 0.6, 1.5)
    # meet halfway: the full match turned the face sallow (the body retexture's skin is yellower); the body skin
    # (neck, chest, arms, hands) takes the other half in pfem_a_basecolor.png, written below
    gain = np.sqrt(full_gain)
    out = head.copy()
    allskin = hpart == P['Body']
    out[allskin] = srgb(np.clip(lin(head[allskin]) * gain, 0, 1))
    bh, bs, bv = C.hsv(body)
    body_skin = (bpart == P['Body']) & (bh > 4) & (bh < 40) & (bs > 0.15) & (bs < 0.65) & (bv > 0.40)
    soft = ndimage.gaussian_filter(body_skin.astype(np.float32), 1.5)[..., None]
    body = np.clip(body * (1 - soft) + srgb(np.clip(lin(body) / gain, 0, 1)) * soft, 0, 1)
    Image.fromarray(np.uint8(body * 255 + 0.5)).save(T / 'pfem_a_basecolor.png', optimize=True)
    bmed = np.median(lin(body[bband]), axis=0)
    # face islands: Meshy's colour differs between UV islands (a visible line down the jaw); the skin's low frequencies
    # (> ~1 cm) come from a 3D surface average instead, high frequencies stay; eyes, brows, nose and lips are protected
    x_, y_, z_ = hxyz[..., 0], hxyz[..., 1], hxyz[..., 2]
    def ellipse(cx, cz, rx, rz):
        dd = np.sqrt(((x_ - cx) / rx) ** 2 + ((z_ - cz) / rz) ** 2)
        return np.clip((1.25 - dd) / 0.25, 0, 1) * (y_ < -0.035)
    eyes = json.loads(str(hdata['eyes']))
    feats = [ellipse(e['centre'][0], e['centre'][2], 0.023, 0.017) for e in eyes.values()]
    feats += [ellipse(-0.0075, 1.411, 0.029, 0.012), ellipse(-0.0075, 1.434, 0.022, 0.012)]
    protect = np.maximum.reduce(feats)
    sy, sx = np.nonzero(allskin)
    pick = np.random.default_rng(3).choice(len(sy), min(len(sy), 60000), replace=False)
    stree = cKDTree(hxyz[sy[pick], sx[pick]])
    smooth3 = np.empty((len(sy), 3), np.float32)
    for a in range(0, len(sy), 8192):
        dd, ii = stree.query(hxyz[sy[a:a + 8192], sx[a:a + 8192]], k=96)
        ww = np.exp(-0.5 * (dd / 0.010) ** 2); ww /= np.maximum(ww.sum(1, keepdims=True), 1e-9)
        smooth3[a:a + 8192] = (out[sy[pick][ii], sx[pick][ii]] * ww[..., None]).sum(1)
    lab, n = ndimage.label(allskin)
    low = np.zeros_like(out)
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        m = (lab[sl] == i).astype(np.float32)
        step = np.linalg.norm(np.diff(hxyz[sl], axis=1), axis=-1)[(lab[sl][:, 1:] == i) & (lab[sl][:, :-1] == i)]
        sigma = float(np.clip(0.010 / max(np.median(step) if step.size else 1e-3, 1e-5), 1.0, 40.0))
        den = ndimage.gaussian_filter(m, sigma)
        for c in range(3):
            low[sl][..., c] = np.where(m > 0, ndimage.gaussian_filter(out[sl][..., c] * m, sigma) / np.maximum(den, 1e-6), 0)
    detail = out[sy, sx] - low[sy, sx]
    keepf = protect[sy, sx][:, None]
    out[sy, sx] = np.clip(out[sy, sx] * keepf + (smooth3 + detail) * (1 - keepf), 0, 1)

    # surface-space blend toward the local body skin, only within 1.5 cm of the seam itself (a height band reached
    # the chin, which overhangs the AO-darkened neck, and turned it yellowish)
    by, bx = np.nonzero(bskin & (bz > seam_z - 0.06) & (bz < seam_z + 0.06))
    tree = cKDTree(bxyz[by, bx])
    cand = allskin & (hz < seam_z + 0.08)
    cy, cx = np.nonzero(cand)
    d0, _ = tree.query(hxyz[cy, cx], k=1)
    seam_pts = hxyz[cy, cx][d0 < 0.004]
    sd, _ = cKDTree(seam_pts).query(hxyz[cy, cx], k=1)
    keep = sd < 0.015
    ny, nx = cy[keep], cx[keep]; near = np.zeros_like(cand); near[ny, nx] = True
    dist, idx = tree.query(hxyz[ny, nx], k=24)
    w = np.exp(-0.5 * (dist / 0.006) ** 2); w /= np.maximum(w.sum(1, keepdims=True), 1e-9)
    local = (body[by[idx], bx[idx]] * w[..., None]).sum(1)
    t = np.clip(1 - sd[keep] / 0.015, 0, 1)[:, None] * 0.85
    detail = out[ny, nx] - ndimage.gaussian_filter(out, (2, 2, 0))[ny, nx]
    out[ny, nx] = np.clip(out[ny, nx] * (1 - t) + (local + 0.5 * detail) * t, 0, 1)
    # projection spill
    hair = (hpart == P['Hair']) | (hpart == P['Braid'])
    h, s, v = C.hsv(out)
    skin_like = (h > 8) & (h < 38) & (s > 0.18) & (s < 0.55) & (v > 0.62)
    hair_like = (h > 5) & (h < 40) & (s > 0.45) & (v < 0.62)
    bad_hair = ndimage.binary_dilation(hair & skin_like, iterations=2) & hair
    out = C.fill3d(out, bad_hair, hair & ~bad_hair, hxyz)
    face_low = allskin & (hz < 1.42) & (hxyz[..., 1] < 0.06)
    bad_skin = ndimage.binary_dilation(face_low & hair_like, iterations=2) & face_low
    out = C.fill3d(out, bad_skin, allskin & ~bad_skin, hxyz)
    # circlet bleed: pale cream texels on the forehead skin under the band; hair-coloured texels on the nape skin
    h, s, v = C.hsv(out)
    forehead = allskin & (hz > 1.475) & (hxyz[..., 1] < 0.0)
    cream = ndimage.binary_dilation(forehead & (v > 0.80) & (s < 0.28), iterations=2) & forehead
    out = C.fill3d(out, cream, allskin & ~cream, hxyz, keep_detail=False)
    nape = allskin & (hxyz[..., 1] > -0.01) & (hz < 1.45)
    nape_skin = nape & (h > 6) & (h < 40) & (s > 0.15) & (s < 0.6) & (v > 0.55)
    nape_med = np.median(v[nape_skin])
    nape_skin &= (v > nape_med * 0.85) & (v < nape_med * 1.12)     # too dark (hair shadow) or pale (cream wedge)
    # the nape under the hair shell is all skin: grey (unseen by Meshy) and hair-coloured texels both go
    nape_bad = ndimage.binary_dilation(nape & ~nape_skin, iterations=2) & nape
    out = C.fill3d(out, nape_bad, nape_skin & ~nape_bad, hxyz, keep_detail=False)
    # skin patches: pale circlet/hair-light bleed and brownish hair-shadow casts against the local skin (3D, 1.5 cm)
    h, s, v = C.hsv(out)
    sy2, sx2 = np.nonzero(allskin)
    lt = cKDTree(hxyz[sy2, sx2][::7])
    _, li = lt.query(hxyz[sy2, sx2], k=1024)      # ~4 cm: a whole temple patch must not set its own median
    loc_v = np.median(v[sy2, sx2][::7][li], axis=1); loc_s = np.median(s[sy2, sx2][::7][li], axis=1)
    odd = np.zeros_like(allskin)
    vv, ss = v[sy2, sx2], s[sy2, sx2]
    odd[sy2, sx2] = (((vv > loc_v * 1.06) & (ss < loc_s * 0.7)) | ((vv < loc_v * 0.86) & (ss > loc_s * 1.15)))
    odd &= protect < 0.05
    odd = ndimage.binary_opening(odd, iterations=1)
    bright = np.zeros_like(allskin); bright[sy2, sx2] = vv > loc_v * 1.12          # pale streaks at the hair edge
    odd = ndimage.binary_dilation(odd | (bright & (protect < 0.05)), iterations=2) & allskin & (protect < 0.05)
    out = C.fill3d(out, odd, allskin & ~odd, hxyz)
    # pale cream skin (circlet/light bleed; this skin sits at saturation ~0.35-0.45) and cream on the hair
    h, s, v = C.hsv(out)
    pale = ndimage.binary_dilation(allskin & (s < 0.2) & (v > 0.75) & (protect < 0.05), iterations=2) & allskin & (protect < 0.05)
    out = C.fill3d(out, pale, allskin & ~pale, hxyz)
    hair_all = (hpart == P['Hair']) | (hpart == P['Braid'])
    cream_hair = ndimage.binary_dilation(hair_all & (s < 0.3) & (v > 0.7), iterations=2) & hair_all
    out = C.fill3d(out, cream_hair, hair_all & ~cream_hair, hxyz)
    # round 2 -- circlet bleed: gold texels on hair/skin within 1.5 cm of the band take their own part's colour
    band = hpart == P['Headband']
    h, s, v = C.hsv(out)
    gold = (h > 30) & (h < 62) & (s > 0.3) & (v > 0.5)
    bd, _ = cKDTree(hxyz[band][::3]).query(hxyz.reshape(-1, 3), k=1, distance_upper_bound=0.015)
    nearband = np.isfinite(bd).reshape(hpart.shape)
    for region in (allskin, hair_all):
        bleed = ndimage.binary_dilation(region & nearband & gold, iterations=1) & region
        out = C.fill3d(out, bleed, region & ~bleed & ~nearband, hxyz)
    # chin and mouth corners: low frequencies matched to the cheeks (lip-red texels keep their colour)
    xm = hxyz[..., 0] + 0.0075
    front = allskin & (hxyz[..., 1] < -0.03)
    chin = front & (hz > 1.375) & (hz < 1.418) & (np.abs(xm) < 0.035)
    cheeks = front & (hz > 1.418) & (hz < 1.448) & (np.abs(xm) > 0.028) & (np.abs(xm) < 0.055)
    h, s, v = C.hsv(out)
    lip = (h < 14) | (h > 340)
    gch = np.median(lin(out[cheeks & ~lip]), axis=0) / np.maximum(np.median(lin(out[chin & ~lip]), axis=0), 1e-4)
    fall = ndimage.gaussian_filter(chin.astype(np.float32), 6.0) * (~lip)
    out = np.where(allskin[..., None], srgb(np.clip(lin(out) * (1 + (np.clip(gch, 0.8, 1.25) - 1) * fall[..., None]), 0, 1)), out)
    # hairline (mm6_pman_v2_reduce_claude/scripts/tex_hairmask.py): skin under the hair/circlet mesh takes the nearby
    # hair colour with darker roots; a 6 mm band outside the mesh edge blends into it; features stay
    hc = np.load(ROOT / 'work/hair_cover_r45.npz'); covered, hdist, under_braid = hc['covered'], hc['distance'], hc['under_braid']
    hairtex = (hpart == P['Hair']) & ~bad_hair
    ky, kx = np.nonzero(allskin)
    _, ki = cKDTree(hxyz[hairtex]).query(hxyz[ky, kx], k=6)
    root = out[hairtex][ki].mean(1) * 0.78
    w = np.where(covered[ky, kx], 1.0, np.clip(1 - hdist[ky, kx] / 0.008, 0, 1) * 0.85) * (1 - protect[ky, kx])
    out[ky, kx] = out[ky, kx] * (1 - w[:, None]) + root * w[:, None]
    # nape under the braid (and not under the hair): the local neck skin
    nb = allskin & under_braid & ~covered
    out = C.fill3d(out, nb, allskin & ~under_braid & ~covered & (hz < 1.42) & (hxyz[..., 1] > -0.02), hxyz, keep_detail=False)
    # back of the neck below the hair: the head retexture's nape skin was paler and greyer than the body's neck; it
    # takes the local body neck colour (3D, 1 cm), keeping half its own fine detail
    back = allskin & ~covered & (hxyz[..., 1] > -0.015) & (hz < 1.43)
    ny2, nx2 = np.nonzero(back)
    if len(ny2):
        nbs = bskin & (bz > seam_z - 0.08) & (bz < seam_z + 0.03) & (bxyz[..., 1] > -0.02)
        my, mx = np.nonzero(nbs)
        dd, ii = cKDTree(bxyz[my, mx]).query(hxyz[ny2, nx2], k=32)
        ww = np.exp(-0.5 * (dd / 0.01) ** 2); ww /= np.maximum(ww.sum(1, keepdims=True), 1e-9)
        local = (body[my[ii], mx[ii]] * ww[..., None]).sum(1)
        det = out[ny2, nx2] - ndimage.gaussian_filter(out, (3, 3, 0))[ny2, nx2]
        wb = np.clip(1 - hdist[ny2, nx2] / 0.012, 0, 1)        # next to the hair edge the hairline band rules
        out[ny2, nx2] = np.clip((local + 0.5 * det) * (1 - wb[:, None]) + out[ny2, nx2] * wb[:, None], 0, 1)
    # braid: Meshy's braid luminance (relief) in the clean hair colour (its grey/white tie bits go)
    braid = hpart == P['Braid']; hairp = (hpart == P['Hair']) & ~bad_hair
    hair_col = np.median(out[hairp], axis=0)
    lum = out.mean(-1); rel = np.clip(lum / max(float(np.median(lum[braid])), 1e-3), 0.55, 1.35)
    out[braid] = np.clip(hair_col * rel[braid][:, None], 0, 1)
    out[band] = (0.78, 0.64, 0.38)
    # pad islands into the gutters
    interior = ndimage.binary_erosion(hpart >= 0, iterations=1)
    _, (iy, ix) = ndimage.distance_transform_edt(~interior, return_indices=True)
    padded = out[iy, ix]; padded[interior] = out[interior]
    Image.fromarray(np.uint8(np.clip(padded, 0, 1) * 255 + 0.5)).save(T / 'pfem_head_basecolor_final.png', optimize=True)
    # neck seam shading: head and body normal maps differ; both fade to flat within 1 cm of the seam
    hn = C.load(T / 'pfem_head_normal_1k.png')
    fade = np.ones(hpart.shape, np.float32); fade[ny, nx] = np.clip(sd[keep] / 0.01, 0, 1)
    hn = hn * fade[..., None] + np.array([0.5, 0.5, 1.0]) * (1 - fade[..., None])
    hn[allskin] = hn[allskin] * 0.5 + np.array([0.5, 0.5, 1.0]) * 0.5     # round 2: shading facets between face islands
    Image.fromarray(np.uint8(np.clip(hn, 0, 1) * 255 + 0.5)).save(T / 'pfem_head_normal_1k.png', optimize=True)
    bn = C.load(T / 'pfem_normal.png')
    bsel = np.nonzero(bpart >= 0)
    bd, _ = cKDTree(seam_pts).query(bxyz[bsel], k=1, distance_upper_bound=0.02)
    bf = np.ones(bpart.shape, np.float32); bf[bsel] = np.clip(np.where(np.isfinite(bd), bd, 1.0) / 0.01, 0, 1)
    bn = bn * bf[..., None] + np.array([0.5, 0.5, 1.0]) * (1 - bf[..., None])
    Image.fromarray(np.uint8(np.clip(bn, 0, 1) * 255 + 0.5)).save(T / 'pfem_normal.png', optimize=True)
    mr = C.load(T / 'pfem_head_metal_rough_1k.png')
    mr[band] = (1.0, 0.35, 0.85); mr[allskin | hair, 2] = 0.0
    Image.fromarray(np.uint8(np.clip(mr, 0, 1) * 255 + 0.5)).save(T / 'pfem_head_metal_rough_1k.png', optimize=True)
    after = np.median(lin(padded[hband]), axis=0)
    report = {'seam_z_m': round(seam_z, 4), 'head_skin_linear_before': hmed.round(4).tolist(),
              'body_skin_linear': bmed.round(4).tolist(), 'full_match_gain': full_gain.round(3).tolist(), 'head_gain_applied': gain.round(3).tolist(),
              'head_skin_linear_after': after.round(4).tolist(), 'blend_texels': int(near.sum()),
              'hair_spill_texels': int(bad_hair.sum()), 'skin_spill_texels': int(bad_skin.sum()),
              'forehead_cream_texels': int(cream.sum()), 'skin_patch_texels': int(odd.sum()), 'pale_skin_texels': int(pale.sum()), 'cream_hair_texels': int(cream_hair.sum()), 'nape_texels': int(nape_bad.sum()), 'hair_covered_texels': int(covered.sum()), 'hairline_painted': int((w > 0).sum()), 'under_braid_texels': int(nb.sum()), 'nape_neck_matched': int(back.sum()), 'chin_gain': gch.round(3).tolist(),
              'band_texels': {'head': int(hband.sum()), 'body': int(bband.sum())}}
    (T / 'pfem_head_match.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
