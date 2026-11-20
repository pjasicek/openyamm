#!/usr/bin/env python3
"""Legs through a long skirt, per clip (h04, for the skirted peasants). Posed LOD0 skin per sample; a skirt vertex
(dominated by a bone whose name starts with the prefix, default Skirt_) is pierced when its nearest leg vertex (thigh,
calf, foot or toe dominated) lies within 4 cm and the skirt vertex is behind that leg vertex's normal: the leg's
surface is outside the cloth there. Prints the share of samples with a pierced vertex, the deepest (mm) and the worst
sample's phase and leg bone. Compare a new clip with the model's accepted locomotion.

    skirt_probe.py <glb> <clip>[,<clip>...] [--prefix Skirt_] [--rate 60]
"""
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402
from contact_probe import vertex_normals  # noqa: E402

LEG = ('Thigh', 'Calf', 'Foot', 'Toe')


def main():
    args = sys.argv[1:]
    prefix = args[args.index('--prefix') + 1] if '--prefix' in args else 'Skirt_'
    rate = float(args[args.index('--rate') + 1]) if '--rate' in args else 60.0
    glb = glb_pose.Glb(args[0])
    model = glb_pose.Model(glb)
    names = [n.get('name', '') for n in glb.json['nodes']]
    prim = model.primitives[0]
    dom = [names[model.joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(axis=1)]]
    skirt = np.array([d.startswith(prefix) for d in dom])
    leg = np.array([d.startswith('B_') and any(t in d for t in LEG) for d in dom])
    si, li = np.where(skirt)[0], np.where(leg)[0]
    for clip in args[1].split(','):
        T = model.clip_times(clip)[-1]
        times = np.arange(0, T, 1.0 / rate)
        hits, worst = 0, (0.0, 0.0, '')
        for t in times:
            pts = model.skinned_positions(model.world(model.sample(clip, float(t))))[0][0]
            nrm = vertex_normals(pts, prim['triangles'])
            d, j = cKDTree(pts[li]).query(pts[si])
            depth = np.einsum('ij,ij->i', pts[si] - pts[li][j], nrm[li][j])
            inside = (d < 0.04) & (depth < -0.002)
            if inside.any():
                hits += 1
                k = int(np.argmin(np.where(inside, depth, 0)))
                if -depth[k] > worst[0]:
                    worst = (-depth[k], t / T, dom[li[j[k]]])
        print(f'{clip:10} skirt pierced: {100 * hits / len(times):.0f}% max {1000 * worst[0]:.0f} mm'
              + (f' at {worst[1]:.2f} by {worst[2]}' if hits else ''))


if __name__ == '__main__':
    main()
