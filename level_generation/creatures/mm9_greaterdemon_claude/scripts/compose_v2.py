#!/usr/bin/env python3
"""Texture sets v2 (2026-10-30 rework): body (2K base, 1K normal and ORM) from meshy/retexture_v2 on the xatlas UVs, and
the 1K head set from the two head-only retextures (main head, left arm head; the right arm head is the mirrored left
one, mirror_armhead.py, and shares its HeadUV texels; the right wrist left between the forearm and that copy, head 4,
is painted from the left arm head's or the left forearm's texels through work/armhead_mirror_2k.npz,
armhead_mirror_map.py). One MM9
skin, no tiers, so no region mask or ramps.

Usage: compose_v2.py <stage>
  body  -> textures/gdemon_v2_basecolor.png (graded next by grade_basecolor.py), gdemon_v2_normal_1k.png,
           gdemon_v2_metal_rough_1k.png (R AO, G roughness, B 0), gdemon_v2_material_classes.png
  head  -> textures/gdemon_v2_head_basecolor_2k.png (graded next, then `headfinal`), gdemon_v2_head_normal_1k.png,
           gdemon_v2_head_metal_rough_1k.png, gdemon_v2_head_material_classes.png; the head luminance is matched to
           the body across the neck seam (median luminance of the texels along the shared edges, both ungraded: they
           are graded the same way afterwards)
  headfinal -> textures/gdemon_v2_head_basecolor_1k.png (the graded 2K head base resized)
Inputs: work/uv_v2_tris.npz (dump_uv_v2.py), work/armhead_mirror_2k.npz, textures/gdemon_ao_v2_2k.png,
textures/gdemon_head_ao_v2_1k.png, meshy/retexture_v2, meshy/head_retexture_v1, meshy/armhead_retexture_v1.
Material classes (CLAUDE_CREATURE_TEXTURES.md): 1 hide, 3 membrane, 4 spike/horn, 5 tooth, 6 eye, 7 mouth,
11 the dark chitin armour plates (low-saturation dark texels on the hide)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
T = HERE / 'textures'
D = np.load(HERE / 'work' / 'uv_v2_tris.npz')
STAGE = sys.argv[1]
W3 = np.array([0.2126, 0.7152, 0.0722], np.float32)


def raster(uvs, labels, n):
    """Label raster (0 = empty) of triangles uvs (T,3,2) at n x n, row 0 = v 1."""
    out = np.zeros((n, n), np.int32)
    for t, lab in zip(uvs * n, labels):
        x0, y0 = np.floor(t.min(0)).astype(int); x1, y1 = np.ceil(t.max(0)).astype(int)
        gx, gy = np.meshgrid(np.arange(max(x0, 0), min(x1, n)) + 0.5, np.arange(max(y0, 0), min(y1, n)) + 0.5)
        a, b, c = t
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12 or gx.size == 0:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        ins = (l1 >= -1e-3) & (l2 >= -1e-3) & (1 - l1 - l2 >= -1e-3)
        out[n - 1 - gy[ins].astype(int), gx[ins].astype(int)] = lab
    return out


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def load(p, mode='RGB', size=None):
    im = Image.open(p).convert(mode)
    if size and im.size != (size, size):
        im = im.resize((size, size), Image.LANCZOS)
    return np.asarray(im).astype(np.float32)


def save(arr, p, size=None):
    im = Image.fromarray(np.clip(np.round(arr), 0, 255).astype(np.uint8))
    if size and im.size != (size, size):
        im = im.resize((size, size), Image.LANCZOS)
    im.save(T / p, optimize=True)
    print('WROTE', p, im.size)


def classes(base, lab_piece, n):
    """Material class map from part labels and colour (see the docstring)."""
    rgb = base / 255
    lum = rgb @ W3
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    hue_red = (rgb[..., 0] > rgb[..., 1] * 1.6) & (rgb[..., 0] > 0.25)
    out = np.zeros(lab_piece.shape, np.uint8)
    out[lab_piece > 0] = 1
    out[(lab_piece == 1) & (sat < 0.18) & (lum < 0.45)] = 11
    out[lab_piece == 3] = 3
    out[lab_piece == 2] = 4
    out[lab_piece == 5] = 5
    out[(lab_piece == 1) & hue_red] = 7
    return Image.fromarray(out).resize((n, n), Image.NEAREST)


if STAGE == 'body':
    bodyf = D['head'] == 0
    # part label: 1 hide (piece 0, 4 wing bones), 2 spikes/teeth, 3 membrane
    part = np.select([D['piece'] == 3, D['piece'] == 2], [3, 2], 1)[bodyf]
    lab = raster(D['uv'][bodyf], part, 2048)
    cov = lab > 0
    M = HERE / 'meshy' / 'retexture_v2'
    base = load(M / 'texture_urls_0_base_color.png', size=2048)
    save(pad(base, cov), 'gdemon_v2_basecolor.png')
    nrm = load(M / 'texture_urls_0_normal.png', size=2048)
    save(pad(nrm, cov), 'gdemon_v2_normal_1k.png', 1024)
    rough = np.clip(load(M / 'texture_urls_0_roughness.png', 'L', 2048) / 255, 0.45, 0.85) * 255
    ao = load(T / 'gdemon_ao_v2_2k.png', 'L', 2048)
    orm = np.stack([pad(ao, cov), pad(rough, cov), np.zeros_like(ao)], -1)
    save(orm, 'gdemon_v2_metal_rough_1k.png', 1024)
    classes(base, lab, 1024).save(T / 'gdemon_v2_material_classes.png')
    print('BODY coverage', round(float(cov.mean()), 3))
elif STAGE == 'head':
    N = 2048
    hf = np.isin(D['head'], (1, 2, 4))      # head 3 (mirrored right arm head) reuses the left head's texels
    hid = D['head'][hf]
    lab_head = raster(D['huv'][hf], hid, N)
    lab_piece = raster(D['huv'][hf], np.where(D['piece'][hf] == 2, 2, 1), N)
    MJ, AJ = HERE / 'meshy' / 'head_retexture_v1', HERE / 'meshy' / 'armhead_retexture_v1'
    MM = np.load(HERE / 'work' / 'armhead_mirror_2k.npz')
    out = {}
    for key, fname, mode in (('base', 'texture_urls_0_base_color.png', 'RGB'),
                             ('normal', 'texture_urls_0_normal.png', 'RGB'),
                             ('rough', 'texture_urls_0_roughness.png', 'L')):
        main, arm = load(MJ / fname, mode, N), load(AJ / fname, mode, N)
        m1, m2 = lab_head == 1, lab_head == 2
        if mode == 'RGB':
            m1, m2 = m1[..., None], m2[..., None]
        img = np.where(m1, main, np.where(m2, arm, 0))
        # the right wrist (head 4): bilinear samples of the left arm head's retexture at the mirrored surface points
        # (or of the body retexture where the mirror image lands on the left forearm)
        sx, sy = MM['src_uv'][:, 0] * N - 0.5, (1 - MM['src_uv'][:, 1]) * N - 0.5
        bodymap = load(HERE / 'meshy' / 'retexture_v2' / fname, mode, N)
        smp = []
        for srcimg in (bodymap, arm):
            if mode == 'RGB':
                smp.append(np.stack([ndimage.map_coordinates(srcimg[..., c], [sy, sx], order=1, mode='nearest')
                                     for c in range(3)], -1))
            else:
                smp.append(ndimage.map_coordinates(srcimg, [sy, sx], order=1, mode='nearest'))
        sel = MM['src_head'] == 1
        smp = np.where(sel[:, None] if mode == 'RGB' else sel, smp[1], smp[0])
        if key == 'normal':
            n = smp / 127.5 - 1
            n[:, 1] *= -1                                   # Meshy normal maps are +y down
            n = np.einsum('nij,nj->ni', MM['M'], n)
            n[:, 1] *= -1
            n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-6
            n[:, 2] = np.abs(n[:, 2])
            smp = (n + 1) * 127.5
        img[MM['dst'][:, 0], MM['dst'][:, 1]] = smp
        out[key] = img
    cov = lab_head > 0
    # seam gain of the main head: body vs head luminance on the texels of the shared neck edges
    body_u = load(T / 'gdemon_v2_basecolor.png', size=2048)
    pos = D['pos'].round(4)
    edges = {}
    for ti in range(len(pos)):
        for k in range(3):
            a, b = tuple(pos[ti][k]), tuple(pos[ti][(k + 1) % 3])
            edges.setdefault(tuple(sorted((a, b))), []).append((ti, k))
    measured = {}
    for h in (1, 2):
        hv, bv = [], []
        for e, owners in edges.items():
            hs = [o for o in owners if D['head'][o[0]] == h]
            bs = [o for o in owners if D['head'][o[0]] == 0 and D['piece'][o[0]] == 0]
            if not hs or not bs:
                continue
            (ht, hk), (bt, bk) = hs[0], bs[0]
            for w in (0.25, 0.5, 0.75):
                hu = D['huv'][ht][hk] * (1 - w) + D['huv'][ht][(hk + 1) % 3] * w
                bu = D['uv'][bt][bk] * (1 - w) + D['uv'][bt][(bk + 1) % 3] * w
                # a little toward each triangle's centroid, so the sample is inside its own island
                hu = hu + (D['huv'][ht].mean(0) - hu) * 0.04
                bu = bu + (D['uv'][bt].mean(0) - bu) * 0.04
                hv.append(out['base'][int((1 - hu[1]) * N), int(hu[0] * N)] @ W3)
                bv.append(body_u[int((1 - bu[1]) * 2048), int(bu[0] * 2048)] @ W3)
        measured[h] = float(np.clip(np.median(bv) / max(np.median(hv), 1e-3), 0.6, 1.6)) if hv else 1.0
    # the arm heads meet the arm at the wrist band (dark armour on the arm, the head's own band on the head): a change
    # of material, not of skin, so their measured ratio is not a seam gain; they keep 1
    gains = {1: measured[1], 2: 1.0, 4: 1.0}
    gmap = np.ones((N, N), np.float32)
    for h, g in gains.items():
        gmap[lab_head == h] = g
    base = out['base'] * gmap[..., None]
    print('HEAD seam gains', {h: round(g, 3) for h, g in gains.items()}, 'measured', {h: round(g, 3) for h, g in measured.items()})
    save(pad(base, cov), 'gdemon_v2_head_basecolor_2k.png')
    save(pad(out['normal'], cov), 'gdemon_v2_head_normal_1k.png', 1024)
    rough = np.clip(out['rough'] / 255, 0.4, 0.85) * 255
    ao = load(T / 'gdemon_head_ao_v2_1k.png', 'L', N)
    save(np.stack([pad(ao, cov), pad(rough, cov), np.zeros_like(ao)], -1), 'gdemon_v2_head_metal_rough_1k.png', 1024)
    classes(base, lab_piece, 1024).save(T / 'gdemon_v2_head_material_classes.png')
    (T / 'gdemon_v2_head_seam_gains.txt').write_text(f'used {gains}\nmeasured {measured}\n')
elif STAGE == 'headfinal':
    save(load(T / 'gdemon_v2_head_basecolor_2k_graded.png'), 'gdemon_v2_head_basecolor_1k.png', 1024)
