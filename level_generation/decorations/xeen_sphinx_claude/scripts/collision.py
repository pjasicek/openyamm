#!/usr/bin/env python3
"""The collision and placement contract for A5 (the decorations have no collision: radius 0).

Footprints are measured on the installed LOD0 mesh (the GLB in export/): its triangles are sliced into a 16-unit
occupancy raster per height band (a cell is solid when the mesh's cross-section at that height covers it, by an
even-odd crossing count per row), outlined row by row (the outer edges, and the inner edges where a row has two
spans: the gap between the paws), simplified (Douglas-Peucker, 20 units) and pushed out 8 units.
Rings: `body` (the whole footprint at 40 over the ground, the gap between the paws left open, closed across the
frame's front) and `head` (the nemes's footprint at its widest band); per region the top heights (mesh maxima).
Model-local units: x = the model's +X (glTF +X: the sphinx's own LEFT, a viewer's right when facing its face),
y = forward (toward the face; glTF +Z); origin = the middle of the door's threshold. World and X6 cell coordinates
are given for each placement (cells of 512, cell = 64 + world x / 512, cell y = 64 - world y / 512).
Writes integration/sphinx_collision.yml and review/collision_<id>.png. Usage: collision.py"""
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
CFG = json.loads((HERE / 'sphinx.json').read_text())
CELL = 16.0
PLACE = {
    'north': {'world': [9216, 10240, 1408], 'facing': 180,
              'note': 'XD-15 shell at (82, 39): the door threshold on the breast at cell (82, 44), ground 1,408 '
                      '(FORE_H); facing 180 looks south.'},
    'south': {'world': [-12544, -10240, 1536], 'facing': 270,
              'note': "FD-02 shell: the breast's east wall at cell (39.5, 84), the dune at 1,536 (SPHINX2_H); "
                      'facing 270 looks east.'},
}


TOPS = {   # regions of the mesh whose top heights A5 may want (walkable lids, barrier heights), model units
    'north': lambda x, y, z: {'forearm_paw_left': (x > 450) & (y > -500) & (z < 900),
                              'forearm_paw_right': (x < -450) & (y > -500) & (z < 900),
                              'breast_and_frame': (np.abs(x) <= 370) & (y > -1300) & (y < 80) & (z < 1400),
                              'shoulders': (y > -2900) & (y <= -1300) & (z < 1700),
                              'back': (y > -4500) & (y <= -2900), 'rump': y <= -4500,
                              'head_nemes': z >= 1400},
    'south': lambda x, y, z: {'breast_and_frame': (np.abs(x) <= 340) & (y > -520) & (z < 560),
                              'shoulders': (y > -1300) & (y <= -520) & (z < 560),
                              'back': (y > -1950) & (y <= -1300), 'haunch': y <= -1950,
                              'head_nemes': z >= 560},
}


def load_lod0(path):
    raw = path.read_bytes()
    jlen = struct.unpack_from('<I', raw, 12)[0]
    gj = json.loads(raw[20:20 + jlen])
    bin_off = 20 + jlen + 8
    mesh = next(m for m in gj['meshes'] if not m['name'].endswith(('_LOD1', '_LOD2', '_LOD3')))

    def acc(i):
        a = gj['accessors'][i]
        bv = gj['bufferViews'][a['bufferView']]
        comp = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a['componentType']]
        n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a['type']]
        off = bin_off + bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        return np.frombuffer(raw, comp, a['count'] * n, off).reshape(a['count'], n) if n > 1 else \
            np.frombuffer(raw, comp, a['count'], off)

    tris = []
    for p in mesh['primitives']:
        v = acc(p['attributes']['POSITION']).astype(np.float64)
        i = acc(p['indices']).astype(np.int64).reshape(-1, 3)
        tris.append(v[i])
    t = np.concatenate(tris) * 100.0          # metres -> units; glTF (x, y up, z forward)
    return np.stack([t[..., 0], t[..., 2], t[..., 1]], -1)   # model (x, y forward, z up)


def section(T, z, xs, ys):
    """Solid cells of the horizontal section at height z (even-odd along +x rays per row)."""
    # segment of each triangle crossing the plane
    d = T[..., 2] - z
    pts = []
    for (i, j) in ((0, 1), (1, 2), (2, 0)):
        m = (d[:, i] < 0) != (d[:, j] < 0)
        t = d[:, i] / np.where(m, d[:, i] - d[:, j], 1)
        pts.append(np.where(m[:, None], T[:, i, :2] + (T[:, j, :2] - T[:, i, :2]) * t[:, None], np.nan))
    pts = np.stack(pts, 1)                  # (M, 3 edges, 2)
    ok = (~np.isnan(pts[..., 0])).sum(1) == 2
    seg = np.array([p[~np.isnan(p[:, 0])] for p in pts[ok]])   # (K, 2 points, 2)
    solid = np.zeros((len(ys), len(xs)), bool)
    y0, y1 = seg[:, 0, 1], seg[:, 1, 1]
    for r, y in enumerate(ys):
        m = (y0 < y) != (y1 < y)
        if not m.any():
            continue
        s = seg[m]
        t = (y - s[:, 0, 1]) / (s[:, 1, 1] - s[:, 0, 1])
        xc = np.sort(s[:, 0, 0] + (s[:, 1, 0] - s[:, 0, 0]) * t)
        for k in range(0, len(xc) - 1, 2):
            solid[r, (xs >= xc[k]) & (xs <= xc[k + 1])] = True
    return solid


def spans(row, xs):
    out = []
    on = False
    for k, v in enumerate(row):
        if v and not on:
            start = xs[k]
            on = True
        if on and (not v or k == len(row) - 1):
            out.append([start, xs[k - 1] if not v else xs[k]])
            on = False
    return out


def dp(points, tol):
    pts = np.asarray(points, float)
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    ab = b - a
    n = np.linalg.norm(ab)
    if n < 1e-9:
        dist = np.linalg.norm(pts - a, axis=1)
    else:
        dist = np.abs(ab[0] * (pts - a)[:, 1] - ab[1] * (pts - a)[:, 0]) / n
    k = int(np.argmax(dist))
    if dist[k] > tol:
        return np.vstack([dp(pts[:k + 1], tol)[:-1], dp(pts[k:], tol)])
    return np.vstack([a, b])


def outline(solid, xs, ys):
    """The largest closed outline of the solid raster: cell-boundary edges with the solid on their left, chained into
    loops (at a diagonal saddle the turn keeps the solid cells apart), simplified (Douglas-Peucker, 20 units)."""
    S = np.pad(solid, 1)
    ny, nx = S.shape
    nxt = {}
    # corner (i, j) = grid corner between rows i-1/i and columns j-1/j of the padded raster
    for i in range(ny):
        for j in range(nx):
            if not S[i, j]:
                continue
            # cell (i, j) spans corners (i, j)-(i+1, j+1); walk counter-clockwise (solid on the left) in (col, row)
            if not S[i - 1, j] if i > 0 else True:
                nxt.setdefault((j + 1, i), []).append((j, i))          # top edge, right to left
            if not S[i + 1, j] if i + 1 < ny else True:
                nxt.setdefault((j, i + 1), []).append((j + 1, i + 1))  # bottom edge, left to right
            if not S[i, j - 1] if j > 0 else True:
                nxt.setdefault((j, i), []).append((j, i + 1))          # left edge, downward
            if not S[i, j + 1] if j + 1 < nx else True:
                nxt.setdefault((j + 1, i + 1), []).append((j + 1, i))  # right edge, upward
    loops = []
    while nxt:
        start = next(iter(nxt))
        loop = [start]
        cur = start
        prev_dir = None
        while True:
            outs = nxt[cur]
            if len(outs) > 1 and prev_dir is not None:
                # saddle: take the turn that keeps to the right of the incoming direction
                def turn(o):
                    d = (o[0] - cur[0], o[1] - cur[1])
                    return prev_dir[0] * d[1] - prev_dir[1] * d[0]
                outs.sort(key=turn)
            n = outs.pop(0)
            if not outs:
                del nxt[cur]
            prev_dir = (n[0] - cur[0], n[1] - cur[1])
            cur = n
            if cur == start:
                break
            loop.append(cur)
        loops.append(loop)
    best = None
    for loop in loops:
        p = np.array(loop, float)
        area = 0.5 * abs(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]))
        if best is None or area > best[0]:
            best = (area, p)
    p = best[1]
    # padded corner (col, row) -> model units: corner j sits half a cell before xs[j - 1]
    pts = np.stack([xs[0] + (p[:, 0] - 1.5) * CELL, ys[0] + (p[:, 1] - 1.5) * CELL], 1)
    # Douglas-Peucker on the closed loop: split at the two farthest-apart points
    k = int(np.argmax(np.linalg.norm(pts - pts[0], axis=1)))
    a = dp(np.vstack([pts[:k + 1]]), 20.0)
    b = dp(np.vstack([pts[k:], pts[:1]]), 20.0)
    return np.vstack([a[:-1], b[:-1]])


def offset(ring, d):
    # push each vertex outward along the average of its edge normals (ring counter-clockwise or clockwise)
    p = np.asarray(ring, float)
    area = 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
    out = []
    for k in range(len(p)):
        a, b, c = p[k - 1], p[k], p[(k + 1) % len(p)]
        n1 = np.array([(b - a)[1], -(b - a)[0]])
        n2 = np.array([(c - b)[1], -(c - b)[0]])
        n1 /= np.linalg.norm(n1) + 1e-9
        n2 /= np.linalg.norm(n2) + 1e-9
        n = n1 + n2
        n /= np.linalg.norm(n) + 1e-9
        out.append(b + n * d * (1 if area < 0 else -1))
    return np.array(out)


def point_in_ring(ring, pts):
    inside = np.zeros(len(pts), bool)
    n = len(ring)
    for k in range(n):
        (x1, y1), (x2, y2) = ring[k], ring[(k + 1) % n]
        m = (y1 > pts[:, 1]) != (y2 > pts[:, 1])
        xc = x1 + (pts[:, 1] - y1) * (x2 - x1) / np.where(y2 != y1, y2 - y1, 1e-9)
        inside ^= m & (pts[:, 0] < xc)
    return inside


def to_world(pts, place):
    wx, wy, _ = place['world']
    yaw = np.radians(place['facing'])
    # engine: glTF +X -> world -X and glTF +Z (forward) -> world +Y at facing 0, then rotated by facing (CCW)
    lx, ly = -pts[:, 0], pts[:, 1]
    c, s = np.cos(yaw), np.sin(yaw)
    return np.stack([wx + c * lx - s * ly, wy + s * lx + c * ly], 1)


def cells(w):
    return np.stack([64 + w[:, 0] / 512, 64 - w[:, 1] / 512], 1)


def r(v, n=0):
    return [round(float(a), n) if n else int(round(float(a))) for a in v]


doc = {'units': 'model-local units (1 model metre = 100 map units); x = glTF +X (the sphinx\'s own left), '
                 'y = forward (toward the face); origin = the middle of the door threshold on the breast at the ground',
       'engine_facing': 'facing 0 faces +Y (north), 90 west, 180 south, 270 east (game/maps/DecorationModelSet.cpp, '
                        'engine/models/ModelAsset.cpp gltfModelPlacement: glTF +X -> world -X at facing 0)'}
import sys
for sid in (sys.argv[1:] or ['north', 'south']):
    P = CFG[sid]
    T = load_lod0(PROJECT / 'export' / f"{P['name']}.glb")
    lo, hi = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
    xs = np.arange(lo[0] - CELL, hi[0] + CELL, CELL)
    ys = np.arange(lo[1] - CELL, hi[1] + CELL, CELL)
    ground = section(T, 40.0, xs, ys)
    D = P['door']
    body = offset(outline(ground, xs, ys), 8)
    hp = P['head']
    head_z = hp['z'] + 140 * hp['scale']
    head_sec = section(T, head_z, xs, ys)
    head = offset(outline(head_sec, xs, ys), 8)
    place = PLACE[sid]
    entry = {
        'decoration': f'xeen_sphinx_{sid}', 'row': 4010 if sid == 'north' else 4011,
        'decoration_list_id': 4009 if sid == 'north' else 4010,
        'origin_world': place['world'], 'origin_cells': r(cells(np.array([place['world'][:2]]))[0], 3),
        'facing': place['facing'], 'note': place['note'],
        'bounds_model': {'x': r([lo[0], hi[0]]), 'y': r([lo[1], hi[1]]), 'z': r([lo[2], hi[2]])},
        'door_opening_model': {'x': [-D['width'] / 2, D['width'] / 2], 'z': [0, D['height']], 'plane_y': 0,
                               'reveal_y': [D['back'], D['front']],
                               'frame_outer': {'x': [-(D['width'] / 2 + D['jamb']), D['width'] / 2 + D['jamb']],
                                               'z': [0, D['height'] + D['lintel']], 'front_y': D['front']}},
        'rings': {},
        'tops': {},
    }
    V = T.reshape(-1, 3)
    for name, sel in TOPS[sid](V[:, 0], V[:, 1], V[:, 2]).items():
        if sel.any():
            entry['tops'][name] = {'top_z': int(round(V[sel, 2].max())),
                                   'x': r([V[sel, 0].min(), V[sel, 0].max()]), 'y': r([V[sel, 1].min(), V[sel, 1].max()])}
    tops = {}
    for name, ring, bottom, top in (('body', body, 0, None), ('head', head, None, None)):
        cen = T.mean(1)
        inside = point_in_ring(ring, cen[:, :2])
        zt = float(T[inside][..., 2].max()) if inside.any() else 0.0
        w = to_world(ring, place)
        entry['rings'][name] = {
            'closed': True,
            'model': [r(p) for p in ring],
            'world': [r(p) for p in w],
            'cells': [r(p, 3) for p in cells(w)],
            'section_z': 40 if name == 'body' else round(head_z),
            'top_of_mesh_inside': round(zt),
        }
    doc[sid] = entry
    # picture
    sc = 0.08
    W = int((hi[0] - lo[0] + 400) * sc)
    H = int((hi[1] - lo[1] + 400) * sc)
    img = Image.new('RGB', (W, H), (30, 30, 30))
    dr = ImageDraw.Draw(img)
    def px(p):
        return ((p[0] - lo[0] + 200) * sc, H - (p[1] - lo[1] + 200) * sc)
    for rr, yv in zip(ground, ys):
        for k in np.nonzero(rr)[0]:
            dr.point(px((xs[k], yv)), fill=(150, 120, 80))
    for rr, yv in zip(head_sec, ys):
        for k in np.nonzero(rr)[0]:
            dr.point(px((xs[k], yv)), fill=(220, 180, 90))
    for ring, colr in ((body, (90, 200, 255)), (head, (255, 90, 90))):
        pts = [px(p) for p in ring]
        dr.line(pts + [pts[0]], fill=colr, width=2)
    dr.rectangle([px((-D['width'] / 2, 12)), px((D['width'] / 2, 0))], outline=(0, 255, 0))
    img.save(PROJECT / 'review' / f'collision_{sid}.png')
    print(sid, 'body ring', len(body), 'points; head ring', len(head), 'points; bounds', entry['bounds_model'])

out = PROJECT / 'integration' / 'sphinx_collision.yml'
lines = ['# The sphinxes\' placement and collision contract for A5 (lane S, xeen_sphinx_claude; written by '
         'scripts/collision.py from the installed LOD0 meshes).', '# README.md "Placement (for A5)" explains it.']


def emit(o, ind=0):
    pre = '  ' * ind
    for k, v in o.items():
        if isinstance(v, dict):
            lines.append(f'{pre}{k}:')
            emit(v, ind + 1)
        elif isinstance(v, list) and v and isinstance(v[0], list):
            lines.append(f'{pre}{k}:')
            for p in v:
                lines.append(f'{pre}  - [{", ".join(str(a) for a in p)}]')
        elif isinstance(v, list):
            lines.append(f'{pre}{k}: [{", ".join(str(a) for a in v)}]')
        elif isinstance(v, str):
            lines.append(f'{pre}{k}: {json.dumps(v)}')
        else:
            lines.append(f'{pre}{k}: {str(v).lower() if isinstance(v, bool) else v}')


emit(doc)
out.write_text('\n'.join(lines) + '\n')
print('WROTE', out)
