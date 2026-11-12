#!/usr/bin/env python3
"""Release / contact time of an attack clip from a socket or joint's forward travel (humanoid playbook: impact = when
the tip reaches 95 % of its forward travel). Forward = the body's facing at Standing (+Z for our B_* bodies); travel
measured from its rearmost point before the forward peak.

    release_time.py <glb> <clip> <node> [--frac 0.95]
"""
import argparse
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import donor_attack as da  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('glb')
    ap.add_argument('clip')
    ap.add_argument('node')
    ap.add_argument('--frac', type=float, default=0.95)
    a = ap.parse_args()
    T = da.Skeleton(a.glb)
    _, W0 = T.world('Standing', 0.0)
    fwd, _, _ = da.facing(T, W0, feet=[(f'B_{s}_Foot', f'B_{s}_Toe0') for s in 'LR']) if 'B_L_Thigh' in T.idx \
        else da.facing(T, W0, 'B_L_Clavicle', 'B_R_Clavicle')
    L = T.model.clip_times(a.clip)[-1]
    ts = np.arange(0, L + 1e-6, 1 / 60)
    P = np.array([T.world(a.clip, t)[1][T.idx[a.node], :3, 3] for t in ts])
    z = P @ fwd
    k = int(np.argmax(z))
    j = int(np.argmin(z[:k + 1]))
    thr = z[j] + a.frac * (z[k] - z[j])
    i = j + int(np.argmax(z[j:k + 1] >= thr))
    print(f'{a.node}: rearmost {z[j] - z[0]:+.3f} m at {ts[j]:.3f} s, forward peak {z[k] - z[0]:+.3f} m at {ts[k]:.3f} s,'
          f' {a.frac:.0%} at {ts[i]:.3f} s (height {P[i, 1]:.2f} m)')


if __name__ == '__main__':
    main()
