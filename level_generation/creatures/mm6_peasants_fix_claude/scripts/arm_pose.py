#!/usr/bin/env python3
"""Set the hanging-arm angles of the listed clips of an actor GLB, keeping the clip's motion about them. Each segment
(upper arm, forearm, hand: shoulder -> elbow -> wrist -> middle knuckle) gets a mean angle out from vertical in the
front view (LAT, degrees away from the body) and the forearm and hand a mean forward bend relative to the segment above
(FLEX, degrees); the upper arm keeps its clip forward angle. Each frame's deviation from the clip mean is kept, so the
idle still breathes. Segments are swung by the smallest rotation onto their new direction, from the shoulder down;
fingers keep their local rotations. Only upper arm, forearm and hand rotation channels change.
History (female peasant, 2026-10-30): a whole-arm swing out left an A-pose with inward kinks at the elbow and wrist,
then per-segment offsets left the elbow in and the hand out; one straight line (equal LAT) clears the skirt at ~10 deg.
Usage: arm_pose.py in.glb out.glb --arms L/<upper>/<fore>/<hand>/<middle1> R/... --lat U F H --flex F H --clips ..."""
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gltf_rig import Glb, qmul, qinv, qrot

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('dst'); ap.add_argument('--arms', nargs=2, required=True)
ap.add_argument('--lat', nargs=3, type=float, required=True)
ap.add_argument('--flex', nargs=2, type=float, required=True)
ap.add_argument('--clips', nargs='+', required=True)
a = ap.parse_args()


def arc(u, v):
    """Smallest rotations taking unit vectors u onto v (frames, 3) as quaternions (x, y, z, w)."""
    c = np.cross(u, v); d = np.sum(u * v, -1, keepdims=True)
    q = np.concatenate([c, 1 + d], -1)
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


def angles(d, sign):
    """Front-view angle out from vertical and side-view forward angle (radians) of downward directions d."""
    return np.arctan2(sign * d[:, 0], -d[:, 1]), np.arctan2(d[:, 2], -d[:, 1])


def direction(lat, fwd, sign):
    v = np.stack([sign * np.tan(lat), -np.ones_like(lat), np.tan(fwd)], -1)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


g = Glb(a.src)
for clip in a.clips:
    t = g.clip_times(clip); T, R, S = g.sample(clip, t); WT, WR = g.fk(T, R); n = len(t)
    for spec in a.arms:
        side, *bones = spec.split('/'); ids = [g.node(b) for b in bones]
        sign = 1 if side == 'L' else -1                  # +X is the character's left
        seg = [WT[:, ids[k + 1]] - WT[:, ids[k]] for k in range(3)]
        seg = [s / np.linalg.norm(s, axis=-1, keepdims=True) for s in seg]
        lat0, fwd0 = zip(*[angles(s, sign) for s in seg])
        fwd_mean = [fwd0[0].mean()]
        for k in (1, 2):
            fwd_mean.append(fwd_mean[-1] + np.radians(a.flex[k - 1]))
        acc = np.tile([0, 0, 0, 1.0], (n, 1)); new_w = []
        for k in range(3):
            lat = np.radians(a.lat[k]) + lat0[k] - lat0[k].mean()
            fwd = fwd_mean[k] + fwd0[k] - fwd0[k].mean()
            cur = qrot(acc, seg[k])
            acc = qmul(arc(cur, direction(lat, fwd, sign)), acc)
            new_w.append(qmul(acc, WR[:, ids[k]]))
        parents = [WR[:, g.parent[ids[0]]]] + new_w[:-1]
        for i, w, pw in zip(ids[:3], new_w, parents):
            g.set_rotation_channel(clip, i, t, qmul(qinv(pw), w))
    print('ARMPOSE', clip, 'lat', a.lat, 'flex', a.flex)
g.save(a.dst)
