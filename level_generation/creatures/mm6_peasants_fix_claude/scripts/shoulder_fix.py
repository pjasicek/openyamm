#!/usr/bin/env python3
"""Hold the clavicles near their rest pose in an installed actor GLB (user review 2026-10-30 of the MM6 male peasant:
shoulders "dislocated", "slumped"). The library clips drop the clavicles 4-20 deg and roll them up to 35 deg forward,
lopsided between the sides. On every key of the listed clips each clavicle (head -> upper-arm head) is turned about its own head so the clip's
mean lies inside [rest - DROP, rest + RAISE] elevation and rest +- FWD forward angle (its own motion kept); the upper arm keeps its
world rotation, so the arm motion is unchanged. Only the clavicle and upper-arm rotation channels are rewritten;
mesh, skin, textures, LODs and the other clips stay byte-identical. glTF frame: +Y up, +Z forward, +X left.
Usage: shoulder_fix.py in.glb out.glb --bones L/B_L_Clavicle/B_L_UpperArm R/B_R_Clavicle/B_R_UpperArm
       [--clips Standing Walking Fidget] [--drop 3] [--raise 6] [--fwd 8]"""
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gltf_rig import Glb, qmul, qinv, qrot, qaxis

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('dst')
ap.add_argument('--bones', nargs='+', required=True)
ap.add_argument('--clips', nargs='+', default=['Standing', 'Walking', 'Fidget'])
ap.add_argument('--drop', type=float, default=3); ap.add_argument('--raise', dest='rise', type=float, default=6)
ap.add_argument('--fwd', type=float, default=8)
a = ap.parse_args()
g = Glb(a.src)
T0, R0, _ = g.rest(); WT0, WR0 = g.fk(T0[None], R0[None])
sides = [b.split('/') for b in a.bones]


def angles(v):
    return np.arctan2(v[..., 1], np.hypot(v[..., 0], v[..., 2])), np.arctan2(v[..., 2], np.abs(v[..., 0]))


def direction(elev, fwd, sign_x):
    c = np.cos(elev)
    return np.stack([sign_x * c * np.cos(fwd), np.sin(elev), c * np.sin(fwd)], -1)


def arc(u, v):                                        # shortest rotation taking unit u onto unit v
    ax = np.cross(u, v); s = np.linalg.norm(ax, axis=-1, keepdims=True); c = np.sum(u * v, -1, keepdims=True)
    q = np.concatenate([ax, 1 + c], -1)
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


rest = {}
for side, cl, ua in sides:
    v = WT0[0, g.node(ua)] - WT0[0, g.node(cl)]; rest[side] = angles(v)
for clip in a.clips:
    t = g.clip_times(clip); T, R, S = g.sample(clip, t); WT, WR = g.fk(T, R)
    report = []
    for side, cl, ua in sides:
        ic, iu = g.node(cl), g.node(ua); ip = g.parent[ic]
        v = WT[:, iu] - WT[:, ic]; L = np.linalg.norm(v, axis=-1, keepdims=True)
        e, f = angles(v); e0, f0 = rest[side]
        # the clip's mean pose is moved into the band and its own motion (breathing, walk sway) kept around it; the
        # extremes are then clamped 2 deg beyond the band
        elo, ehi = e0 - np.radians(a.drop), e0 + np.radians(a.rise)
        flo, fhi = f0 - np.radians(a.fwd), f0 + np.radians(a.fwd)
        e2 = np.clip(e - (e.mean() - np.clip(e.mean(), elo, ehi)), elo - np.radians(2), ehi + np.radians(2))
        f2 = np.clip(f - (f.mean() - np.clip(f.mean(), flo, fhi)), flo - np.radians(2), fhi + np.radians(2))
        sign_x = np.sign(v[:, 0])
        Q = arc(v / L, direction(e2, f2, sign_x))
        new_wr_cl = qmul(Q, WR[:, ic])
        local_cl = qmul(qinv(WR[:, ip]), new_wr_cl)
        local_ua = qmul(qinv(new_wr_cl), WR[:, iu])
        g.set_rotation_channel(clip, ic, t, local_cl)
        g.set_rotation_channel(clip, iu, t, local_ua)
        report.append('%s drop %.1f..%.1f deg fwd %.1f..%.1f -> held' % (side, np.degrees((e - e0).min()), np.degrees((e - e0).max()),
                                                                       np.degrees((f - f0).min()), np.degrees((f - f0).max())))
    print('SHOULDERS', clip, len(t), 'keys |', ' | '.join(report))
g.save(a.dst)
print('SAVED', a.dst)
