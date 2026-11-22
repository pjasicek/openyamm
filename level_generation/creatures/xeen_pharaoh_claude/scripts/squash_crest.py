#!/usr/bin/env python3
"""Fold the Lizardman Warrior's head crest under the nemes: every vertex of every mesh (colour and shadow LODs) whose
dominant joint is B_Head or B_Neck and which lies outside the nemes hood, seen from the head centre, moves along that
ray to just inside the hood. Bind-space positions are edited in place; nothing else in the GLB changes.

    squash_crest.py <in.glb> <nemes_model.glb> <out.glb> [--margin 0.008]"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pglb import Glb  # noqa: E402

CENTRE = np.array([-0.009, 1.705, -0.07])


def tris_of(glb):
    j = glb.json
    prim = j['meshes'][0]['primitives'][0]
    v = glb.accessor(prim['attributes']['POSITION']).astype(np.float64)
    f = glb.accessor(prim['indices']).astype(np.int64).reshape(-1, 3)
    return v[f]


def ray_hits(origins_dirs, tri):
    """Distance along each unit dir from CENTRE to the farthest hood triangle hit (inf when none)."""
    d = origins_dirs
    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    e1, e2 = b - a, c - a
    out = np.full(len(d), np.inf)
    for s in range(0, len(d), 256):
        D = d[s:s + 256][:, None, :]
        pvec = np.cross(D, e2[None])
        det = (e1[None] * pvec).sum(-1)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        tvec = CENTRE[None, None] - a[None]
        u = (tvec * pvec).sum(-1) * inv
        qvec = np.cross(tvec, e1[None])
        v = (D * qvec).sum(-1) * inv
        t = (e2[None] * qvec).sum(-1) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
        tt = np.where(hit, t, np.inf)
        out[s:s + 256] = tt.min(1)
    return out


def main():
    src, nemes, dst = sys.argv[1:4]
    margin = float(sys.argv[sys.argv.index('--margin') + 1]) if '--margin' in sys.argv else 0.008
    g = Glb(src)
    tri = tris_of(Glb(nemes))
    j = g.json
    names = {n.get('name'): i for i, n in enumerate(j['nodes'])}
    joints = j['skins'][0]['joints']
    want = {joints.index(names['B_Head']), joints.index(names['B_Neck'])}
    done = set()
    report = []
    for mesh in j['meshes']:
        for prim in mesh['primitives']:
            att = prim['attributes']
            pa = att['POSITION']
            if pa in done or 'JOINTS_0' not in att:
                continue
            done.add(pa)
            pos = g.accessor(pa).astype(np.float64)
            jo = g.accessor(att['JOINTS_0']).astype(np.int64)
            we = g.accessor(att['WEIGHTS_0']).astype(np.float64)
            dom = jo[np.arange(len(jo)), we.argmax(1)]
            sel = np.isin(dom, list(want)) & (pos[:, 1] > 1.50)
            idx = np.nonzero(sel)[0]
            rel = pos[idx] - CENTRE
            dist = np.linalg.norm(rel, axis=1)
            dirs = rel / dist[:, None]
            hit = ray_hits(dirs, tri)
            move = np.isfinite(hit) & (dist > hit - margin)
            new = CENTRE + dirs[move] * (hit[move] - margin)[:, None]
            pos[idx[move]] = new
            acc = j['accessors'][pa]
            view = j['bufferViews'][acc['bufferView']]
            start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
            stride = view.get('byteStride', 0) or 12
            raw = np.ndarray((acc['count'], 3), dtype=np.float32, buffer=g.bin, offset=start, strides=(stride, 4))
            raw[...] = pos.astype(np.float32)
            acc['min'] = pos.min(0).tolist(); acc['max'] = pos.max(0).tolist()
            report.append((mesh.get('name'), int(move.sum()), float((dist[move] - hit[move] + margin).max()) if move.any() else 0.0))
    for r in report:
        print('mesh %-24s moved %4d vertices, deepest %.3f m' % r)
    g.write(dst)
    print('WROTE', dst)


if __name__ == '__main__':
    main()
