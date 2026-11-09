#!/usr/bin/env python3
"""Legs through a robe or coat skirt (G6 skirt poke, approximate), per clip.

    skirt_poke_probe.py <glb> <clip>[,<clip>...]

Skirt: LOD0 triangles whose vertices are all dominated by the robe chain bones (Robe_*). Leg points: every third
vertex dominated by a thigh or calf bone. Per leg point a horizontal ray from the pelvis's vertical axis (at the
point's height) through the point: the point is covered when a skirt triangle crosses the ray beyond it, and pokes
through when skirt triangles cross the ray only before it (between the axis and the point). A point with no skirt on
its ray (below the hem, or a slit) is not counted. Prints the share of samples (30 Hz) with a poke, the most poking
points at one sample and the farthest poke beyond the skirt (mm). Compare with the model's accepted Walking.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402


def ray_hits(o, d, tri):
    """Distances along rays (o + s d, per row) of their crossings with triangles tri (T, 3, 3): (rays, T), nan if none."""
    e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    p = np.cross(d[:, None, :], e2[None])
    det = np.einsum('rtk,tk->rt', p, e1)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    s = o[:, None, :] - tri[None, :, 0]
    u = np.einsum('rtk,rtk->rt', s, p) * inv
    q = np.cross(s, e1[None])
    v = np.einsum('rk,rtk->rt', d, q) * inv
    t = np.einsum('rtk,tk->rt', q, e2) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
    return np.where(hit, t, np.nan)


def main():
    glb = glb_pose.Glb(sys.argv[1])
    model = glb_pose.Model(glb)
    names = [n['name'] for n in glb.json['nodes']]
    pelvis = names.index('B_Pelvis')
    prim = model.primitives[0]
    dom = [names[model.joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(axis=1)]]
    skirt_v = np.array([d.startswith('Robe_') for d in dom])
    tris = prim['triangles']
    skirt_t = tris[skirt_v[tris].all(axis=1)]
    leg = np.where([('Thigh' in d or 'Calf' in d) for d in dom])[0][::3]
    for clip in sys.argv[2].split(','):
        T = model.clip_times(clip)[-1]
        hits, worst_n, worst_d, n = 0, 0, 0.0, 0
        side = {'front': [0, 0.0], 'back': [0, 0.0]}
        for t in np.arange(0, T, 1.0 / 30):
            W = model.world(model.sample(clip, float(t)))
            pts = model.skinned_positions(W)[0][0]
            c = W[pelvis, :3, 3]
            lp = pts[leg]
            o = np.stack([np.full(len(lp), c[0]), lp[:, 1], np.full(len(lp), c[2])], axis=1)
            d = lp - o
            r = np.linalg.norm(d, axis=1)
            keep = r > 0.02
            o, d, r, lp = o[keep], d[keep] / r[keep, None], r[keep], lp[keep]
            out = np.zeros(len(lp))
            poke = np.zeros(len(lp), dtype=bool)
            for a in range(0, len(lp), 200):
                s = ray_hits(o[a:a + 200], d[a:a + 200], pts[skirt_t])
                beyond = np.nanmax(np.where(s > r[a:a + 200, None], s, np.nan), axis=1, initial=-1.0)
                before = np.nanmax(np.where(s <= r[a:a + 200, None], s, np.nan), axis=1, initial=-1.0)
                pk = (beyond < 0) & (before > 0)
                poke[a:a + 200] = pk
                out[a:a + 200] = np.where(pk, r[a:a + 200] - before, 0.0)
            poke &= out > 0.005
            for name, m in (('front', (lp[:, 2] - c[2]) > 0), ('back', (lp[:, 2] - c[2]) <= 0)):
                if (poke & m).any():
                    side[name][0] += 1
                    side[name][1] = max(side[name][1], float(out[poke & m].max()))
            n += 1
            if poke.any():
                hits += 1
                worst_n = max(worst_n, int(poke.sum()))
                worst_d = max(worst_d, float(out[poke].max()))
        cells = '  '.join(f'{k} {100 * v[0] / n:.0f}% {1000 * v[1]:.0f} mm' for k, v in side.items())
        print(f'{clip:9} skirt poke: {100 * hits / n:.0f}% of samples, worst {worst_n} points, farthest {1000 * worst_d:.0f} mm'
              f'  ({cells})')


if __name__ == '__main__':
    main()
