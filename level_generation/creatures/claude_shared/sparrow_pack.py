"""Pack fixed UV islands into one square at one uniform scale with sparrow, for uv_atlas.py (packer='sparrow').
Runs outside Blender in claude_shared/sparrow_venv/py (setup in TEXTURE_QUALITY_PASS.md):

    sparrow_venv/py/bin/python -I sparrow_pack.py <in.npz> <out.npz> [--size 2048] [--height-share 1.0] [--sep 4]
        [--seconds 60] [--runs 5] [--fill 0.66] [--rotation continuous|90] [--sparrow <binary>]

in.npz: uv (M x 3 x 2, the charts at their final relative scale, anywhere; overlapping is fine) and island (M, one
label per rigid island: faces with the same label move together). out.npz: uv packed into [0, 1] (v 0..height_share),
k (final scale), log (JSON of the runs).

sparrow (Jeroen Gardeyn, KU Leuven, MIT, github.com/JeroenGar/sparrow, arXiv 2509.13329) is a state-of-the-art
2D irregular strip packer. Each island becomes its outline polygon in texels (union of its triangles, holes dropped,
0.3 px outward buffer, simplified at 0.25 px); `min_item_separation` keeps the gap (`--sep`, 2 x the margin per side,
as xatlas padding 2 leaves 4 empty texels). sparrow minimises the strip width at a fixed strip height
(height_share x size); the scale k is searched so that the width also fits the square: the first k gives the outlines
`--fill` of the strip area, then k_next = k sqrt(size / width), `--runs` runs of `--seconds` each, keeping the largest
k that fitted. sparrow is stochastic: never re-pack an upload that went to Meshy. On the uv_research_20261111 subjects
it reached 69.7-74.7 % atlas use against 50-58 % for xatlas on the same charts.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))


def outlines(uv, island, size):
    polys = []
    for i in range(island.max() + 1):
        tris = uv[island == i] * size
        area = np.abs((tris[:, 1, 0] - tris[:, 0, 0]) * (tris[:, 2, 1] - tris[:, 0, 1])
                      - (tris[:, 2, 0] - tris[:, 0, 0]) * (tris[:, 1, 1] - tris[:, 0, 1]))
        geom = unary_union([Polygon(t) for t, a in zip(tris, area) if a > 1e-12])
        geom = geom.buffer(0.3, join_style='mitre')
        if geom.geom_type != 'Polygon':
            geom = geom.convex_hull
        geom = Polygon(geom.exterior).simplify(0.25, preserve_topology=True)
        if not geom.is_valid:
            geom = geom.buffer(0)
        if geom.is_empty or geom.geom_type != 'Polygon' or geom.area < 1.0 or len(geom.exterior.coords) < 4:
            geom = shapely.MultiPoint(tris.reshape(-1, 2)).convex_hull.buffer(0.5, join_style='mitre')
        polys.append(geom)
    return polys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('src')
    parser.add_argument('dst')
    parser.add_argument('--size', type=int, default=2048)
    parser.add_argument('--height-share', type=float, default=1.0)
    parser.add_argument('--sep', type=float, default=4.0)
    parser.add_argument('--seconds', type=int, default=60)
    parser.add_argument('--runs', type=int, default=5)
    parser.add_argument('--fill', type=float, default=0.66)
    parser.add_argument('--rotation', default='continuous')
    parser.add_argument('--sparrow', default=os.path.join(HERE, 'sparrow_venv', 'bin', 'sparrow'))
    args = parser.parse_args()
    data = np.load(args.src)
    uv = data['uv'].astype(np.float64)
    island = np.unique(data['island'], return_inverse=True)[1].ravel()
    lo = uv.reshape(-1, 2).min(0)
    span = max(float((uv.reshape(-1, 2) - lo).max()), 1e-12)
    uv = (uv - lo) / span                      # only the relative scale matters
    S, H = args.size, args.size * args.height_share
    polys = outlines(uv, island, S)
    print(f'SPARROW {len(polys)} islands, {sum(len(p.exterior.coords) for p in polys)} outline vertices', flush=True)
    rotation = {'mode': 'continuous'} if args.rotation == 'continuous' else {'mode': 'stepped',
                                                                             'step': int(args.rotation)}

    def run(k):
        items = []
        for i, p in enumerate(polys):
            c = np.array(p.exterior.coords)[:-1] * k
            if not Polygon(c).exterior.is_ccw:
                c = c[::-1]
            items.append({'id': i, 'demand': 1, 'orientation': {'rotation': rotation},
                          'shape': {'type': 'simple_polygon', 'data': c.tolist()}})
        instance = {'name': 'uv', 'min_item_separation': args.sep, 'items': items, 'strip_height': float(H)}
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, 'uv.json'), 'w') as f:
                json.dump(instance, f)
            out = subprocess.run([args.sparrow, '-i', 'uv.json', '-t', str(args.seconds)], cwd=tmp,
                                 capture_output=True, text=True)
            if out.returncode:
                raise RuntimeError(out.stdout[-2000:] + out.stderr[-2000:])
            with open(os.path.join(tmp, 'output', 'final_uv.json')) as f:
                return json.load(f)['solution']

    k = float(np.sqrt(args.fill * S * H / sum(p.area for p in polys)))
    best, log, start = None, [], time.time()
    for _ in range(args.runs):
        t = time.time()
        sol = run(k)
        width = sol['strip_width']
        fits = width <= S
        log.append({'k': k, 'strip_width': width, 'fits': fits, 'seconds': round(time.time() - t)})
        print('SPARROW run', json.dumps(log[-1]), flush=True)
        if fits and (best is None or k > best[0]):
            best = (k, sol)
        k = k * np.sqrt(S / width) * (1.004 if fits else 0.996)
    if best is None:
        raise RuntimeError('sparrow: no run fitted the square')
    k, sol = best
    out = np.zeros_like(uv)
    for placed in sol['layout']['placed_items']:
        i = placed['item_id']
        a = np.radians(placed['transformation']['rotation'])
        tx, ty = placed['transformation']['translation']
        rot = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
        m = island == i
        out[m] = (uv[m] * S * k @ rot.T + [tx, ty]) / S
    if out.min() < -1e-3 or out[..., 0].max() > 1 + 1e-3 or out[..., 1].max() > args.height_share + 1e-3:
        raise RuntimeError(f'sparrow placed islands outside the square: {out.min()} {out.max()}')
    np.savez(args.dst, uv=np.clip(out, 0, 1), k=k, log=json.dumps(log))
    print(f'SPARROW best k {k:.4f}, {len(log)} runs, {time.time() - start:.0f} s', flush=True)


if __name__ == '__main__':
    sys.exit(main())
