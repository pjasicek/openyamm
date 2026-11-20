#!/usr/bin/env python3
"""Leaf-spray atlas for one species (work/<id>/leaves_basecolor.png 1024 RGBA, leaves_normal.png 1024): four 512 px cells,
each a whorl of ~100 real-scale leaves on 8-10 twigs radiating from the centre (a cell spans one 0.5 m card, so a 65-85 px leaf is 6-8 cm).
Leaves come from ambientCG LeafSet022 (CC0). Each leaf keeps its own tangent normal, rotated with it, plus a fold
across its width (the halves tilt +-25 degrees), so in-engine lighting picks out individual leaves. Value varies per
leaf and darkens toward each twig's base; there is no baked crown occlusion here (that is the COLOR_0 vertex colour).
RGB/normals are dilated into transparent texels so mips and the alpha cutoff never pick up a halo.
Leaf colour, value and hue jitter come from the species' leaves settings. Twigs start 30 % out from the spray's hub,
thin and olive-brown, and a few leaves cross the hub (their own rng, so the rest of the spray is unchanged): seen from
below, converging dark twigs read as a black star at every card's centre.
kind 'blossom' (6tree04) adds clusters of five-petal flowers (own rng) over a darker leaf spray.
Optional (absent = the approved atlases, bit-identical):
 - leaves.palette [[srgb, weight], ...] (or one such list per atlas cell): each leaf takes one of these colours
   (own rng) instead of target_srgb (mixed autumn foliage);
 - kind 'needles': conifer branchlets instead of leaf sprays: 7-10 twigs from the hub with side twiglets, needles
   along both sides (each needle two half-strips with their own tilted normals), lighter toward the tips;
   leaves.needles {length [px], width px, spacing px, twiglets} tune them (cell = card, so px = card size / 512);
 - kind 'rosette': long narrow leaves (leaves.rosette {count, length [px], width}) radiating from the hub (palm- or
   yucca-like foliage pads);
 - leaves.snow {cells, cover, radius [px], srgb, seed}: those atlas cells get lumpy snow clumps over the spray
   (domed normals, blue-grey toward their edges) until `cover` of the spray is snow; build_tree.py gives the snow
   cells to upward-facing cards (snow.up).
Usage: make_leaf_atlas.py <id>"""
import os, math
import numpy as np
from PIL import Image
from scipy import ndimage
import common
spec = common.load(); LEAVES = spec['leaves']
SRC = os.path.join(common.SOURCE, 'leafset022')
OUT = spec['work']
color = np.asarray(Image.open(os.path.join(SRC, 'LeafSet022_1K-PNG_Color.png')).convert('RGB'), np.float32) / 255
alpha = np.asarray(Image.open(os.path.join(SRC, 'LeafSet022_1K-PNG_Opacity.png')).convert('L'), np.float32) / 255
normal = np.asarray(Image.open(os.path.join(SRC, 'LeafSet022_1K-PNG_NormalGL.png')).convert('RGB'), np.float32) / 255
lab, _ = ndimage.label(alpha > 0.5)
leaves = []
for sl in ndimage.find_objects(lab):
    if sl[0].stop - sl[0].start < 100:
        continue
    pad = 6
    ys = slice(max(sl[0].start - pad, 0), sl[0].stop + pad); xs = slice(max(sl[1].start - pad, 0), sl[1].stop + pad)
    leaves.append((color[ys, xs], alpha[ys, xs], normal[ys, xs]))
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)
mean = np.mean([lin(c)[a > 0.5].mean(0) for c, a, _ in leaves], 0)
TARGET = lin(np.array(LEAVES['target_srgb']) / 255.0)   # leaf albedo; the vertex occlusion (0.3..1) darkens the crown
CELL = 512
PALETTE = LEAVES.get('palette')
palette_rng = np.random.default_rng(LEAVES['seeds'][0] + 3000) if PALETTE else None


current_cell = [0]


def leaf_target():
    """Leaf albedo (linear): target_srgb, or one palette colour per leaf (leaves.palette: one list for every cell, or
    a list per atlas cell, so cards of different cells form differently coloured patches)."""
    if not PALETTE:
        return TARGET
    palette = PALETTE[current_cell[0]] if isinstance(PALETTE[0][0][0], list) else PALETTE
    weights = np.array([float(entry[1]) for entry in palette]); weights /= weights.sum()
    return lin(np.array(palette[int(palette_rng.choice(len(palette), p=weights))][0]) / 255.0)


def resize(img, w, h):
    return np.asarray(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((w, h), Image.LANCZOS),
                      np.float32) / 255


def paste_leaf(acc_c, acc_a, acc_n, r, bx, by, angle_deg, length_px, value, width_scale=1.0):
    """One leaf with its stem end at (bx, by), tip pointing at screen angle angle_deg (0 = up, clockwise)."""
    c, a, nm = leaves[r.integers(len(leaves))]
    s = length_px / c.shape[0]
    hgt, wid = max(int(c.shape[0] * s), 4), max(int(c.shape[1] * s * width_scale), 3)
    c, a, nm = resize(c, wid, hgt), resize(a, wid, hgt), resize(nm, wid, hgt)
    # fold: the left/right halves tilt about the midrib (tangent x), mild cup toward the tip
    x = (np.arange(wid) - (wid - 1) / 2) / max(wid / 2, 1)
    fold = np.clip(x, -1, 1)[None, :] * math.sin(math.radians(25)) * r.choice([-1.0, 1.0])
    n = nm * 2 - 1
    n[..., 0] = n[..., 0] + fold
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    # stem at the bottom: pad below so rotation about the image centre is rotation about the stem end
    pad = lambda img: np.concatenate([img, np.zeros(img.shape, img.dtype)], 0)
    cR = ndimage.rotate(pad(c), -angle_deg, reshape=True, order=1)
    aR = ndimage.rotate(pad(a), -angle_deg, reshape=True, order=1)
    nR = ndimage.rotate(pad(n), -angle_deg, reshape=True, order=1)
    th = math.radians(-angle_deg)                        # rotate tangent xy with the image (image y is down)
    nx, ny = nR[..., 0], -nR[..., 1]
    rx = nx * math.cos(th) - ny * math.sin(th); ry = nx * math.sin(th) + ny * math.cos(th)
    nR = np.stack([rx, -ry, nR[..., 2]], -1) * 0.5 + 0.5
    cl = lin(np.clip(cR, 0, 1)) / mean * leaf_target() * value
    cl *= np.array([r.uniform(*LEAVES['jitter_red']), 1.0, r.uniform(*LEAVES['jitter_blue'])])
    hh, ww = aR.shape
    ox, oy = int(round(bx - ww / 2)), int(round(by - hh / 2))
    ys_, xs_ = np.nonzero(aR > 0.05)
    if ys_.size == 0 or oy + ys_.min() < 8 or ox + xs_.min() < 8 or oy + ys_.max() >= CELL - 8 \
            or ox + xs_.max() >= CELL - 8:
        return False
    x0, y0 = max(ox, 0), max(oy, 0); x1, y1 = min(ox + ww, CELL), min(oy + hh, CELL)
    sub = (slice(y0 - oy, y1 - oy), slice(x0 - ox, x1 - ox))
    av = np.clip(aR[sub], 0, 1)[..., None]
    region = (slice(y0, y1), slice(x0, x1))
    acc_c[region] = acc_c[region] * (1 - av) + srgb(cl[sub]) * av
    acc_n[region] = acc_n[region] * (1 - av) + nR[sub] * av
    acc_a[region] = np.maximum(acc_a[region], av[..., 0])
    return True


def blossoms(acc_c, acc_a, acc_n, r, origin):
    """Clusters of five-petal flowers (~2.5-3.5 cm) over the spray: pink petals paler at the tips, a darker throat and
    a small yellow centre; each flower's normals dome outward from its centre."""
    yy, xx = np.mgrid[:CELL, :CELL]
    petal = lin(np.array(LEAVES['blossom_srgb']) / 255.0)
    count = 0
    clusters, per, size = LEAVES.get('blossom_clusters', [9, 13]), LEAVES.get('blossom_per_cluster', [4, 8]), \
        LEAVES.get('blossom_radius', [15, 22])
    for _ in range(int(r.integers(*clusters))):                  # clusters along the spray
        a = r.uniform(0, 2 * math.pi); d = r.uniform(30, 190)
        cx0, cy0 = origin + d * np.array([math.sin(a), -math.cos(a)])
        for _ in range(int(r.integers(*per))):
            cx, cy = np.array([cx0, cy0]) + r.normal(0, 22, 2)
            rf = r.uniform(*size); rot = r.uniform(0, 2 * math.pi)
            if not (rf + 8 < cx < CELL - rf - 8 and rf + 8 < cy < CELL - rf - 8):
                continue
            tint = r.uniform(0.8, 1.15) * np.array([1.0, r.uniform(0.85, 1.2), r.uniform(0.9, 1.15)])
            dx, dy = xx - cx, yy - cy
            dist = np.hypot(dx, dy)
            box = dist < rf * 1.15
            ang = np.arctan2(dy, dx) - rot
            k = np.round(ang / (2 * math.pi / 5))
            local = ang - k * 2 * math.pi / 5                   # angle from the nearest petal axis
            along, across = dist * np.cos(local), dist * np.sin(local)
            inside = box & ((along - 0.55 * rf) ** 2 / (0.52 * rf) ** 2 + across ** 2 / (0.36 * rf) ** 2 < 1)
            inside |= box & (dist < 0.25 * rf)
            t = np.clip(dist / rf, 0, 1)
            colour = petal[None, :] * tint * (0.7 + 0.45 * t[inside])[:, None]      # paler toward the petal tips
            centre = dist[inside] < 0.18 * rf
            colour[centre] = lin(np.array([210.0, 170.0, 60.0]) / 255) * 0.6
            acc_c[inside] = srgb(colour)
            acc_a[inside] = 1.0
            n = np.stack([dx[inside] / rf * 0.7, -dy[inside] / rf * 0.7, np.ones(inside.sum())], 1)
            n /= np.linalg.norm(n, axis=1, keepdims=True)
            acc_n[inside] = n * 0.5 + 0.5
            count += 1
    return count


def cluster(seed):
    r = np.random.default_rng(seed)
    acc_c = np.zeros((CELL, CELL, 3), np.float32); acc_a = np.zeros((CELL, CELL), np.float32)
    acc_n = np.zeros((CELL, CELL, 3), np.float32); acc_n[...] = (0.5, 0.5, 1.0)
    yy, xx = np.mgrid[:CELL, :CELL]
    # a whorl at a branch end: 6-7 twigs radiating from near the centre, alternate leaves along each, leaves
    # filling the centre last (on top) so the card reads as a dense round spray from any side
    origin = np.array([CELL * 0.5, CELL * 0.5]) + r.uniform(-12, 12, 2)
    twigs = int(r.integers(8, 11))
    spread = np.sort(r.uniform(0, 360, twigs))
    spread = np.linspace(0, 360, twigs, endpoint=False) + r.uniform(0, 360) + r.uniform(-14, 14, twigs)
    placed = 0
    for t, heading in enumerate(spread):
        steps = int(r.uniform(70, 95)); ang = math.radians(heading); p = origin.copy(); path = []
        for i in range(steps):
            path.append(p.copy()); p += 2.0 * np.array([math.sin(ang), -math.cos(ang)]); ang += r.uniform(-0.02, 0.02)
        for i, (tx, ty) in enumerate(path):
            if i < 0.3 * steps:
                continue                                     # no twig at the hub (no dark star from below)
            w = 1.6 * (1 - i / steps) + 0.7
            m = (xx - tx) ** 2 + (yy - ty) ** 2 < w * w
            acc_c[m] = (0.20, 0.17, 0.08); acc_a[m] = 1
        count = int(r.integers(7, 10))
        for k in range(count):
            f = 0.25 + 0.72 * (k + r.uniform(-0.2, 0.2)) / count
            i = min(int(f * steps), steps - 1); tx, ty = path[i]
            side = 1 if k % 2 == 0 else -1
            value = r.uniform(*LEAVES['value']) * (0.75 + 0.25 * f)    # darker toward the whorl centre
            placed += paste_leaf(acc_c, acc_a, acc_n, r, tx, ty, heading + side * r.uniform(30, 55),
                                 r.uniform(66, 84), value)
        tx, ty = path[-1]
        placed += paste_leaf(acc_c, acc_a, acc_n, r, tx, ty, heading + r.uniform(-12, 12), r.uniform(70, 86),
                             r.uniform(0.95, 1.2))
    for k in range(int(r.integers(14, 20))):
        heading = r.uniform(0, 360); d = r.uniform(10, 120)
        tx, ty = origin + d * np.array([math.sin(math.radians(heading)), -math.cos(math.radians(heading))])
        placed += paste_leaf(acc_c, acc_a, acc_n, r, tx, ty, heading, r.uniform(64, 80), r.uniform(0.85, 1.1))
    hub = np.random.default_rng(seed + 1000)
    for k in range(5):                                   # leaves lying across the hub
        heading = hub.uniform(0, 360); d = -hub.uniform(20, 45)
        tx, ty = origin + d * np.array([math.sin(math.radians(heading)), -math.cos(math.radians(heading))])
        placed += paste_leaf(acc_c, acc_a, acc_n, hub, tx, ty, heading, hub.uniform(64, 80), hub.uniform(0.9, 1.1))
    if LEAVES['kind'] == 'blossom':
        placed += blossoms(acc_c, acc_a, acc_n, np.random.default_rng(seed + 2000), origin)
    border = np.zeros_like(acc_a); border[6:-6, 6:-6] = 1
    acc_a *= border
    return acc_c, acc_a, acc_n, placed


def needle_cluster(seed):
    """Conifer branchlet whorl (kind 'needles'), drawn at 2x and box-filtered to the cell."""
    from PIL import ImageDraw
    r = np.random.default_rng(seed)
    cfg = LEAVES.get('needles', {})
    length = [2 * v for v in cfg.get('length', [24, 36])]; width = 2 * cfg.get('width', 3.0)
    spacing = 2 * cfg.get('spacing', 2.2); twiglets = cfg.get('twiglets', [6, 9])
    S = 2 * CELL
    col = np.zeros((S, S, 3), np.float32); nrm_ = np.zeros((S, S, 3), np.float32); alp = np.zeros((S, S), np.float32)
    layer_c = Image.new('RGB', (S, S)); layer_n = Image.new('RGB', (S, S), (128, 128, 255)); layer_a = Image.new('L', (S, S))
    dc, dn, da = ImageDraw.Draw(layer_c), ImageDraw.Draw(layer_n), ImageDraw.Draw(layer_a)

    def enc_c(lin_rgb):
        return tuple(int(v) for v in (np.clip(srgb(np.clip(lin_rgb, 0, 1)), 0, 1) * 255).round())

    def enc_n(n):
        n = np.array(n, float); n /= np.linalg.norm(n)
        return tuple(int(v) for v in ((n * 0.5 + 0.5) * 255).round())

    origin = np.array([S * 0.5, S * 0.5]) + r.uniform(-20, 20, 2)
    twig_rgb = lin(np.array([62.0, 48.0, 32.0]) / 255)
    needles = 0
    branches = []                                        # (start, heading rad, length px, base value)
    count = int(r.integers(9, 13))
    for heading in np.linspace(0, 2 * math.pi, count, endpoint=False) + r.uniform(0, 2 * math.pi) \
            + r.uniform(-0.2, 0.2, count):
        reach = r.uniform(0.70, 0.92) * (S / 2 - 40)
        start = origin + 0.12 * reach * np.array([math.sin(heading), -math.cos(heading)])
        branches.append((start, heading, reach * 0.88, 0.8))
        for k in range(int(r.integers(*twiglets))):
            f = r.uniform(0.25, 0.75); side = 1 if k % 2 == 0 else -1
            p = start + f * reach * 0.88 * np.array([math.sin(heading), -math.cos(heading)])
            h2 = heading + side * r.uniform(0.6, 0.95)
            branches.append((p, h2, reach * r.uniform(0.3, 0.5) * (1.15 - f), 0.9))
    hub = np.random.default_rng(seed + 1000)              # short tufts across the hub (no hole at the card centre)
    for k in range(int(hub.integers(6, 9))):
        heading = hub.uniform(0, 2 * math.pi)
        start = origin + hub.uniform(0, 40) * np.array([math.sin(heading + 2.5), -math.cos(heading + 2.5)])
        branches.append((start, heading, hub.uniform(60, 110), 0.85))
    for start, heading, reach, base_value in branches:
        steps = max(int(reach / 4), 2); ang = heading; p = start.copy(); path = []
        for i in range(steps):
            path.append(p.copy()); p = p + 4 * np.array([math.sin(ang), -math.cos(ang)]); ang += r.uniform(-0.03, 0.03)
        dc.line([tuple(q) for q in path], fill=enc_c(twig_rgb), width=4); da.line([tuple(q) for q in path], fill=255, width=4)
        dn.line([tuple(q) for q in path], fill=(128, 128, 255), width=4)
        travelled = 0.0
        for i in range(1, steps):
            travelled += 4
            if travelled < spacing:
                continue
            travelled = 0.0
            f = i / steps
            tx, ty = path[i]
            for side in (-1, 1):
                if r.random() < 0.05:
                    continue
                a = heading + side * math.radians(r.uniform(38, 72))
                ln = r.uniform(*length) * (0.75 + 0.25 * (1 - f))
                d = np.array([math.sin(a), -math.cos(a)]); perp = np.array([-d[1], d[0]])
                tip = np.array([tx, ty]) + d * ln
                value = r.uniform(*LEAVES['value']) * (0.72 + 0.28 * f) * base_value
                value *= 1.0 + 0.35 * max(f - 0.75, 0) / 0.25          # fresh lighter growth at the tips
                rgb = TARGET * value * np.array([r.uniform(*LEAVES['jitter_red']), 1.0, r.uniform(*LEAVES['jitter_blue'])])
                for half in (-1, 1):                       # two half-strips: a rounded needle
                    off = perp * half * width * 0.25
                    seg = [tuple(np.array([tx, ty]) + off), tuple(tip + off * 0.4)]
                    shade = 1.0 + 0.12 * half
                    dc.line(seg, fill=enc_c(rgb * shade), width=max(int(round(width / 2)), 1))
                    da.line(seg, fill=255, width=max(int(round(width / 2)), 1))
                    nx, ny = perp * half * 0.55
                    dn.line(seg, fill=enc_n([nx, -ny, 1.0]), width=max(int(round(width / 2)), 1))
                needles += 1
    a2 = np.asarray(layer_a, np.float32) / 255
    c2 = np.asarray(layer_c, np.float32) / 255; n2 = np.asarray(layer_n, np.float32) / 255
    box = lambda x: x.reshape(CELL, 2, CELL, 2, *x.shape[2:]).mean((1, 3))
    acc_a = box(a2)
    acc_c = box(c2 * a2[..., None]) / np.maximum(acc_a[..., None], 1e-6)
    acc_n = box(n2 * a2[..., None]) / np.maximum(acc_a[..., None], 1e-6)
    acc_n = np.where(acc_a[..., None] > 0, acc_n, (0.5, 0.5, 1.0))
    border = np.zeros_like(acc_a); border[6:-6, 6:-6] = 1
    return acc_c, acc_a * border, acc_n, needles


def rosette_cluster(seed):
    """Foliage pad (kind 'rosette'): long narrow leaves radiating from the hub, darker toward it."""
    r = np.random.default_rng(seed)
    cfg = LEAVES.get('rosette', {})
    acc_c = np.zeros((CELL, CELL, 3), np.float32); acc_a = np.zeros((CELL, CELL), np.float32)
    acc_n = np.zeros((CELL, CELL, 3), np.float32); acc_n[...] = (0.5, 0.5, 1.0)
    origin = np.array([CELL * 0.5, CELL * 0.5]) + r.uniform(-8, 8, 2)
    placed = 0
    count = int(r.integers(*cfg.get('count', [26, 34])))
    order = np.argsort(r.uniform(size=count))           # long outer leaves first, short central ones on top
    lengths = np.sort(r.uniform(*cfg.get('length', [150, 225]), count))[::-1]
    for k in range(count):
        heading = r.uniform(0, 360); ln = lengths[k]
        d = r.uniform(4, 16)
        bx, by = origin + d * np.array([math.sin(math.radians(heading)), -math.cos(math.radians(heading))])
        value = r.uniform(*LEAVES['value']) * (0.8 + 0.2 * k / count)
        placed += paste_leaf(acc_c, acc_a, acc_n, r, bx, by, heading, ln, value, cfg.get('width', 0.4))
    border = np.zeros_like(acc_a); border[6:-6, 6:-6] = 1
    acc_a *= border
    return acc_c, acc_a, acc_n, placed


def add_snow(acc_c, acc_a, acc_n, seed):
    """Lumpy snow clumps over a spray (leaves.snow): domed, slightly blue-grey toward their edges."""
    cfg = LEAVES['snow']
    r = np.random.default_rng(seed + 4000)
    spray = acc_a > 0.5
    if not spray.any():
        return 0.0
    ys, xs = np.nonzero(spray)
    yy, xx = np.mgrid[:CELL, :CELL]
    rough = ndimage.gaussian_filter(r.normal(0, 1, (CELL, CELL)), 6); rough /= rough.std()
    fine = ndimage.gaussian_filter(r.normal(0, 1, (CELL, CELL)), 1.5); fine /= fine.std()
    height = np.zeros((CELL, CELL), np.float32)
    target = cfg.get('cover', 0.5) * spray.sum()
    for _ in range(400):
        mask = height > 0
        if (mask & spray).sum() >= target:
            break
        i = int(r.integers(len(ys))); cy, cx = ys[i], xs[i]
        rad = r.uniform(*cfg.get('radius', [16, 40]))
        d = np.hypot(xx - cx, (yy - cy) * r.uniform(1.0, 1.6)) / rad + 0.18 * rough + 0.08 * fine
        height = np.maximum(height, np.clip(1 - d ** 2, 0, None))
    mask = height > 0.02
    gy, gx = np.gradient(ndimage.gaussian_filter(height, 1.0) * 26)
    n = np.dstack([-gx, gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    snow = lin(np.array(cfg.get('srgb', [236, 240, 248])) / 255.0)
    shade = (0.72 + 0.28 * np.clip(height / 0.6, 0, 1))[..., None]
    tint = np.array([0.93, 0.97, 1.05]) + (1 - np.clip(height / 0.6, 0, 1))[..., None] * np.array([-0.08, -0.04, 0.0])
    colour = srgb(snow * shade * tint * (1 + 0.04 * fine[..., None]))
    acc_c[mask] = colour[mask]; acc_a[mask] = 1.0; acc_n[mask] = (n * 0.5 + 0.5)[mask]
    border = np.zeros_like(acc_a); border[6:-6, 6:-6] = 1
    acc_a *= border
    return round(float((mask & spray).sum() / spray.sum()), 3)


base = np.zeros((1024, 1024, 4), np.float32); nrm = np.zeros((1024, 1024, 3), np.float32); nrm[...] = (0.5, 0.5, 1.0)
info = []
for cell, seed in enumerate(LEAVES['seeds']):
    current_cell[0] = cell
    if LEAVES['kind'] == 'needles':
        c, a, nm, placed = needle_cluster(seed)
    elif LEAVES['kind'] == 'rosette':
        c, a, nm, placed = rosette_cluster(seed)
    else:
        c, a, nm, placed = cluster(seed)
    if LEAVES.get('snow') and cell in LEAVES['snow']['cells']:
        print('SNOW cell', cell, 'cover', add_snow(c, a, nm, seed))
    row, col = divmod(cell, 2)
    sl = (slice(row * CELL, (row + 1) * CELL), slice(col * CELL, (col + 1) * CELL))
    base[sl[0], sl[1], :3] = c; base[sl[0], sl[1], 3] = a; nrm[sl] = nm
    info.append((placed, round(float(a.mean()), 3)))
inside = base[..., 3] > 0.5
idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
base[..., :3] = base[..., :3][idx[0], idx[1]]
nrm = np.where(inside[..., None], nrm, nrm[idx[0], idx[1]])
Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'leaves_basecolor.png'))
Image.fromarray((np.clip(nrm, 0, 1) * 255).astype(np.uint8), 'RGB').save(os.path.join(OUT, 'leaves_normal.png'))
preview = Image.new('RGBA', (1024, 1024), (150, 160, 175, 255))
preview.alpha_composite(Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8) * inside[..., None], 'RGBA'))
preview.convert('RGB').save(os.path.join(OUT, 'atlas_preview.png'))
print('ATLAS v2 leaves and coverage per cell', info)

MOSS = spec['crown'].get('moss')
if MOSS and MOSS.get('kind') == 'willow':
    # Leftovers addition: weeping-willow wands instead of moss (crown.moss.kind 'willow'), same 128 x 512 card (u
    # across, v down, image top = the strand's top): `fibres` thin pendulous shoots per card, each a slightly swaying
    # stem with narrow lanceolate leaves along both sides, pointing down and out, lighter toward the tips; a few
    # sunlit leaves (`highlight` [fraction, srgb]). Drawn at 4x and reduced, with a flat normal map.
    from PIL import ImageDraw
    mr = np.random.default_rng(MOSS.get('seed', 707) + 1)
    MW, MH, SSW = 128, 512, 4
    big = Image.new('RGBA', (MW * SSW, MH * SSW), (0, 0, 0, 0)); draw = ImageDraw.Draw(big)
    base = np.array(MOSS.get('srgb', [70, 120, 60]), float)
    hl_fraction, hl_srgb = MOSS.get('highlight', [0.12, [170, 205, 110]])
    for _ in range(MOSS.get('fibres', 5)):
        x0 = mr.uniform(0.18, 0.82) * MW; length = mr.uniform(0.7, 1.0) * MH; phase = mr.uniform(0, 6.3)
        sway = mr.uniform(4, 12); period = mr.uniform(120, 260); drift = mr.uniform(-10, 10)
        stem = lambda y: x0 + sway * math.sin(y / period + phase) + drift * y / MH
        ys = np.arange(0, length, 2.0)
        draw.line([(stem(y) * SSW, y * SSW) for y in ys], fill=(70, 80, 40, 255), width=SSW)
        y = mr.uniform(0, 8)
        while y < length - 4:
            for side in (-1, 1):
                t = y / length
                leaf_len = mr.uniform(16, 26) * (1 - 0.35 * t); leaf_w = mr.uniform(2.6, 3.6)
                ang = math.radians(mr.uniform(14, 34))          # from straight down, outward
                dx, dy = side * math.sin(ang), math.cos(ang)
                bx, by = stem(y), y
                tip = (bx + dx * leaf_len, by + dy * leaf_len)
                nx, ny = -dy, dx
                mid = (bx + dx * leaf_len * 0.45, by + dy * leaf_len * 0.45)
                poly = [(bx, by), (mid[0] + nx * leaf_w, mid[1] + ny * leaf_w), tip,
                        (mid[0] - nx * leaf_w, mid[1] - ny * leaf_w)]
                value = mr.uniform(0.75, 1.2) * (0.85 + 0.3 * t)
                colour = np.array(hl_srgb, float) if mr.random() < hl_fraction else base * value
                colour = colour * np.array([mr.uniform(0.9, 1.1), 1.0, mr.uniform(0.88, 1.08)])
                draw.polygon([(px * SSW, py * SSW) for px, py in poly],
                             fill=tuple(int(c) for c in np.clip(colour, 0, 255)) + (255,))
            y += mr.uniform(6, 10)
    small = big.resize((MW, MH), Image.LANCZOS)
    arr = np.asarray(small).astype(np.float32) / 255.0
    acc = (arr[..., 3] > 0.5).astype(np.float32)
    acc[:, :2] = acc[:, -2:] = 0
    rgb = arr[..., :3] / np.maximum(arr[..., 3:4], 1e-3)
    inside = acc > 0.5
    idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
    rgb = rgb[idx[0], idx[1]]
    Image.fromarray((np.dstack([np.clip(rgb, 0, 1), acc]) * 255).astype(np.uint8), 'RGBA').save(
        os.path.join(OUT, 'moss_basecolor.png'))
    Image.fromarray(np.full((MH, MW, 3), (128, 128, 255), np.uint8), 'RGB').save(os.path.join(OUT, 'moss_normal.png'))
    print('MOSS willow texture coverage', round(float(acc.mean()), 3))
elif MOSS:
    # Hanging moss (crown.moss species): work/<id>/moss_basecolor.png 128 x 512 RGBA, u across a strand card, v down
    # it (image top = the strand's top). Wispy fibres of grey-green, thinning and breaking up toward their ends.
    mr = np.random.default_rng(MOSS.get('seed', 707) + 1)
    MW, MH = 128, 512
    acc = np.zeros((MH, MW), np.float32); shade = np.ones((MH, MW), np.float32)
    yy, xx = np.mgrid[:MH, :MW]
    fibres = MOSS.get('fibres', 70)
    fibre_width = MOSS.get('fibre_width', 1.6)
    fringe = MOSS.get('fringe', 0.0)
    for _ in range(fibres):
        x0 = mr.uniform(0.2, 0.8) * MW; length = mr.uniform(0.35, 1.0) * MH; phase = mr.uniform(0, 6.3)
        wave = x0 + 10 * np.sin(yy / mr.uniform(40, 90) + phase) + (yy / MH) * mr.uniform(-14, 14)
        width = fibre_width * (1 - yy / length).clip(0.15, 1)
        # fringe: the fibre breaks up over its last part, so a strand ends in ragged wisps instead of a hard edge
        broken = 0.08 + 0.5 * yy / MH + fringe * np.clip((yy / length - 0.6) / 0.4, 0, 1)
        on = (np.abs(xx - wave) < width) & (yy < length) & (mr.random((MH, MW)) > broken)
        acc = np.maximum(acc, on.astype(np.float32))
        shade = np.where(on, mr.uniform(0.7, 1.15), shade)
    acc = ndimage.binary_closing(acc > 0, iterations=1).astype(np.float32)
    acc[:, :3] = acc[:, -3:] = 0
    colour = lin(np.array(MOSS.get('srgb', [120, 140, 90])) / 255.0)
    rgb = srgb(colour[None, None, :] * shade[..., None] * (0.85 + 0.25 * (1 - yy / MH))[..., None])
    inside = acc > 0.5
    idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
    rgb = rgb[idx[0], idx[1]]
    Image.fromarray((np.dstack([np.clip(rgb, 0, 1), acc]) * 255).astype(np.uint8), 'RGBA').save(
        os.path.join(OUT, 'moss_basecolor.png'))
    Image.fromarray(np.full((MH, MW, 3), (128, 128, 255), np.uint8), 'RGB').save(os.path.join(OUT, 'moss_normal.png'))
    print('MOSS texture coverage', round(float(acc.mean()), 3))
