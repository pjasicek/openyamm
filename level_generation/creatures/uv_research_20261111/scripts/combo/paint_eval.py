#!/usr/bin/env python3
"""Paint evaluation for the combined-layout study (uv_research_20261111, phase 2). Plain numpy/scipy/PIL
(sparrow_venv/py).

  paint_eval.py prep <meshy base colour png> <upload glb> <out 2K png>
      4K -> 2K once (Lanczos, sRGB as TEXTURE_QUALITY_PASS step 4), then every texel outside the upload's islands takes
      the nearest island texel (layout/RESULTS.md verdict A; texlib.pad). Prints the coverage.
  paint_eval.py bands <2K png> <upload glb> <out json>
      texture-space detail bands on luma inside the islands (2 px eroded), with mask-normalised Gaussians:
      speckle = G1 - G4 (1-4 px: isolated specks), blotch = G4 - G16 (the 4-16 px band of TEXTURE_QUALITY_PASS step 1).
      RMS and p99 of |band| in 8-bit levels.
  paint_eval.py shots <views dir> <out prefix> <view,...> <label=title> [<label=title> ...]
      identical-camera renders (paint_views.py): per view the same bands in screen space (speckle G0.7-G2.5,
      blotch G2.5-G10 px) on the pixels every label covers, and the pairwise differences between labels: mean |diff|
      (levels, RGB mean) and its low-pass part (G4 on both: colour/pattern drift) and high-pass part (the rest:
      grain); writes <prefix>.json and the sheet <prefix>.png (rows = views, columns = labels).
  paint_eval.py seams <2K png> <faces npz> <layout npz | -> <out json>
      seam step: for every UV seam edge, the colour on both sides at the same 3D points (t = 0.2..0.8, bilinear,
      RGB mean |diff| in levels), against a control step between points 1.5 texels apart inside the islands.
      faces npz = the trial's (pos, tri, vis, uv v-up); layout npz = sparrow's packed uv (glTF v-down), or '-' to use
      the faces npz's own (packed) uv.
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'layout'))
import uvlib  # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def coverage(glb, size):
    doc, binary = uvlib.read_glb(glb)
    tris = []
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            uv = uvlib.accessor(doc, binary, prim['attributes']['TEXCOORD_0'])
            idx = uvlib.accessor(doc, binary, prim['indices']).astype(np.int64).reshape(-1, 3)
            tris.append(uv[idx])
        break   # upload GLBs hold one mesh
    tris = np.concatenate(tris)
    return uvlib.conservative_labels(tris, np.zeros(len(tris), np.int32), size) >= 0


def masked_gauss(x, m, s):
    return ndimage.gaussian_filter(x * m, s) / np.maximum(ndimage.gaussian_filter(m, s), 1e-6)


def luma(rgb):
    return rgb[..., :3].astype(np.float64) @ np.array([0.2126, 0.7152, 0.0722])


def bands(y, mask, s0, s1, s2):
    m = mask.astype(np.float64)
    g0, g1, g2 = (masked_gauss(y, m, s) for s in (s0, s1, s2))
    inner = ndimage.binary_erosion(mask, iterations=2)
    sp, bl = (g0 - g1)[inner], (g1 - g2)[inner]
    return {'speckle_rms': round(float(np.sqrt((sp ** 2).mean())), 3),
            'speckle_p99': round(float(np.percentile(np.abs(sp), 99)), 2),
            'blotch_rms': round(float(np.sqrt((bl ** 2).mean())), 3),
            'blotch_p99': round(float(np.percentile(np.abs(bl), 99)), 2), 'pixels': int(inner.sum())}


def prep(src, glb, out):
    im = Image.open(src).convert('RGB')
    if im.size != (2048, 2048):
        im = im.resize((2048, 2048), Image.LANCZOS)
    a = np.asarray(im)
    cov = coverage(glb, 2048)
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    Image.fromarray(a[iy, ix]).save(out)
    print(json.dumps({'src_size': Image.open(src).size, 'coverage_pct': round(100 * float(cov.mean()), 2)}))


def tex_bands(png, glb, out):
    a = np.asarray(Image.open(png).convert('RGB'))
    cov = coverage(glb, a.shape[0])
    res = bands(luma(a), cov, 1.0, 4.0, 16.0)
    res['coverage_pct'] = round(100 * float(cov.mean()), 2)
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps(res))


def shots(views_dir, prefix, view_names, labels):
    labels = [l.split('=', 1) for l in labels]
    result = {'views': {}}
    rows = []
    for v in view_names:
        ims = {lab: np.asarray(Image.open(Path(views_dir) / f'{lab}_{v}.png').convert('RGBA')).astype(np.float64)
               for lab, _ in labels}
        common = np.logical_and.reduce([im[..., 3] > 250 for im in ims.values()])
        common = ndimage.binary_erosion(common, iterations=2)
        entry = {'bands': {}, 'pairs': {}}
        for lab, im in ims.items():
            entry['bands'][lab] = bands(luma(im), common, 0.7, 2.5, 10.0)
        m = common.astype(np.float64)
        low = {lab: np.stack([masked_gauss(im[..., c], m, 4.0) for c in range(3)], -1) for lab, im in ims.items()}
        for (a, _), (b, _) in itertools.combinations(labels, 2):
            d = np.abs(ims[a][..., :3] - ims[b][..., :3]).mean(-1)[common]
            dl = np.abs(low[a] - low[b]).mean(-1)[common]
            dh = np.abs((ims[a][..., :3] - low[a]) - (ims[b][..., :3] - low[b])).mean(-1)[common]
            entry['pairs'][f'{a}|{b}'] = {'mean': round(float(d.mean()), 2), 'low': round(float(dl.mean()), 2),
                                          'high': round(float(dh.mean()), 2)}
        result['views'][v] = entry
        rows.append((v, [Image.fromarray(im.astype(np.uint8), 'RGBA') for im in ims.values()]))
    json.dump(result, open(f'{prefix}.json', 'w'), indent=1)
    cell = max(max(i.size[0] for i in r[1]) for r in rows)
    pad, head = 6, 22
    sheet = Image.new('RGB', (pad + len(labels) * (cell + pad), head + len(rows) * (cell + head + pad)), (70, 70, 70))
    draw = ImageDraw.Draw(sheet)
    for j, (_, title) in enumerate(labels):
        draw.text((pad + j * (cell + pad) + 4, 4), title, fill=(255, 255, 255))
    for i, (v, ims) in enumerate(rows):
        y = head + i * (cell + head + pad)
        draw.text((pad + 4, y + 4), v, fill=(255, 230, 120))
        for j, im in enumerate(ims):
            if im.size[0] != cell:
                im = im.resize((cell, cell), Image.NEAREST)   # distant (mip) views shown with their real pixels
            tile = Image.new('RGBA', im.size, (110, 110, 110, 255))
            tile.alpha_composite(im)
            sheet.paste(tile.convert('RGB'), (pad + j * (cell + pad), y + head))
    sheet.save(f'{prefix}.png')
    print(json.dumps({v: {'pairs': e['pairs'], 'blotch': {k: b['blotch_rms'] for k, b in e['bands'].items()},
                          'speckle': {k: b['speckle_rms'] for k, b in e['bands'].items()}}
                      for v, e in result['views'].items()}, indent=None))


def sample(img, uv):
    """Bilinear sample at glTF uv (v down: row = v * size)."""
    h, w = img.shape[:2]
    x, y = uv[:, 0] * w - 0.5, uv[:, 1] * h - 0.5
    return np.stack([ndimage.map_coordinates(img[..., c], [y, x], order=1, mode='nearest') for c in range(3)], -1)


def seam_steps(png, faces, layout, out):
    img = np.asarray(Image.open(png).convert('RGB')).astype(np.float64)
    d = np.load(faces)
    pos, tri, vis = d['pos'], d['tri'], d['vis']
    if layout == '-':
        uv = d['uv'].astype(np.float64).copy()
        uv[..., 1] = 1 - uv[..., 1]
    else:
        uv = np.load(layout)['uv'].astype(np.float64)
    extent = float(np.ptp(pos, 0).max())
    edge = {}
    for f, t in enumerate(tri):
        for k in range(3):
            a, b = int(t[k]), int(t[(k + 1) % 3])
            edge.setdefault((min(a, b), max(a, b)), []).append(f)
    ts = np.linspace(0.2, 0.8, 4)
    steps, lens, viss = [], [], []
    for (a, b), fs in edge.items():
        if len(fs) != 2:
            continue
        f, g = fs
        ua = [uv[f][list(tri[f]).index(v)] for v in (a, b)]
        ub = [uv[g][list(tri[g]).index(v)] for v in (a, b)]
        if max(np.abs(ua[0] - ub[0]).max(), np.abs(ua[1] - ub[1]).max()) < 1e-6:
            continue
        pa = ua[0][None] + ts[:, None] * (ua[1] - ua[0])[None]
        pb = ub[0][None] + ts[:, None] * (ub[1] - ub[0])[None]
        steps.append(np.abs(sample(img, pa) - sample(img, pb)).mean())
        lens.append(np.linalg.norm(pos[a] - pos[b]) / extent)
        viss.append((vis[f] + vis[g]) / 2)
    steps, lens, viss = np.array(steps), np.array(lens), np.array(viss)
    # control: the same sampling across interior edges, the second side shifted 1.5 texels along the edge normal
    rng = np.random.default_rng(0)
    ctrl = []
    inner = [(e, fs) for e, fs in edge.items() if len(fs) == 2]
    for i in rng.choice(len(inner), min(4000, len(inner)), replace=False):
        (a, b), (f, g) = inner[i]
        ua = [uv[f][list(tri[f]).index(v)] for v in (a, b)]
        if max(np.abs(ua[0] - uv[g][list(tri[g]).index(a)]).max(), np.abs(ua[1] - uv[g][list(tri[g]).index(b)]).max()) > 1e-6:
            continue
        dvec = ua[1] - ua[0]
        nrm = np.array([-dvec[1], dvec[0]]) / max(np.linalg.norm(dvec), 1e-12) * 1.5 / img.shape[0]
        pa = ua[0][None] + ts[:, None] * dvec[None]
        ctrl.append(np.abs(sample(img, pa + nrm / 2) - sample(img, pa - nrm / 2)).mean())
    res = {'seam_edges': int(len(steps)), 'step_mean': round(float(steps.mean()), 2),
           'step_len_weighted': round(float((steps * lens).sum() / lens.sum()), 2),
           'step_x_visible_len': round(float((steps * lens * viss).sum()), 2),
           'visible_len': round(float((lens * viss).sum()), 2),
           'step_visible_weighted': round(float((steps * lens * viss).sum() / (lens * viss).sum()), 2),
           'control_step_1p5_texel': round(float(np.mean(ctrl)), 2)}
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps(res))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'prep':
        prep(*sys.argv[2:5])
    elif cmd == 'bands':
        tex_bands(*sys.argv[2:5])
    elif cmd == 'shots':
        shots(sys.argv[2], sys.argv[3], sys.argv[4].split(','), sys.argv[5:])
    elif cmd == 'seams':
        seam_steps(*sys.argv[2:6])
