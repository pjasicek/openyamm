#!/usr/bin/env python3
"""See-through test for the head (follow-up 4, 2026-11-12). Orthographic renders of a runtime GLB's head and neck in the bind pose
(every LOD): a pixel inside the silhouette (any triangle) that no front-facing triangle covers shows the background with backface
culling (a hole, or a single-sided shell seen from behind). 120 directions (azimuth 15 deg steps, elevation -40..40), 0.4 mm pixels.
Usage: seethrough.py <glb> [lod ...] [--png out_prefix] -> holes per LOD, clustered by 3D entry point."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from glbio import Glb

PX = 0.0004; R = 0.15; CEN = np.array([0.0, 0.63, 0.0])


def lod_tris(g, mesh):
    out = []; ids = []
    for p in range(len(g.j['meshes'][mesh]['primitives'])):
        d = g.prim(mesh, p); out.append(d['POSITION'][d['idx']].astype(float)); ids.append(np.c_[np.full(len(d['idx']), p), np.arange(len(d['idx']))])
    return np.concatenate(out), np.concatenate(ids)


def view(T, az, el):
    a, e = np.radians(az), np.radians(el)
    fwd = -np.array([np.sin(a) * np.cos(e), np.sin(e), np.cos(a) * np.cos(e)])  # camera looks along fwd
    r = np.cross(fwd, [0, 1.0, 0]); r /= np.linalg.norm(r); u = np.cross(r, fwd)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); front = n @ fwd < 0
    P = T - CEN; X = (P @ r + R) / PX; Y = (R - P @ u) / PX; Dp = P @ fwd
    S = int(2 * R / PX)
    sil = Image.new('L', (S, S)); fr = Image.new('L', (S, S)); ds, df = ImageDraw.Draw(sil), ImageDraw.Draw(fr)
    for i in range(len(T)):
        poly = [(X[i, k], Y[i, k]) for k in range(3)]
        ds.polygon(poly, fill=255, outline=255)
        if front[i]: df.polygon(poly, fill=255, outline=255)
    sil, fr = np.asarray(sil) > 0, np.asarray(fr) > 0
    hole = sil & ~fr
    hole = ndimage.binary_opening(hole, iterations=1)  # single-pixel rasterisation gaps are not holes
    # nearest back-facing triangle per pixel (painter's order, far to near): what the hole looks through
    idimg = Image.new('I', (S, S), -1); di = ImageDraw.Draw(idimg); zc = Dp.mean(1)
    for i in np.nonzero(~front)[0][np.argsort(-zc[~front])]:
        di.polygon([(X[i, k], Y[i, k]) for k in range(3)], fill=int(i), outline=int(i))
    return hole, np.asarray(idimg), (r, u, fwd)


def main():
    args = [a for a in sys.argv[2:] if not a.startswith('--')]
    png = sys.argv[sys.argv.index('--png') + 1] if '--png' in sys.argv else None
    if png: args = [a for a in args if a != png]
    g = Glb(sys.argv[1]); lods = [int(a) for a in args] or [0, 1, 2, 3]
    res = {}
    for lod in lods:
        T, ids = lod_tris(g, lod); tot = 0; spots = []
        for el in (-40, -20, 0, 20, 40):
            for az in range(0, 360, 15):
                hole, idimg, (r, u, fwd) = view(T, az, el)
                lab, n = ndimage.label(hole)
                for k in range(1, n + 1):
                    yy, xx = np.nonzero(lab == k)
                    if len(yy) < 6: continue
                    tt = idimg[yy, xx]; tt = tt[tt >= 0]
                    if not len(tt): continue
                    ti = np.bincount(tt).argmax(); p = T[ti].mean(0)
                    spots.append((az, el, len(yy), p, tuple(ids[ti]))); tot += len(yy)
                if png and hole.any() and lod == lods[0]:
                    Image.fromarray((hole * 255).astype(np.uint8)).save(f'{png}_lod{lod}_az{az}_el{el}.png')
        print(f'LOD{lod}: hole pixels {tot} in {len(spots)} spots (0.16 mm2 each)')
        # group spots by the 1 cm cell of the triangle they look through
        cells = {}
        for az, el, npx, p, tid in spots:
            k = tuple(np.round(p / 0.01).astype(int)); c = cells.setdefault(k, [0, [], set()]); c[0] += npx; c[1].append((az, el)); c[2].add(tid[0])
        for k, (npx, vw, pr) in sorted(cells.items(), key=lambda kv: -kv[1][0])[:30]:
            print(f'   through ({k[0]/100:+.2f}, {k[1]/100:.2f}, {k[2]/100:+.2f}) prim {sorted(pr)} px {npx:6d} views {len(vw)} e.g. {vw[:4]}')
        res[lod] = tot
    print('TOTAL', res)


if __name__ == '__main__':
    main()
