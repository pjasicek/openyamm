#!/usr/bin/env python3
"""Clearance gate of the dual clips: per clip the closest approach between the two blades (hilt to tip segments, a
longsword's length along the Weapon / OffHandWeapon node's +Y) and between each blade and the other forearm, in the
arms' units (about 1.43 cm); and where each wrist goes on screen (normalised device coordinates of the engine's view:
the eye at Camera01 looking along glTF -Z, 60 degree vertical field, 16:9), worst |x| and lowest y over the clip: a
wrist beyond about x 1.1 or below y -1.7 takes its whole hand out of view.

    clearance.py <arms.glb> [blade length, default 75]
"""
import sys

import numpy as np

from bake_dual_clips import Arms, load_glb


def segment_distance(p1, q1, p2, q2):
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    c, b = d1 @ r, d1 @ d2
    denom = a * e - b * b
    s = np.clip((b * f - c * e) / denom, 0, 1) if denom > 1e-9 else 0.0
    t = np.clip((b * s + f) / e, 0, 1)
    s = np.clip((b * t - c) / a, 0, 1)
    return np.linalg.norm((p1 + d1 * s) - (p2 + d2 * t))


def main():
    arms = Arms(*load_glb(sys.argv[1]))
    length = float(sys.argv[2]) if len(sys.argv) > 2 else 75.0
    idx = arms.index
    worst = {}
    tan = np.tan(np.radians(30.0))
    for name in sorted(n for n in arms.clips if n.startswith('dual')):
        best = (1e9, 0, '')
        screen = {'R': [0.0, 9.0], 'L': [0.0, 9.0]}
        for t in np.linspace(0, arms.duration(name), 40):
            w = arms.world(arms.local(name, t))
            eye = w[idx['Camera01']][:3, 3]
            for side in 'RL':
                x, y, z = w[idx[f'Bip01 {side} Hand']][:3, 3] - eye
                depth = max(-z, 1.0)
                screen[side][0] = max(screen[side][0], abs(x / depth / (tan * 16.0 / 9.0)))
                screen[side][1] = min(screen[side][1], y / depth / tan)
            blade = {}
            for side, node in (('R', 'Weapon'), ('L', 'OffHandWeapon')):
                m = w[idx[node]]
                blade[side] = (m[:3, 3], (m @ np.array([0, length, 0, 1]))[:3])
            fore = {s: (w[idx[f'Bip01 {s} Forearm']][:3, 3], w[idx[f'Bip01 {s} Hand']][:3, 3]) for s in 'RL'}
            pairs = {'blades': segment_distance(*blade['R'], *blade['L']),
                     'R blade/L arm': segment_distance(*blade['R'], *fore['L']),
                     'L blade/R arm': segment_distance(*blade['L'], *fore['R']),
                     'arms': segment_distance(*fore['R'], *fore['L'])}
            for what, d in pairs.items():
                if d < best[0]:
                    best = (d, t, what)
        worst[name] = best
        print(f'{name:28s} closest {best[0]:6.1f} at {best[1]:.2f} s ({best[2]:13s})  wrist R |x|<={screen["R"][0]:.2f} '
              f'y>={screen["R"][1]:.2f}  L |x|<={screen["L"][0]:.2f} y>={screen["L"][1]:.2f}')


if __name__ == '__main__':
    main()
