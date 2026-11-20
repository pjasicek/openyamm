#!/usr/bin/env python3
"""Map pass v2 of the held-sword retexture pilot (README.md, "Post-process"), replacing post_maps.py pack.

Meshy's paint (4K, downsampled once to 2K, gently graded) is kept, with four fixes measured in game on v1:
1. Fine band: Meshy painted a 4-8 texel weave/knit pattern over the metal (item001: blade and guard like chain-mail
   fabric). On metal texels the detail finer than sigma 3 texels is kept at 15 %; blade steel keeps half its chroma.
2. Metal albedo into the PBR range (Khronos: metal base colour 0.5-1.0 linear): the painted iron was 0.2 linear, so the
   blade reflected a fifth of the sky and read black. Metal texels are scaled so their median luminance is TARGET.
3. Blade profile in the normal map: Meshy's normal map is nearly flat, and the blade faces are flat slabs, so every
   texel of a blade face reflected one direction. Computed from the mesh: per blade face texel its place across the
   blade (from the blade's outline per slice along its length) gives a ridge (both halves tilted a few degrees away
   from the centre line) and honed edge bevels (a band at each cutting edge tilted further); single-edged blades get
   the edge bevel on the edge side only. Blended with Meshy's normal (whiteout).
4. Roughness: Meshy's metal roughness stretched to 0.2-0.55 (satin flats), honed bevels glossier, and a fine
   lengthwise grinding grain from the 3D position (seamless across UV islands) in colour and roughness.

Usage: python3 blade_pass.py <icon>
Reads work/<icon>/layout_measure.glb and work/<icon>/maps/{base_color_2k_graded,metallic_2k,roughness_2k,normal_2k,
old_metal}.png; writes maps/{basecolor,mr,normal}.png and maps/debug_*.png. Normal output is in Meshy's convention
(+y down the image); tools/normal_map_convention.py converts the assembled GLB.
"""
import json
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
SIZE = 2048
TARGET = 0.55          # median linear luminance of metal texels
FINE_KEEP = 0.15
FINE_SIGMA = 3.0      # texels at 2K: the weave cells are 4-8 texels
FITTING_SIGMA = 6.0   # texels: metal fittings outside the blade
BLADE_CHROMA = 0.5    # blade steel keeps half its painted colour saturation (the paint tinted it like brass)
# Blade profiles: ridge tilt (degrees) over the flat, honed bevel band (fraction of the half width) and its tilt;
# 'single' puts the bevel on the edge side only (side found from the blade's thickness: the spine is thicker).
PROFILES = {
    'item001': {'kind': 'diamond', 'ridge': 6.0, 'band': 0.16, 'bevel': 22.0},
    'item005': {'kind': 'diamond', 'ridge': 7.0, 'band': 0.14, 'bevel': 22.0},
    '7item010': {'kind': 'single', 'ridge': 0.0, 'band': 0.22, 'bevel': 20.0},
    '7item012': {'kind': 'single', 'ridge': 0.0, 'band': 0.25, 'bevel': 20.0},
}


def read_glb(path):
    data = open(path, 'rb').read()
    jlen = struct.unpack('<I', data[12:16])[0]
    doc = json.loads(data[20:20 + jlen])
    binary = data[20 + jlen + 8:]
    types = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}
    counts = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}

    def acc(i):
        a = doc['accessors'][i]
        view = doc['bufferViews'][a['bufferView']]
        start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
        n = a['count'] * counts[a['type']]
        return np.frombuffer(binary, types[a['componentType']], n, start).reshape(a['count'], -1).astype(np.float64)

    prim = doc['meshes'][0]['primitives'][0]
    return (acc(prim['attributes']['POSITION']), acc(prim['attributes']['TEXCOORD_0']),
            acc(prim['indices']).astype(np.int64).reshape(-1, 3))


def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def value_noise(x, seed):
    """Smooth 1D value noise, period-free (hashing integer lattice points)."""
    i = np.floor(x).astype(np.int64)
    f = x - i
    def h(k):
        k = (k * 374761393 + seed * 668265263) & 0xFFFFFFFF
        k = ((k ^ (k >> 13)) * 1274126177) & 0xFFFFFFFF
        return (k & 0xFFFF) / 65535.0 * 2 - 1
    u = f * f * (3 - 2 * f)
    return h(i) * (1 - u) + h(i + 1) * u


def main(icon):
    prof = PROFILES[icon]
    work = os.path.join(PROJECT, 'work', icon)
    maps = os.path.join(work, 'maps')
    pos, uv, tri = read_glb(os.path.join(work, 'layout_measure.glb'))

    # Triangle id per texel (glTF UV: u right, v down = image rows).
    ids = Image.new('I', (SIZE, SIZE), 0)
    draw = ImageDraw.Draw(ids)
    for f, t in enumerate(tri):
        draw.polygon([(uv[k, 0] * SIZE, uv[k, 1] * SIZE) for k in t], fill=f + 1)
    tid = np.asarray(ids, np.int64) - 1
    inside = tid >= 0
    ys, xs = np.nonzero(inside)
    ft = tid[ys, xs]

    # Per triangle: face normal, position gradients along u (columns) and v (rows), and the map uv -> position.
    p0, p1, p2 = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    q0, q1, q2 = uv[tri[:, 0]] * SIZE, uv[tri[:, 1]] * SIZE, uv[tri[:, 2]] * SIZE
    nf = np.cross(p1 - p0, p2 - p0)
    nf /= np.maximum(np.linalg.norm(nf, axis=1, keepdims=True), 1e-12)
    du1, du2 = q1 - q0, q2 - q0
    det = du1[:, 0] * du2[:, 1] - du1[:, 1] * du2[:, 0]
    det = np.where(np.abs(det) < 1e-12, 1e-12, det)
    e1, e2 = p1 - p0, p2 - p0
    dpdx = (e1 * du2[:, 1:2] - e2 * du1[:, 1:2]) / det[:, None]
    dpdy = (e2 * du1[:, 0:1] - e1 * du2[:, 0:1]) / det[:, None]
    texel = np.stack([xs + 0.5, ys + 0.5], 1)
    d = texel - q0[ft]
    p = p0[ft] + dpdx[ft] * d[:, 0:1] + dpdy[ft] * d[:, 1:2]
    n = nf[ft]

    # Blade frame from the mesh: long, wide and thin axes; guard = widest slice; blade = guard to tip.
    ext = pos.max(0) - pos.min(0)
    order = np.argsort(ext)
    thin, wide, long_ = order[0], order[1], order[2]
    lo, hi = pos[:, long_].min(), pos[:, long_].max()
    bins = np.linspace(lo, hi, 61)
    widths = []
    for a, b in zip(bins[:-1], bins[1:]):
        sel = (pos[:, long_] >= a) & (pos[:, long_] <= b)
        widths.append(np.ptp(pos[sel, wide]) if sel.sum() > 2 else 0)
    g = int(np.argmax(widths))
    guard = (bins[g] + bins[g + 1]) / 2
    tip = 1.0 if hi - guard > guard - lo else -1.0
    L = hi - lo
    start = guard + tip * 0.04 * L
    end = (hi if tip > 0 else lo)
    sl = np.linspace(start, end, 81)
    cen, half, thick_pos, thick_neg = [], [], [], []
    for a, b in zip(sl[:-1], sl[1:]):
        lo_, hi_ = min(a, b), max(a, b)
        sel = (pos[:, long_] >= lo_) & (pos[:, long_] <= hi_)
        if sel.sum() < 2:
            cen.append(np.nan); half.append(np.nan); thick_pos.append(np.nan); thick_neg.append(np.nan); continue
        w = pos[sel, wide]
        c = (w.min() + w.max()) / 2
        cen.append(c); half.append((w.max() - w.min()) / 2)
        # Thickness near each side: the spine of a single-edged blade is thicker than its edge.
        t = pos[sel, thin]
        side = w - c
        hw = max((w.max() - w.min()) / 2, 1e-6)
        pos_side = side > 0.5 * hw
        neg_side = side < -0.5 * hw
        thick_pos.append(np.ptp(t[pos_side]) if pos_side.sum() > 1 else np.nan)
        thick_neg.append(np.ptp(t[neg_side]) if neg_side.sum() > 1 else np.nan)
    # The blade outline per long coordinate, exact for the polygon: where the mesh edges cross the cut (sampling
    # vertices per slice put a wedge into the relief at the cutlass's kink).
    ea = np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
    ea = np.unique(np.sort(ea, 1), axis=0)
    pa, pb = pos[ea[:, 0]], pos[ea[:, 1]]
    la, lb = pa[:, long_], pb[:, long_]
    samples = np.linspace(start, end, 600)
    cen_s, half_s = np.full(len(samples), np.nan), np.full(len(samples), np.nan)
    for i, c in enumerate(samples):
        cross = (np.minimum(la, lb) <= c) & (np.maximum(la, lb) >= c) & (np.abs(la - lb) > 1e-9)
        if cross.sum() < 2:
            continue
        t = (c - la[cross]) / (lb[cross] - la[cross])
        w = pa[cross, wide] + t * (pb[cross, wide] - pa[cross, wide])
        cen_s[i], half_s[i] = (w.min() + w.max()) / 2, (w.max() - w.min()) / 2
    ok = np.isfinite(cen_s)
    order_l = np.argsort(samples[ok])
    ml = samples[ok][order_l]
    pc = np.interp(p[:, long_], ml, cen_s[ok][order_l])
    ph = np.interp(p[:, long_], ml, half_s[ok][order_l])
    edge_side = 1.0 if np.nanmean(thick_pos) < np.nanmean(thick_neg) else -1.0

    metal_mask = np.asarray(Image.open(os.path.join(maps, 'old_metal.png')).convert('L'), np.float64)[ys, xs] / 255
    along = (p[:, long_] - guard) * tip
    in_blade = (along > 0.04 * L) & (along < np.abs(end - guard))
    taper = smoothstep(0.04 * L, 0.09 * L, along)   # no step in the relief where the profile starts
    flat = np.abs(n[:, thin]) > 0.9
    blade = in_blade & flat & (metal_mask > 0.5)
    dd = np.clip((p[:, wide] - pc) / np.maximum(ph, 1e-6), -1.2, 1.2)

    # Tilt angle per texel (degrees) and its side (+1 toward +wide).
    soft = 0.04
    if prof['kind'] == 'diamond':
        ad = np.abs(dd)
        bevel = smoothstep(1 - prof['band'] - soft, 1 - prof['band'] + soft, ad)
        angle = prof['ridge'] * smoothstep(0.0, 0.06, ad) * (1 - bevel) + prof['bevel'] * bevel
        sign = np.sign(dd)
    else:
        e = dd * edge_side
        bevel = smoothstep(1 - prof['band'] - soft, 1 - prof['band'] + soft, e)
        angle = prof['bevel'] * bevel
        sign = np.full_like(dd, edge_side)
    angle = np.where(blade, angle * taper, 0.0)
    bevel = np.where(blade, bevel, 0.0)
    wv = np.zeros(3); wv[wide] = 1.0
    wperp = wv[None, :] - n * (n @ wv)[:, None]
    wperp /= np.maximum(np.linalg.norm(wperp, axis=1, keepdims=True), 1e-9)
    rad = np.radians(angle)
    tilted = n * np.cos(rad)[:, None] + wperp * (np.sin(rad) * sign)[:, None]

    # Tangent space with y along +rows (down the image): Meshy's convention.
    tx = dpdx[ft] - n * np.sum(dpdx[ft] * n, 1, keepdims=True)
    tx /= np.maximum(np.linalg.norm(tx, axis=1, keepdims=True), 1e-12)
    ty = dpdy[ft] - n * np.sum(dpdy[ft] * n, 1, keepdims=True) - tx * np.sum(dpdy[ft] * tx, 1, keepdims=True)
    ty /= np.maximum(np.linalg.norm(ty, axis=1, keepdims=True), 1e-12)
    ts = np.stack([np.sum(tilted * tx, 1), np.sum(tilted * ty, 1), np.sum(tilted * n, 1)], 1)

    meshy = np.asarray(Image.open(os.path.join(maps, 'normal_2k.png')).convert('RGB'), np.float64) / 127.5 - 1
    mv = meshy[ys, xs]
    blend = np.stack([mv[:, 0] + ts[:, 0], mv[:, 1] + ts[:, 1], mv[:, 2] * ts[:, 2]], 1)
    blend /= np.maximum(np.linalg.norm(blend, axis=1, keepdims=True), 1e-9)
    normal = meshy.copy()
    normal[ys, xs] = blend
    Image.fromarray(np.clip((normal + 1) * 127.5 + 0.5, 0, 255).astype(np.uint8)).save(os.path.join(maps, 'normal.png'))
    ridge_only = np.zeros((SIZE, SIZE, 3)); ridge_only[..., 2] = 1; ridge_only[ys, xs] = ts
    Image.fromarray(np.clip((ridge_only + 1) * 127.5 + 0.5, 0, 255).astype(np.uint8)).save(
        os.path.join(maps, 'debug_ridge_normal.png'))

    # Grinding grain: value noise across the blade at about 0.4 mm, slowly varying along it, from the 3D position.
    across = p[:, wide] / 0.0004 + value_noise(p[:, long_] / 0.02, 3) * 2.0
    grain = 0.6 * value_noise(across, 1) + 0.4 * value_noise(across * 2.3, 2)
    grain *= np.where(metal_mask > 0.5, 1.0, 0.0) * np.where(in_blade, 1.0, 0.4)

    # Colour: fine band on metal, metal albedo into the PBR range, honed bevels a little brighter, grain.
    colour = np.asarray(Image.open(os.path.join(maps, 'base_color_2k_graded.png')).convert('RGB'), np.float64) / 255
    blur = np.asarray(Image.fromarray((colour * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(FINE_SIGMA)),
                      np.float64) / 255
    metal_full = np.asarray(Image.open(os.path.join(maps, 'old_metal.png')).convert('L'), np.float64) / 255
    keep = np.where(metal_full > 0.5, FINE_KEEP, 1.0)[..., None]
    colour = blur + (colour - blur) * keep
    # Guards, pommels and fittings: Meshy's speckle there is coarser (leopard spots on item001's guard); their form
    # comes from the geometry and the relief, so the paint keeps only its broad colour.
    blade_full = np.zeros((SIZE, SIZE), bool); blade_full[ys, xs] = in_blade
    blur2 = np.asarray(Image.fromarray((colour * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(FITTING_SIGMA)),
                       np.float64) / 255
    fitting = ((metal_full > 0.5) & ~blade_full)[..., None]
    colour = np.where(fitting, blur2 + (colour - blur2) * 0.3, colour)
    lin = srgb_to_linear(colour)
    lum = lin @ np.array([0.2126, 0.7152, 0.0722])
    metal_tex = np.zeros((SIZE, SIZE), bool); metal_tex[ys, xs] = metal_mask > 0.5
    gain = TARGET / max(np.median(lum[metal_tex]), 1e-3)
    lin_m = lin * gain
    lin_m[ys, xs] *= (1 + 0.10 * bevel + 0.05 * grain)[:, None]
    blade_tex = np.zeros((SIZE, SIZE), bool); blade_tex[ys, xs] = in_blade & (metal_mask > 0.5)
    grey = (lin_m @ np.array([0.2126, 0.7152, 0.0722]))[..., None]
    lin_m = np.where(blade_tex[..., None], grey + (lin_m - grey) * BLADE_CHROMA, lin_m)
    lin = np.where(metal_full[..., None] > 0.5, np.minimum(lin_m, 0.95), lin)
    Image.fromarray((linear_to_srgb(lin) * 255 + 0.5).astype(np.uint8)).save(os.path.join(maps, 'basecolor.png'))

    # Metallic-roughness (glTF: G roughness, B metallic; R unused = 1).
    mm = np.asarray(Image.open(os.path.join(maps, 'metallic_2k.png')).convert('L'), np.float64) / 255
    rr = np.asarray(Image.open(os.path.join(maps, 'roughness_2k.png')).convert('L'), np.float64) / 255
    mblur = np.asarray(Image.fromarray((metal_full * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)),
                       np.float64) / 255
    metal = mblur * (0.85 + 0.15 * mm) + (1 - mblur) * 0.1 * mm
    lo_r, hi_r = np.percentile(rr[metal_tex], [5, 95])
    r_metal = 0.2 + 0.35 * np.clip((rr - lo_r) / max(hi_r - lo_r, 1e-3), 0, 1)
    r_metal[ys, xs] *= (1 - 0.35 * bevel)
    r_metal[ys, xs] += 0.04 * grain
    rough = np.where(metal_full > 0.5, r_metal, rr)
    mr = np.stack([np.ones_like(metal), np.clip(rough, 0.05, 1), metal], 2)
    Image.fromarray((mr * 255 + 0.5).astype(np.uint8)).save(os.path.join(maps, 'mr.png'))
    print('BLADE', icon, json.dumps({'axes': [int(long_), int(wide), int(thin)], 'tip': tip, 'edge_side': edge_side,
                                     'blade_texels': int(blade.sum()), 'metal_gain': round(float(gain), 2),
                                     'metal_lum_median_before': round(float(np.median(lum[metal_tex])), 3),
                                     'rough_metal_p5_p95_meshy': [round(float(lo_r), 2), round(float(hi_r), 2)]}))


if __name__ == '__main__':
    main(sys.argv[1])
