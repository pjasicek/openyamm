"""Throat repaint for the v2 compose (system Python, called by scripts/compose_v2.py).

Meshy never saw the front of the neck (the head hides it in the front master), so the body paint has a pale stripe
there and the head paint a white patch under the jaw, where the native dragon has gold ventral plates up to the
chin. Here the gold plate band of the chest is continued up the neck to the jaw:
- the ventral line is the front-most midline point per 1 mm of height (texels with |x| < 4 mm facing forward/down);
  every throat texel gets an arc length s along it and its lateral offset x;
- the chest part of the line (z 0.165-0.245) has clean plates: they give the band half-width w, the plate period (from
  the plate edges, luminance minima) and the gold colour;
- above it, texels inside the band are painted with procedural plates phase-locked to the last clean plate edge
  (copying chest plates up the neck smeared them), the band narrowing toward the jaw; edges feathered over 2.5 mm;
- pale, unsaturated texels left beside the band in the throat zone take the colour of the nearest non-pale scale
  texel at the same height.
Both texture sets (body, head) are handled together through their 3D texel positions, so the band is continuous
across the head seam. Returns a report; sets D[label]['throat'] (gold region) per set."""
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree


def hsv(rgb):
    h, s, v = np.moveaxis(np.array(Image.fromarray(np.uint8(np.clip(rgb, 0, 1) * 255)).convert('HSV'), float) / 255, -1, 0)
    return h * 360, s, v


def repaint(D):
    labels = ['body', 'head']
    P = np.concatenate([D[l]['pos'][D[l]['cov']] for l in labels]); Nn = np.concatenate([D[l]['nrm'][D[l]['cov']] for l in labels])
    C = np.concatenate([D[l]['rgb'][D[l]['cov']] for l in labels])
    where = [np.argwhere(D[l]['cov']) for l in labels]; owner = np.concatenate([np.full(len(w), i) for i, w in enumerate(where)])
    flat = np.concatenate(where)
    front = Nn @ np.array([0, -.9, -.45]) / np.linalg.norm([0, -.9, -.45])
    mid = (np.abs(P[:, 0]) < .004) & (front > .35) & (P[:, 1] < -.2) & (P[:, 2] > .16) & (P[:, 2] < .43)
    zb = np.round(P[mid, 2] / .001).astype(int); line = []
    for k in np.unique(zb):
        sel = P[mid][zb == k]
        if len(sel) < 3: continue
        line.append(sel[np.argmin(sel[:, 1])] * [0, 1, 1])
    line = np.array(sorted(line, key=lambda p: p[2]))
    line = line[line[:, 1] > -.345]                     # stop under the chin; the face is not throat
    # smooth the line and drop the jaw part (the line turns forward under the chin)
    line[:, 1] = ndimage.median_filter(line[:, 1], 9); line[:, 1] = ndimage.gaussian_filter1d(line[:, 1], 3)
    s_line = np.r_[0, np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))]
    lt = cKDTree(line)
    zone = (P[:, 1] < -.22) & (P[:, 2] > .19) & (P[:, 2] < .425) & (np.abs(P[:, 0]) < .045) & (front > -.1)
    d, j = lt.query(P[zone]); s = s_line[j]; x = P[zone, 0]
    h, sat, val = hsv(C[zone][None])[0], hsv(C[zone][None])[1][0], hsv(C[zone][None])[2][0]
    h = h[0]
    gold = (h > 35) & (h < 62) & (sat > .45) & (val > .30)
    z = P[zone, 2]
    good = (z > .165) & (z < .245)          # clean chest plates (the pale Meshy stripe reaches down to z 0.25)
    # half-width of the gold band on the chest, per 5 mm of arc
    sg = s[good & gold]; xg = np.abs(x[good & gold])
    bins = np.arange(sg.min(), sg.max() + .005, .005)
    widths = [np.percentile(xg[(sg >= b) & (sg < b + .005)], 92) for b in bins[:-1] if ((sg >= b) & (sg < b + .005)).sum() > 30]
    w_chest = float(np.median(widths))
    s0, s1 = float(np.percentile(s[good], 2)), float(np.percentile(s[good], 98))
    jaw = line[np.argmax(line[:, 2])]; s_top = float(s_line[-1])
    def half_width(sv):
        f = np.clip((sv - s1) / max(s_top - s1, 1e-6), 0, 1); return w_chest * (1 - .45 * f)
    # plate period: luminance minima along the midline of the good part
    # plate period from luminance minima along the band (off the midline, whose texels sit on the island border);
    # minima closer than 8 mm are merged, and a period outside 12-35 mm falls back to 20 mm
    ml = good & (np.abs(x) > .004) & (np.abs(x) < .014); ss = s[ml]; lum = C[zone][ml] @ [.2126, .7152, .0722]
    grid = np.arange(s0, s1, .0005); prof = np.array([lum[np.abs(ss - g) < .001].mean() if (np.abs(ss - g) < .001).any() else np.nan for g in grid])
    prof = np.where(np.isfinite(prof), prof, np.nanmean(prof)); prof = ndimage.gaussian_filter1d(prof, 4)
    minima = []
    for i in range(8, len(prof) - 8):
        if prof[i] == prof[i - 8:i + 9].min() and prof[i] < np.mean(prof) and (not minima or grid[i] - minima[-1] > .008): minima.append(grid[i])
    gaps = np.diff(minima); period = float(np.median(gaps)) if len(gaps) else .02
    if not .012 <= period <= .035: period = .02
    # procedural plates from the start of the stripe (z 0.245) to the chin: grooves every `period`, phase-locked to
    # the last clean plate edge below, a shallow downward chevron, lighter upper half of each plate, rounder
    # (darker) toward the band edge; colour = median clean gold scaled by that luminance, plus 30 % of the
    # original fine detail. Blended in over 10 mm at the start and 2.5 mm at the band edge.
    tile_end = minima[-1] if minima else s1
    gold_c = np.median(C[zone][good & gold & (np.abs(x) < w_chest * .7)], 0); gold_l = float(gold_c @ [.2126, .7152, .0722])
    zone_idx = np.where(zone)[0]
    chin = (P[zone, 1] < -.345) | (P[zone, 2] > line[-1, 2] + .004)
    target = (s > tile_end) & (np.abs(x) < half_width(s) * 1.1) & ~chin
    st, xt = s[target], np.abs(x[target]); wt = half_width(st)
    u = (st - tile_end) / period - .35 * (xt / wt); f = np.mod(u, 1.)
    groove = np.exp(-(f / .09) ** 2) + np.exp(-((1 - f) / .09) ** 2)
    lum_p = (.82 + .30 * np.clip(f / .2, 0, 1) * (1 - .55 * f)) * (1 - .42 * groove) * (1 - .30 * (xt / wt) ** 2)
    orig = C[zone][target]; ol = orig @ [.2126, .7152, .0722]
    local = ndimage.uniform_filter1d(ol[np.argsort(st)], 25)[np.argsort(np.argsort(st))]
    newc = np.clip(gold_c * (lum_p / .95)[:, None] * (1 + .3 * (ol - local)[:, None] / max(gold_l, 1e-3)), 0, 1)
    edge = np.clip((wt * 1.1 - xt) / .0025, 0, 1)
    start = np.clip((st - tile_end) / .010, 0, 1)
    wgt = (edge * start)[:, None]
    C2 = C.copy(); C2[zone_idx[target]] = C[zone_idx[target]] * (1 - wgt) + newc * wgt
    # pale leftovers beside the band
    hz, sz, vz = hsv(C2[zone][None]); sz, vz = sz[0], vz[0]
    pale = (sz < .38) & (vz > .45) & (s > tile_end - .01) & ~target & (front[zone] > .1) & ~chin
    okc = ~pale & ~target & (sz > .4) & (z > .28)
    if pale.any():
        tr = cKDTree(np.c_[P[zone][okc][:, 2] * 3, np.abs(P[zone][okc][:, 0]), P[zone][okc][:, 1]])
        _, k2 = tr.query(np.c_[P[zone][pale][:, 2] * 3, np.abs(P[zone][pale][:, 0]) + .006, P[zone][pale][:, 1]])
        C2[zone_idx[pale]] = C2[zone][okc][k2]
    # write back
    throat_mask = np.zeros(len(P), bool); throat_mask[zone_idx[target]] = True
    for i, l in enumerate(labels):
        sel = owner == i; rgb = D[l]['rgb']; rgb[flat[sel][:, 0], flat[sel][:, 1]] = C2[sel]
        m = np.zeros(D[l]['cov'].shape, bool); m[flat[sel & throat_mask][:, 0], flat[sel & throat_mask][:, 1]] = True
        D[l]['throat'] = ndimage.binary_dilation(m, iterations=1) & D[l]['cov']
    return {'ventral_line_points': len(line), 'band_half_width_chest_m': w_chest, 'plate_period_m': period, 'tile_end_s_m': float(tile_end),
            'neck_length_s_m': s_top, 'repainted_texels': int(target.sum()), 'pale_texels_recoloured': int(pale.sum())}
