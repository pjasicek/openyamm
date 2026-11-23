#!/usr/bin/env python3
"""Open containers with no inside: the decoration models the Xeen maps place, checked for surfaces seen from behind.

Family F39 of the user's play feedback (devdocs/xeen/reviews/PLAYER_FEEDBACK_20261123.md): XD-02's cook cauldron
(cauld00, engine/models/mm6_deco_cauldron_pot.glb) showed the floor through its rim, because the brew disc under the
rim faced down and the renderer culls the back faces of single-sided materials. The same fault hides the inside of
any open shell: a pot, barrel, bucket, well, trough or chest whose inner wall or contents were never modelled, or
were modelled facing the wrong way.

Each model is drawn orthographically (a small software z-buffer) from straight above and from eight directions at
30 and 60 degrees down, the way a player looks at a prop on the floor. A pixel is a fault when the nearest opaque
surface there is the back of a single-sided triangle (glTF counter-clockwise front, material without doubleSided):
the game skips it and shows whatever lies behind, usually the floor. BLEND and MASK materials (flames, cards,
foliage) are skipped as occluders. A model fails when, in any view of a checked LOD, at least FAULT_FRACTION of its
covered pixels and at least FAULT_PIXELS pixels show a back face. The line names the materials seen from behind.

Scope: by default the containers and fire fixtures, the props a player looks into (CONTAINER_WORDS in the decoration's
name or hint or the model's file name: cauldrons, pots, barrels, bowls, braziers, fountains, campfires, candles,
sconces, chests ...; closed casks and kegs are not), at LOD 0, the level drawn up close. `--all` checks every placed model, `--lods all` every LOD
level: these also list other faults of the same kind (single-sided foliage cards seen from above, decimated far
LODs, inside-out chain links) that are not open interiors.

Which models: every decoration the Xeen maps place (BLV entities through `oymap export`, ODM entities from the
scene), looked up by name or decoration_list_id in the merged decoration table (engine + worlds/xeen rows), bound
through engine/models/indoor_decorations.yml (BLV) or decorations.yml (ODM) as extended by worlds/xeen/models/
(model, free_model, parts, animated), plus their decoration_overlays.yml state models, plus every
worlds/xeen/models/xeen_deco_*.glb. Creature bodies are not checked.

Usage:
  tools/xeen/check_open_interiors.py [--assets ROOT] [--maps xeen_xd02,xeen_x1] [--all] [--lods 0|all]
                                     [--cache DIR] [--verbose]
  tools/xeen/check_open_interiors.py --glb a.glb [b.glb ...]      (these models, whatever their kind)

Prints one line per faulty model (worst view, its back-face share, the maps placing it) and exits 1 on any fault.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
OYMAP = ROOT / 'openyamm-studio' / 'build-xeen' / 'oymap'
FAULT_FRACTION = 0.01
FAULT_PIXELS = 12
RESOLUTION = 128
ELEVATIONS = (30.0, 60.0)
AZIMUTHS = 8
CONTAINER_WORDS = re.compile(r'cauldron|kettle|\bpot\b|_pot|barrel|barel|bucket|\bwell|trough|bowl|basket'
                             r'|\bvat|brazi|brzier|fountain|chest|crate|\burn\b|\bjar\b|\btub\b|fire|fyr|flamb'
                             r'|sconce|candle|cndl|goblet|\bcup\b|basin|\bfont\b|emberfont|planter|cauld')

COMPONENTS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
DTYPES = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NORMALISE = {5120: 127.0, 5121: 255.0, 5122: 32767.0, 5123: 65535.0}


# ---------------------------------------------------------------------------------------------------------- glTF

def read_glb(path: Path):
    data = path.read_bytes()
    document, binary, offset = None, b'', 12
    while offset < len(data):
        size, kind = struct.unpack_from('<II', data, offset)
        chunk = data[offset + 8:offset + 8 + size]
        if kind == 0x4E4F534A:
            document = json.loads(chunk)
        elif kind == 0x004E4942:
            binary = chunk
        offset += 8 + size
    return document, binary


def accessor(document, binary, index):
    acc = document['accessors'][index]
    n = COMPONENTS[acc['type']]
    dtype = np.dtype(DTYPES[acc['componentType']])
    count = acc['count']
    if 'bufferView' not in acc:
        return np.zeros((count, n), dtype=np.float32)
    view = document['bufferViews'][acc['bufferView']]
    start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    stride = view.get('byteStride') or n * dtype.itemsize
    raw = np.frombuffer(binary, dtype=np.uint8, count=stride * (count - 1) + n * dtype.itemsize, offset=start)
    rows = np.lib.stride_tricks.as_strided(raw, shape=(count, n * dtype.itemsize), strides=(stride, 1))
    values = rows.copy().view(dtype).reshape(count, n)
    if acc.get('normalized') and acc['componentType'] in NORMALISE:
        return np.maximum(values.astype(np.float64) / NORMALISE[acc['componentType']], -1.0)
    return values.astype(np.float64)


def node_matrix(node):
    if 'matrix' in node:
        return np.array(node['matrix'], dtype=np.float64).reshape(4, 4).T
    t = np.eye(4)
    t[:3, 3] = node.get('translation', [0, 0, 0])
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    r = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    s = np.diag(node.get('scale', [1, 1, 1]))
    m = np.eye(4)
    m[:3, :3] = r @ s
    return t @ m


def lod_levels(path: Path):
    """[(level, triangles (T,3,3), single_sided (T,) bool, material names (T,))] of the model: level 0 is every mesh
    node, level k the nodes' k-th openyamm_lods mesh (a node without one keeps its last). Opaque materials only."""
    document, binary = read_glb(path)
    materials = document.get('materials', [])
    parents = {}
    for i, node in enumerate(document.get('nodes', [])):
        for child in node.get('children', []):
            parents[child] = i

    def world(i):
        m = node_matrix(document['nodes'][i])
        while i in parents:
            i = parents[i]
            m = node_matrix(document['nodes'][i]) @ m
        return m

    nodes = [(i, n) for i, n in enumerate(document.get('nodes', [])) if 'mesh' in n]
    chains = []
    for i, n in nodes:
        lods = document['meshes'][n['mesh']].get('extras', {}).get('openyamm_lods', [])
        chains.append((np.eye(4) if 'skin' in n else world(i), [n['mesh']] + list(lods)))
    depth = max((len(c) for _, c in chains), default=0)
    levels = []
    for level in range(depth):
        tris, single, names = [], [], []
        for matrix, chain in chains:
            mesh = document['meshes'][chain[min(level, len(chain) - 1)]]
            for prim in mesh['primitives']:
                if prim.get('mode', 4) != 4 or 'POSITION' not in prim['attributes']:
                    continue
                material = materials[prim['material']] if 'material' in prim else {}
                if material.get('alphaMode', 'OPAQUE') != 'OPAQUE':
                    continue
                pos = accessor(document, binary, prim['attributes']['POSITION'])[:, :3]
                pos = pos @ matrix[:3, :3].T + matrix[:3, 3]
                if 'indices' in prim:
                    idx = accessor(document, binary, prim['indices']).astype(np.int64).reshape(-1, 3)
                else:
                    idx = np.arange(len(pos)).reshape(-1, 3)
                if np.linalg.det(matrix[:3, :3]) < 0:
                    idx = idx[:, ::-1]
                tris.append(pos[idx])
                single.append(np.full(len(idx), not material.get('doubleSided', False)))
                names.append(np.full(len(idx), material.get('name', '?'), dtype=object))
        if tris:
            levels.append((level, np.concatenate(tris), np.concatenate(single), np.concatenate(names)))
    return levels


# ------------------------------------------------------------------------------------------------- rasteriser

def views():
    yield 'top', np.array([0.0, -1.0, 0.0])
    for elevation in ELEVATIONS:
        e = math.radians(elevation)
        for k in range(AZIMUTHS):
            a = 2 * math.pi * k / AZIMUTHS
            # glTF y up; the eye looks down along -y tilted toward (x, z) = -(cos a, sin a).
            yield f'{int(elevation)}deg_az{int(math.degrees(a))}', np.array(
                [-math.cos(a) * math.cos(e), -math.sin(e), -math.sin(a) * math.cos(e)])


def raster(tris: np.ndarray, single: np.ndarray, names: np.ndarray, direction: np.ndarray):
    """(covered pixels, back-face pixels, {material: back-face pixels}) of the opaque triangles seen
    orthographically along direction."""
    d = direction / np.linalg.norm(direction)
    helper = np.array([0.0, 0.0, 1.0]) if abs(d[1]) > 0.99 else np.array([0.0, 1.0, 0.0])
    right = np.cross(d, helper)
    right /= np.linalg.norm(right)
    up = np.cross(right, d)
    sx, sy, sz = tris @ right, tris @ up, tris @ d          # (T, 3) each; smaller z is nearer the eye
    normal = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    area = np.linalg.norm(normal, axis=1)
    keep = area > 1e-12
    sx, sy, sz, normal, single, names = sx[keep], sy[keep], sz[keep], normal[keep], single[keep], names[keep]
    back = (normal @ d > 0) & single
    lo = np.array([sx.min(), sy.min()])
    extent = max(sx.max() - lo[0], sy.max() - lo[1], 1e-6)
    pixel = extent / RESOLUTION
    size = RESOLUTION + 2
    eps = extent * 2e-4
    fx, fy = (sx - lo[0]) / pixel, (sy - lo[1]) / pixel     # pixel centres at integer + 0.5
    x0 = np.clip(np.ceil(fx.min(1) - 0.5).astype(int), 0, size - 1)
    x1 = np.clip(np.floor(fx.max(1) - 0.5).astype(int), 0, size - 1)
    y0 = np.clip(np.ceil(fy.min(1) - 0.5).astype(int), 0, size - 1)
    y1 = np.clip(np.floor(fy.max(1) - 0.5).astype(int), 0, size - 1)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    span = np.maximum(w, h)
    nearest = np.full(size * size, np.inf)
    pix_all, depth_all, ok_all, tri_all = [], [], [], []
    for k in (2, 4, 8, 16, 32, 64, 128, 256):
        sel = np.nonzero((span > 0) & (span <= k) & (span > k // 2 if k > 2 else span > 0))[0]
        if len(sel) == 0:
            continue
        ox, oy = np.meshgrid(np.arange(k), np.arange(k))
        ox, oy = ox.ravel(), oy.ravel()
        chunk = max(1, 2_000_000 // (k * k))
        for start in range(0, len(sel), chunk):
            t = sel[start:start + chunk]
            px = x0[t, None] + ox[None, :]
            py = y0[t, None] + oy[None, :]
            valid = (px <= x1[t, None]) & (py <= y1[t, None])
            cx, cy = px + 0.5, py + 0.5
            ax, ay = fx[t, 0, None], fy[t, 0, None]
            bx, by = fx[t, 1, None], fy[t, 1, None]
            qx, qy = fx[t, 2, None], fy[t, 2, None]
            den = (by - qy) * (ax - qx) + (qx - bx) * (ay - qy)
            den = np.where(np.abs(den) < 1e-12, np.nan, den)
            l0 = ((by - qy) * (cx - qx) + (qx - bx) * (cy - qy)) / den
            l1 = ((qy - ay) * (cx - qx) + (ax - qx) * (cy - qy)) / den
            l2 = 1 - l0 - l1
            tol = -1e-3
            inside = valid & (l0 >= tol) & (l1 >= tol) & (l2 >= tol)
            z = l0 * sz[t, 0, None] + l1 * sz[t, 1, None] + l2 * sz[t, 2, None]
            rows, cols = np.nonzero(inside)
            pix = py[rows, cols] * size + px[rows, cols]
            depth = z[rows, cols]
            pix_all.append(pix)
            depth_all.append(depth)
            ok_all.append(~back[t][rows])
            tri_all.append(t[rows])
    if not pix_all:
        return 0, 0, {}
    pix = np.concatenate(pix_all)
    depth = np.concatenate(depth_all)
    ok = np.concatenate(ok_all)
    tri = np.concatenate(tri_all)
    np.minimum.at(nearest, pix, depth)
    near = depth <= nearest[pix] + eps
    good = np.zeros(size * size, dtype=bool)
    good[pix[near & ok]] = True
    covered = np.isfinite(nearest)
    faulty = covered & ~good
    hit = near & faulty[pix]
    culprits = {}
    for name, count in zip(*np.unique(names[tri[hit]].astype(str), return_counts=True)):
        culprits[str(name)] = int(count)
    return int(covered.sum()), int(faulty.sum()), culprits


def check_model(path: Path, lods='all'):
    """[(level, view, covered, back, {material: back-face hits})] of the worst view of each LOD level."""
    worst = []
    for level, tris, single, names in lod_levels(path):
        if lods != 'all' and level != int(lods):
            continue
        best = None
        for name, direction in views():
            covered, back, culprits = raster(tris, single, names, direction)
            if covered and (best is None or back / covered > best[3] / max(best[2], 1)):
                best = (level, name, covered, back, culprits)
        if best:
            worst.append(best)
    return worst


def is_fault(covered, back):
    return covered > 0 and back >= FAULT_PIXELS and back / covered >= FAULT_FRACTION


# ------------------------------------------------------------------------------------------------- placements

def decoration_table(assets: Path):
    """(row -> (name, hint), name -> row) of the merged decoration table."""
    by_id, by_name = {}, {}
    for table in (assets / 'engine' / 'data_tables' / 'decoration_data.txt',
                  assets / 'worlds' / 'xeen' / 'models' / 'decoration_data.txt'):
        for line in table.read_text(errors='replace').splitlines():
            cells = line.split('\t')
            if len(cells) < 2 or not cells[0].strip().isdigit():
                continue
            row = int(cells[0]) - 1
            name = cells[1].strip().lower()
            by_id[row] = (name, cells[2].strip().lower() if len(cells) > 2 else '')
            by_name.setdefault(name, row)
    return by_id, by_name


def bindings(assets: Path, manifest: str, stem: str):
    """name -> [model paths] of one binding manifest, the Xeen world's entries replacing the engine's."""
    result = {}
    for scope in ('engine', 'worlds/xeen'):
        path = assets / scope / 'models' / manifest
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text()) or {}
        own = {}
        for entry in data.get('decorations') or []:
            name = str(entry.get('name', '')).lower()
            maps = entry.get('maps')
            if maps and f'{stem}.blv' not in maps and f'{stem}.odm' not in maps:
                continue
            models = [entry.get('model'), entry.get('free_model'), entry.get('animated')] + list(entry.get('parts')
                                                                                                    or [])
            own.setdefault(name, []).extend(m for m in models if isinstance(m, str))
        result.update(own)
    return result


def overlays(assets: Path):
    result = {}
    for scope in ('engine', 'worlds/xeen'):
        path = assets / scope / 'models' / 'decoration_overlays.yml'
        if not path.exists():
            continue
        for entry in (yaml.safe_load(path.read_text()) or {}).get('overlays') or []:
            result[str(entry.get('name', '')).lower()] = [m for m in entry.get('states') or [] if isinstance(m, str)]
    return result


def map_entities(path: Path, assets: Path, cache: Path):
    if path.suffix == '.odm':
        scene = path.with_suffix('.scene.yml')
        if not scene.exists():
            return []
        data = yaml.load(scene.read_text(), Loader=getattr(yaml, 'CSafeLoader', yaml.SafeLoader))
        return [(e.get('name', ''), e.get('decoration_list_id', -1)) for e in data.get('entities') or []]
    out = cache / (path.name + '.json')
    if not out.exists() or out.stat().st_mtime < path.stat().st_mtime:
        cache.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(OYMAP), 'export', str(path), '--world', 'xeen', '--assets', str(assets), '--out',
                        str(out)], capture_output=True, timeout=600, check=True)
    data = json.loads(out.read_text())
    return [(e.get('name', ''), e.get('decoration_list_id', -1)) for e in data['map'].get('entities') or []]


def placed_models(assets: Path, stems, cache: Path, everything=False):
    """model path (assets-relative) -> {map stem: set of decoration names}; only container-like ones unless
    everything."""
    by_id, by_name = decoration_table(assets)
    over = overlays(assets)
    models = {}
    for path in sorted((assets / 'worlds' / 'xeen' / 'maps').glob('*')):
        if path.suffix not in ('.blv', '.odm') or (stems and path.stem not in stems):
            continue
        bound = bindings(assets, 'indoor_decorations.yml' if path.suffix == '.blv' else 'decorations.yml', path.stem)
        for name, list_id in map_entities(path, assets, cache):
            name = name.strip().lower()
            row = by_name[name] if name in by_name else list_id
            if row not in by_id:
                continue
            deco, hint = by_id[row]
            for model in bound.get(deco, []) + over.get(deco, []):
                if everything or CONTAINER_WORDS.search(f'{deco} {hint} {Path(model).stem}'):
                    models.setdefault(model, {}).setdefault(path.stem, set()).add(deco)
    if not stems:
        for glb in sorted((assets / 'worlds' / 'xeen' / 'models').glob('xeen_deco_*.glb')):
            if everything or CONTAINER_WORDS.search(glb.stem):
                models.setdefault(str(glb.relative_to(assets)), {})
    return models


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--assets', default=str(ROOT / 'assets_dev'))
    parser.add_argument('--maps', default='')
    parser.add_argument('--cache', default=str(ROOT / 'output' / 'xeen_fb' / 'open_interiors_cache'))
    parser.add_argument('--glb', nargs='+')
    parser.add_argument('--all', action='store_true', help='every placed model, not only containers')
    parser.add_argument('--lods', default='0', help="the LOD level to check, or 'all' (default 0)")
    parser.add_argument('--verbose', action='store_true', help='print every model checked')
    args = parser.parse_args()
    assets = Path(args.assets)
    if args.glb:
        targets = {g: {} for g in args.glb}
    else:
        stems = {s.strip() for s in args.maps.split(',') if s.strip()}
        targets = placed_models(assets, stems, Path(args.cache), args.all)
    faults = 0
    for model, maps in sorted(targets.items()):
        path = Path(model) if args.glb else assets / model
        where = ', '.join(f'{stem} ({"/".join(sorted(names))})' for stem, names in sorted(maps.items()))
        if not path.exists():
            print(f'MISSING {model}: {where}')
            faults += 1
            continue
        worst = check_model(path, args.lods)
        bad = [w for w in worst if is_fault(w[2], w[3])]
        if bad:
            faults += 1
            level, view, covered, back, culprits = max(bad, key=lambda w: w[3] / w[2])
            materials = ', '.join(f'{k} {v}' for k, v in sorted(culprits.items(), key=lambda kv: -kv[1]))
            print(f'FAULT {model}: LOD{level} {view}: {back}/{covered} px ({100 * back / covered:.1f} %) '
                  f'back faces in view ({materials}); LODs {[w[0] for w in bad]}; placed by {where or "-"}')
        elif args.verbose:
            share = max((w[3] / w[2] for w in worst), default=0.0)
            print(f'ok    {model}: worst {100 * share:.2f} %; placed by {where or "-"}')
    print(f'{len(targets)} models checked, {faults} with open-interior faults')
    sys.exit(1 if faults else 0)


if __name__ == '__main__':
    main()
