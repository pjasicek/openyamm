#!/usr/bin/env python3
"""Pack fixed UV islands into one square with sparrow (MIT, github.com/JeroenGar/sparrow: jagua-rs collision engine,
state-of-the-art 2D irregular strip packing, 2025), at one uniform scale.

Each island becomes its outline polygon in texels (union of its triangles, holes dropped, 0.3 px outward buffer,
simplified); min_item_separation keeps the gap. sparrow minimises the strip width at a strip height of `size`;
the scale is searched so the width fits in `size` too (k_next = k sqrt(size / width), a few runs).

    sparrow_venv/py/bin/python sparrow_pack.py <layout npz> <out npz> [--sparrow <binary>] [--sep 5]
        [--rotation continuous|90] [--seconds 60] [--runs 5] [--size 2048] [--k0 1.0]

The binary and the Python environment (shapely, numpy, scipy, pillow) live in ../../../claude_shared/sparrow_venv/ (moved there 2026-11-12) (git-ignored):
bin/sparrow, py/, src_sparrow/ (github.com/JeroenGar/sparrow 67bfaf8, MIT) and the Rust 1.99.1 toolchain in rust/.
Rebuild offline (in claude_shared/): RUSTUP_HOME=sparrow_venv/rust/rustup CARGO_HOME=sparrow_venv/rust/cargo
sparrow_venv/rust/cargo/bin/cargo build --release --offline --features=only_final_svg (in src_sparrow/), then copy
target/release/sparrow to bin/.
"""
import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import uvlib  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument('layout')
parser.add_argument('out')
parser.add_argument('--sparrow', default=str(Path(__file__).resolve().parents[3] / 'claude_shared/sparrow_venv/bin/sparrow'))
parser.add_argument('--sep', type=float, default=5.0)
parser.add_argument('--rotation', default='continuous')
parser.add_argument('--seconds', type=int, default=60)
parser.add_argument('--runs', type=int, default=5)
parser.add_argument('--size', type=int, default=2048)
parser.add_argument('--k0', type=float, default=1.0)
parser.add_argument('--fill', type=float, default=None, help='first scale so the island outlines cover this share of the square (unpacked input)')
args = parser.parse_args()
d = np.load(args.layout)
pos, uv = d['pos'], d['uv']
isl = uvlib.island_ids(uv, pos)
S = args.size
polys = []
for i in range(isl.max() + 1):
    tris = uv[isl == i] * S
    geom = unary_union([Polygon(t) for t in tris if abs((t[1, 0] - t[0, 0]) * (t[2, 1] - t[0, 1]) - (t[2, 0] - t[0, 0]) * (t[1, 1] - t[0, 1])) > 1e-12])
    geom = geom.buffer(0.3, join_style='mitre')
    if geom.geom_type != 'Polygon':
        geom = geom.convex_hull
    geom = Polygon(geom.exterior).simplify(0.25, preserve_topology=True)
    if not geom.is_valid:
        geom = geom.buffer(0)
    if geom.is_empty or geom.geom_type != 'Polygon' or geom.area < 1.0 or len(geom.exterior.coords) < 4:
        geom = shapely.MultiPoint(tris.reshape(-1, 2)).convex_hull.buffer(0.5, join_style='mitre')
    polys.append(geom)
print(f'{len(polys)} islands, polygon vertices {sum(len(p.exterior.coords) for p in polys)}', flush=True)
if args.fill:
    args.k0 = float(np.sqrt(args.fill * S * S / sum(p.area for p in polys)))
    print(f'k0 {args.k0:.5f} from fill {args.fill}', flush=True)
rotation = {'mode': 'continuous'} if args.rotation == 'continuous' else {'mode': 'stepped', 'step': int(args.rotation)}


def run(k):
    items = []
    for i, p in enumerate(polys):
        c = np.array(p.exterior.coords)[:-1] * k
        if Polygon(c).exterior.is_ccw is False:
            c = c[::-1]
        items.append({'id': i, 'demand': 1, 'orientation': {'rotation': rotation},
                      'shape': {'type': 'simple_polygon', 'data': c.tolist()}})
    inst = {'name': 'uv', 'min_item_separation': args.sep, 'items': items, 'strip_height': float(S)}
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, 'uv.json').write_text(json.dumps(inst))
        t = time.time()
        r = subprocess.run([args.sparrow, '-i', 'uv.json', '-t', str(args.seconds)], cwd=tmp, capture_output=True,
                           text=True)
        if r.returncode:
            raise RuntimeError(r.stdout[-2000:] + r.stderr[-2000:])
        sol = json.loads(Path(tmp, 'output/final_uv.json').read_text())['solution']
    return sol, time.time() - t


best = None
k = args.k0
total = 0.0
log = []
for n in range(args.runs):
    sol, sec = run(k)
    total += sec
    width = sol['strip_width']
    ok = width <= S
    log.append({'k': k, 'strip_width': width, 'fits': ok, 'seconds': round(sec)})
    print(json.dumps(log[-1]), flush=True)
    if ok and (best is None or k > best[0]):
        best = (k, sol)
    k = k * np.sqrt(S / width) * (1.004 if ok else 0.996)
if best is None:
    raise SystemExit('nothing fitted')
k, sol = best
out = np.zeros_like(uv)
for placed in sol['layout']['placed_items']:
    i = placed['item_id']
    a = np.radians(placed['transformation']['rotation'])
    tx, ty = placed['transformation']['translation']
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    m = isl == i
    p = uv[m] * S * k
    out[m] = (p @ R.T + [tx, ty]) / S
assert out.min() > -1e-3 and out.max() < 1 + 1e-3, (out.min(), out.max())
np.savez(args.out, pos=pos, uv=np.clip(out, 0, 1), seconds=total, margin=args.sep, k=k, log=json.dumps(log))
print(f'best k {k:.4f} (area x{k * k:.3f}) total {total:.0f}s')
