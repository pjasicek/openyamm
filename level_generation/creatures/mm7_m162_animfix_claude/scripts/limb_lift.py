#!/usr/bin/env python3
"""Lift a striking limb out of the floor in one clip (anim fix, 2026-11-11: the MM7 Behemoth's Attack, whose left
claw struck 10-14 cm into the ground at the blow).

    limb_lift.py <in.glb> <out.glb> --clip Attack --joint B_L_UpperArm --part 'B_L_*' [--margin 0.005] [--sigma 1.5]

Per key: the limb's vertices (dominated by joints matching --part that are descendants of --joint) are posed; when the
lowest is under the floor, the joint turns about the horizontal axis across its own swing plane (perpendicular to the
joint-to-lowest-point direction and to the vertical) by the smallest angle that lifts that point to --margin (bisection,
at most 30 degrees). The angles are taken as a running maximum of +/-1 key, Gaussian-smoothed (--sigma keys) so the
lift eases in and out, and applied as a world-space pre-rotation of the joint (written back as its local rotation).
Only that joint's rotation sampler of the clip changes.
"""
import argparse
import fnmatch
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose  # noqa: E402


def axis_angle(axis, angle):
    axis = axis / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * K @ K


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('input')
    p.add_argument('output')
    p.add_argument('--clip', required=True)
    p.add_argument('--joint', required=True)
    p.add_argument('--part', required=True)
    p.add_argument('--margin', type=float, default=0.005)
    p.add_argument('--sigma', type=float, default=1.5)
    args = p.parse_args()
    g = glb_pose.Glb(args.input)
    m = glb_pose.Model(g)
    names = [x.get('name', '') for x in g.json['nodes']]
    J = names.index(args.joint)

    def descends(i):
        while i >= 0:
            if i == J:
                return True
            i = m.parent[i]
        return False

    prim = m.primitives[0]
    dom = np.array(m.joints)[prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(axis=1)]]
    sel = np.array([descends(int(d)) and fnmatch.fnmatch(names[int(d)], args.part) for d in dom])
    pal_nodes = m.joints

    def limb_points(local):
        W = m.world(local)
        pal = W[pal_nodes] @ m.inverse_binds
        pos = prim['positions'][sel]
        Mv = np.einsum('vk,vkij->vij', prim['weights'][sel], pal[prim['joints'][sel]])
        return np.einsum('vij,vj->vi', Mv, np.c_[pos, np.ones(len(pos))])[:, :3], W

    anim = g.json['animations'][m.clips[args.clip]]
    ch = next(c for c in anim['channels'] if c['target']['node'] == J and c['target']['path'] == 'rotation')
    sampler = anim['samplers'][ch['sampler']]
    keys = g.accessor(sampler['input'])[:, 0].astype(float)
    angles, axes = np.zeros(len(keys)), np.zeros((len(keys), 3))
    for k, t in enumerate(keys):
        local = m.sample(args.clip, float(t))
        pts, W = limb_points(local)
        low = pts[np.argmin(pts[:, 1])]
        s = W[J][:3, 3]
        d = low - s
        ax = np.cross(d, [0.0, 1.0, 0.0])
        if np.linalg.norm(ax) < 1e-9:
            ax = np.array([1.0, 0.0, 0.0])
        # turning about ax by +angle lifts a point below the joint toward it: pick the sign that raises the point
        if (axis_angle(ax, 0.01) @ d)[1] < d[1]:
            ax = -ax
        axes[k] = ax / np.linalg.norm(ax)
        if pts[:, 1].min() >= args.margin:
            continue
        lo, hi = 0.0, np.radians(30)
        for _ in range(30):
            mid = (lo + hi) / 2
            R = axis_angle(axes[k], mid)
            lifted = (pts - s) @ R.T + s
            lo, hi = (mid, hi) if lifted[:, 1].min() < args.margin else (lo, mid)
        angles[k] = hi
    need = angles.copy()
    angles = gaussian_filter1d(maximum_filter1d(angles, 3), args.sigma, mode='nearest')
    angles = np.maximum(angles, need)
    for k in range(len(keys)):
        if angles[k] <= 0 or np.linalg.norm(axes[k]) == 0:
            continue
    # smooth the axes where they matter, then write the joint's local rotation
    out = g.accessor(sampler['output']).astype(float).copy()
    ref_axis = axes[np.argmax(angles)] if angles.max() > 0 else np.array([1.0, 0, 0])
    for k, t in enumerate(keys):
        if angles[k] <= 1e-6:
            continue
        local = m.sample(args.clip, float(t))
        W = m.world(local)
        R = axis_angle(ref_axis, angles[k])
        Wj = W[J][:3, :3] / np.linalg.norm(W[J][:3, :3], axis=0)
        Wp = W[m.parent[J]][:3, :3] / np.linalg.norm(W[m.parent[J]][:3, :3], axis=0)
        q = glb_pose.matrix_quaternion(Wp.T @ R @ Wj)
        out[k] = q / np.linalg.norm(q)
    for i in range(1, len(out)):
        if np.dot(out[i], out[i - 1]) < 0:
            out[i] = -out[i]
    sampler['output'] = g.append_accessor(out, 'VEC4')
    g.write(args.output)
    print(f'LIMBLIFT {args.clip} {args.joint}: max {np.degrees(angles.max()):.1f} deg over {int((angles > 1e-4).sum())} keys,'
          f' axis {np.round(ref_axis, 3)}')


if __name__ == '__main__':
    main()
