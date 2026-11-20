#!/usr/bin/env python3
"""Fit the shared lance release onto a fixed floor pose beside the falling Kreegan.
Both modules rest on their common stock back. Dead uses the same world anchor. Other channels are unchanged.
Usage: death_carbine_floor.py <in.glb> <out.glb> <weapon.glb>; WEAPON/DEATH/DEAD name the rig channels.
"""
from pathlib import Path
import sys
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
import glb_pose  # noqa: E402
from floor_fix import channel, keys_covering  # noqa: E402

import os
RAMP_BEFORE, RAMP, CLEAR = 0.25, float(os.environ.get('RAMP', '0.5')), 0.002
UP = np.array([0.0, 1.0, 0.0])
src, out = Path(sys.argv[1]), Path(sys.argv[2])
rifle_glb = glb_pose.Glb(sys.argv[3] if len(sys.argv) > 3 else HERE / 'export' / 'hes_kreegan_carbine.glb')
RP = np.concatenate([rifle_glb.accessor(p['attributes']['POSITION']).astype(np.float64)
                     for p in rifle_glb.json['meshes'][0]['primitives']])
RPH = np.c_[RP, np.ones(len(RP))]
model = glb_pose.Model(glb_pose.Glb(src))
nodes = model.glb.json['nodes']
RIFLE = next(i for i, n in enumerate(nodes) if n.get('name') == os.environ.get('WEAPON', 'Rifle'))
PARENT = model.parent[RIFLE]
PELVIS = next(i for i, n in enumerate(nodes) if n.get('name') == 'B_Pelvis'); FALL = float(os.environ.get('FALL', '0.5'))


def rifle_low(world_matrix):
    return float((RPH @ world_matrix.T)[:, 1].min())


def laid(world_matrix):
    """Barrel level, stock back down; both modules have the same local Z support height."""
    R = world_matrix[:3, :3] / np.linalg.norm(world_matrix[:3, :3], axis=0)
    barrel = R[:, 1] - (R[:, 1] @ UP) * UP
    barrel = barrel / max(np.linalg.norm(barrel), 1e-9) if np.linalg.norm(barrel) > 1e-6 else np.array([1.0, 0, 0])
    # Both barrel modules share the raised rear stock: rest its back on the floor.
    side = np.cross(barrel, -UP)
    third = np.cross(side, barrel)                       # local Z = X x Y
    return np.stack([side, barrel, third], axis=1)


def smooth(x):
    x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)


def solve(clip, anchor=None):
    original = model.clip_times(clip)
    times = np.unique(np.r_[original, np.arange(original[0], original[-1], 1/120)].astype(np.float32)).tolist()
    worlds = [model.world(model.sample(clip, t)) for t in times]
    lows = np.array([rifle_low(w[RIFLE]) for w in worlds])
    if anchor is None:
        # hkr: the Kreegan carries the gun low (its muzzle ~25 cm up while standing), so the gun's own height says
        # nothing: the fist opens when the falling pelvis has dropped FALL of its total drop
        pel = np.array([w[PELVIS][1, 3] for w in worlds]); drop = pel[0] - pel.min()
        down = np.where(pel < pel[0] - FALL * drop)[0]
        start = times[int(down[0])] - RAMP_BEFORE if len(down) else times[-1]
        contact = np.where(lows < CLEAR)[0]
        if len(contact):
            start = min(start, times[int(contact[0])]-RAMP_BEFORE)
        start = max(times[0], start)
        release = worlds[int(np.searchsorted(times, start))][RIFLE]
        anchor = release.copy()
        anchor[:3, :3] = laid(release)*np.linalg.norm(release[:3,:3],axis=0)
        anchor[:3, 3] += np.array([-1.15, 0., .75])
        anchor[:3, 3] += (CLEAR-rifle_low(anchor))*UP
    else:
        start = 0.
    trans, rots = [], []
    for t, w in zip(times, worlds):
        held = release if clip == DEATH and t >= start else w[RIFLE]
        k = smooth((t - start) / RAMP) if clip == DEATH else 1.0
        qa = glb_pose.matrix_quaternion(held[:3, :3] / np.linalg.norm(held[:3, :3], axis=0))
        qb = glb_pose.matrix_quaternion(anchor[:3, :3]/np.linalg.norm(anchor[:3,:3],axis=0))
        q = glb_pose.slerp(qa, qb, k); q = q / np.linalg.norm(q)
        T = np.eye(4); T[:3, :3] = glb_pose.quaternion_matrix(q)[:3, :3] * np.linalg.norm(held[:3, :3], axis=0)
        T[:3, 3] = held[:3, 3]*(1-k)+anchor[:3, 3]*k
        low = rifle_low(T)
        # the fist lies ~30 cm up at the end: the guard lets go, and the rifle drops onto the floor with the lay-in
        T[:3, 3] += max(k * (CLEAR - low), CLEAR - low) * UP if low > CLEAR else (CLEAR - low) * UP
        local = np.linalg.inv(w[PARENT]) @ T
        S = np.linalg.norm(local[:3, :3], axis=0)
        trans.append(local[:3, 3]); rots.append(glb_pose.matrix_quaternion(local[:3, :3] / S))
    rots = np.array(rots)
    for i in range(1, len(rots)):                           # one hemisphere, so LINEAR keys slerp the short way
        if rots[i] @ rots[i - 1] < 0:
            rots[i] = -rots[i]
    for path, values in (('translation', np.array(trans)), ('rotation', rots)):
        sampler = channel(model, clip, RIFLE, path)
        keys_covering(model, sampler, times, path)        # inputs onto every clip key
        sampler['input'] = model.glb.append_accessor(np.array(times)[:, None], 'SCALAR')
        sampler['interpolation'] = 'LINEAR'
        sampler['output'] = model.glb.append_accessor(values, 'VEC3' if path == 'translation' else 'VEC4')
    new = [rifle_low(model.world(model.sample(clip, t))[RIFLE]) for t in times]
    body = [model.lowest(clip, t) for t in times]
    print(f'RIFLEFLOOR {clip}: lay-in from {start:.3f} s; held rifle lowest {lows.min():+.4f}, after {min(new):+.4f} '
          f'(last {new[-1]:+.4f}); body lowest last {body[-1]:+.4f}, min {min(body):+.4f}')
    return anchor


DEATH, DEAD = os.environ.get('DEATH', 'Carbine_Death'), os.environ.get('DEAD', 'Carbine_Dead')
anchor = solve(DEATH)
solve(DEAD, anchor)
model.glb.write(out)
