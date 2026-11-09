"""Skirt gates for the dress fix, every key of every clip, LOD0 posed with glb_pose (no Blender):
- robe_p99 / robe_max: edge stretch (posed / rest length) of edges between robe-weighted vertices (weight on Robe_*
  bones over 0.3), the production gate (mm7_m342_claude/scripts/gates.py: p99 <= 1.53, Death 1.70);
- hand_in_skirt: deepest hand vertex (hand shells, dominant joint a hand or finger bone) inside the skirt and
  petticoat surface (below the belt, 1.02 m rest height), metres; nearest-triangle signed distance, within 10 cm;
- leg_out: furthest leg vertex (legs piece, rest height 0.25-0.95 m: above the shoes) outside the skirt and
  petticoat surface and above the local hem (2 cm over the lowest cloth point within 8 cm horizontally), metres, and
  the share of such vertices more than 5 mm out.
Robe edges are welded by rest position, so UV splits do not change the stretch figures.
Usage: skirt_gates.py <glb> [...] (prints one row per clip and GLB; writes <glb>.gates.json)"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
import glb_pose as G  # noqa: E402

before = np.load(HERE / 'work' / 'lod0_before.npz')
PIECE = before['piece']


def signed(points, P, tris, tree, k=12):
    """Signed distance of points to the triangle set (positive outside along the face normal) and the distance."""
    _, cand = tree.query(points, k=k)
    a, b, c = P[tris[cand, 0]], P[tris[cand, 1]], P[tris[cand, 2]]
    best_d = np.full(len(points), np.inf)
    best_s = np.zeros(len(points))
    for j in range(cand.shape[1]):
        q = closest(points, a[:, j], b[:, j], c[:, j])
        d = np.linalg.norm(points - q, axis=1)
        n = np.cross(b[:, j] - a[:, j], c[:, j] - a[:, j])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        s = np.sign(((points - q) * n).sum(1)) * d
        better = d < best_d
        best_d[better], best_s[better] = d[better], s[better]
    return best_s, best_d


def closest(p, a, b, c):
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp, cp = p - b, p - c
    d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    denom = np.maximum(va + vb + vc, 1e-18)
    v, w = vb / denom, vc / denom
    q = a + ab * v[:, None] + ac * w[:, None]
    for cond, val in (((d1 <= 0) & (d2 <= 0), a), ((d3 >= 0) & (d4 <= d3), b), ((d6 >= 0) & (d5 <= d6), c)):
        q[cond] = val[cond]
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
    t = d1 / np.maximum(d1 - d3, 1e-18)
    q[m] = (a + ab * t[:, None])[m]
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
    t = d2 / np.maximum(d2 - d6, 1e-18)
    q[m] = (a + ac * t[:, None])[m]
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    t = (d4 - d3) / np.maximum((d4 - d3) + (d5 - d6), 1e-18)
    q[m] = (b + (c - b) * t[:, None])[m]
    return q


def gates(path):
    g = G.Glb(path)
    m = G.Model(g)
    prim = m.primitives[0]
    tri, rest = prim['triangles'], prim['positions']
    names = [g.json['nodes'][j]['name'] for j in m.joints]
    robe_j = np.array([n.startswith('Robe_') for n in names])
    hand_j = np.array(['Hand' in n or 'Finger' in n for n in names])
    J, Wt = prim['joints'], prim['weights']
    robe_v = (Wt * robe_j[J]).sum(1) > 0.3
    dom = J[np.arange(len(J)), Wt.argmax(1)]
    hand_v = np.unique(tri[np.isin(PIECE, [0, 41])])
    hand_v = hand_v[hand_j[dom[hand_v]]]
    leg_v = np.unique(tri[PIECE == 4])
    leg_v = leg_v[(rest[leg_v, 1] > 0.25) & (rest[leg_v, 1] < 0.95)]
    cloth_t = tri[np.isin(PIECE, [2, 3]) & (rest[tri].mean(1)[:, 1] < 1.02)]
    # orient the cloth's normals outward at rest (any face whose normal points at the body axis is flipped)
    c = rest[cloth_t].mean(1)
    n = np.cross(rest[cloth_t[:, 1]] - rest[cloth_t[:, 0]], rest[cloth_t[:, 2]] - rest[cloth_t[:, 0]])
    radial = c - np.array([0.0, 0.0, 0.03])
    radial[:, 1] = 0
    flip = (n * radial).sum(1) < 0
    cloth_t[flip] = cloth_t[flip][:, [0, 2, 1]]
    _, weld = np.unique(rest.round(6), axis=0, return_index=True, return_inverse=True)[1:]
    weld = weld.ravel()
    first = np.full(weld.max() + 1, -1)
    first[weld[::-1]] = np.arange(len(weld))[::-1]             # one vertex per rest position (UV splits welded)
    wt = first[weld[tri]]
    e = np.concatenate([wt[:, [0, 1]], wt[:, [1, 2]], wt[:, [2, 0]]])
    e = np.unique(np.sort(e, 1), axis=0)
    e = e[robe_v[e[:, 0]] & robe_v[e[:, 1]]]
    rest_len = np.linalg.norm(rest[e[:, 0]] - rest[e[:, 1]], axis=1)
    ok = rest_len > 1e-5
    out = {}
    for clip in m.clips:
        times = m.clip_times(clip)
        rec = {'robe_p99': 0.0, 'robe_max': 0.0, 'hand_in_skirt': 0.0, 'leg_out': 0.0, 'leg_out_share': 0.0}
        for t in times[::2] + [times[-1]]:
            P = m.skinned_positions(m.world(m.sample(clip, t)))[0][0]
            st = np.linalg.norm(P[e[ok, 0]] - P[e[ok, 1]], axis=1) / rest_len[ok]
            rec['robe_p99'] = max(rec['robe_p99'], float(np.percentile(st, 99)))
            rec['robe_max'] = max(rec['robe_max'], float(st.max()))
            if clip in ('Death', 'Dead'):
                continue
            tree = cKDTree(P[cloth_t].mean(1))
            s, d = signed(P[hand_v], P, cloth_t, tree)
            inside = (s < 0) & (d < 0.10)
            if inside.any():
                rec['hand_in_skirt'] = max(rec['hand_in_skirt'], float(d[inside].max()))
            s, d = signed(P[leg_v], P, cloth_t, tree)
            # a leg point below the hem (the walk and jog kick the front hem up) is not through the cloth
            cloth_v = P[np.unique(cloth_t)]
            hem = np.array([cloth_v[np.linalg.norm((cloth_v - q)[:, [0, 2]], axis=1) < 0.08][:, 1].min()
                            if (np.linalg.norm((cloth_v - q)[:, [0, 2]], axis=1) < 0.08).any() else -1.0
                            for q in P[leg_v]])
            s = np.where(P[leg_v, 1] > hem + 0.02, s, -1.0)
            outside = s > 0
            if outside.any():
                rec['leg_out'] = max(rec['leg_out'], float(s[outside].max()))
            rec['leg_out_share'] = max(rec['leg_out_share'], float((s > 0.005).mean()))
        out[clip] = {k: round(v, 4) for k, v in rec.items()}
    return out


for path in sys.argv[1:]:
    res = gates(path)
    json.dump(res, open(path + '.gates.json', 'w'), indent=1)
    for clip, r in res.items():
        print(f'{Path(path).name:22s} {clip:9s} robe p99 {r["robe_p99"]:.2f} max {r["robe_max"]:.2f} | hand in skirt '
              f'{100 * r["hand_in_skirt"]:.1f} cm | leg out {100 * r["leg_out"]:.1f} cm (share >5 mm {100 * r["leg_out_share"]:.1f} %)')
