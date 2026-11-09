#!/usr/bin/env python3
"""Retime the Smuggler (human form) Cast clip inside its length (2.0 s) and release (impact 1.1167 s, actors.yml
events), user review 2026-10-19: "cast - first 45 frames do nothing ... blended the sequence and not have dead spots".
The source stands still for 0.93 s, gathers in 0.17 s, thrusts the left palm through the release, holds with a slow
drift (1.2-1.7 s), snaps back to guard in 0.23 s and stands still again from 1.93 s. A monotone time warp (new time ->
source time, PCHIP through the knots below) spreads the gather over the dead start, keeps the release and the thrust
at source speed, shortens the hold drift and slows the return:
  0.00-0.10 s    source 0.00-0.93: the near-still start (it drifts up to 5 deg), so the first pose is kept
  0.10-1.1167 s  source 0.93-1.1167: the gather at about 1/6 speed, so the arm starts moving by frame 10
  1.1167-1.20 s  identity (the thrust through the release)
  1.20-1.45 s    source 1.20-1.68 (hold drift)
  1.45-2.00 s    source 1.68-2.00 (return to guard, about half speed)
Slowed down, the 30 Hz source keys show as speed jolts, so linear channels are sampled through a velocity-continuous
spline (modified Akima) over the source's own keys (mm8_m604_reduce_claude/scripts/retime_attack.py, review 3).
Every channel keeps its key times and interpolation; only output values change, in place. The legs are not animated
in this clip. Usage: retime_cast.py <in.glb> <out.glb>"""
import sys
from pathlib import Path

import numpy as np
from scipy.interpolate import Akima1DInterpolator, PchipInterpolator

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import append_accessor, read_glb, write_glb  # noqa: E402

CLIP, END = 'Cast', 2.0
KNOTS = [(0.0, 0.0), (0.1, 0.93), (0.35, 0.975), (0.75, 1.04), (1.1167, 1.1167), (1.20, 1.20), (1.45, 1.68), (1.95, 1.93),
         (2.0, 2.0)]


def view(doc, binary, index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    comp = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a['type']]
    assert a['componentType'] == 5126 and v.get('byteStride', comp * 4) == comp * 4
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return off, np.frombuffer(binary, np.float32, a['count'] * comp, off).reshape(a['count'], comp).copy()


def slerp(q0, q1, f):
    d = (q0 * q1).sum(-1, keepdims=True); q1 = np.where(d < 0, -q1, q1); d = np.abs(d)
    th = np.arccos(np.clip(d, -1, 1)); s = np.sin(th); small = s < 1e-6
    a = np.where(small, 1 - f, np.sin((1 - f) * th) / np.where(small, 1, s))
    b = np.where(small, f, np.sin(f * th) / np.where(small, 1, s))
    q = a * q0 + b * q1
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


def sample_linear(times, values, path, t):
    i = np.clip(np.searchsorted(times, t, side='right') - 1, 0, len(times) - 2)
    f = np.clip((t - times[i]) / np.maximum(times[i + 1] - times[i], 1e-9), 0, 1)[:, None]
    return slerp(values[i], values[i + 1], f) if path == 'rotation' else values[i] * (1 - f) + values[i + 1] * f


def knots(times, values, path):
    """every 4th key when the 120 Hz keys are a linear resampling of 30 Hz keys (checked), else every key"""
    idx = np.r_[np.arange(0, len(times) - 1, 4), len(times) - 1]
    if len(times) < 9 or abs(np.median(np.diff(times)) - 1 / 120) > 1e-4:
        return np.arange(len(times))
    lin = sample_linear(times[idx], values[idx], path, times)
    err = np.abs(np.abs((lin * values).sum(1)) - 1).max() if path == 'rotation' else np.abs(lin - values).max()
    return idx if err < 1e-5 else np.arange(len(times))


def sample(times, values, interp, path, t):
    t = np.clip(t, times[0], times[-1])
    if interp == 'STEP':
        i = np.clip(np.searchsorted(times, t, side='right') - 1, 0, len(times) - 1)
        return values[i]
    idx = knots(times, values, path)
    if len(idx) < 3:
        return sample_linear(times, values, path, t)
    v = values[idx].astype(np.float64).copy()
    if path == 'rotation':
        for j in range(1, len(v)):
            if (v[j] * v[j - 1]).sum() < 0:
                v[j] = -v[j]
    out = Akima1DInterpolator(times[idx], v, axis=0, method='makima')(t)
    if path == 'rotation':
        out /= np.linalg.norm(out, axis=1, keepdims=True)
    return out.astype(values.dtype)


def retime(doc, binary):
    anim = next(a for a in doc['animations'] if a['name'] == CLIP)
    warp = PchipInterpolator(*zip(*KNOTS))
    shared = {s['output'] for a in doc['animations'] if a is not anim for s in a['samplers']}
    done = set()
    for ch in anim['channels']:
        s = anim['samplers'][ch['sampler']]
        if s['output'] in done or ch['target']['path'] == 'scale':
            continue
        done.add(s['output'])
        _, times = view(doc, binary, s['input']); times = times[:, 0]
        off, vals = view(doc, binary, s['output'])
        if np.allclose(vals, vals[0], atol=1e-7):
            continue
        assert abs(times[-1] - END) < 1e-3, times[-1]
        if s['output'] in shared:
            s['output'] = append_accessor(doc, binary, doc['accessors'][s['output']], vals.tobytes())
            done.add(s['output']); off, vals = view(doc, binary, s['output'])
        out = sample(times, vals, s.get('interpolation', 'LINEAR'), ch['target']['path'], warp(times))
        binary[off:off + out.nbytes] = out.astype(np.float32).tobytes()
    return anim


if __name__ == '__main__':
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    doc, binary = read_glb(src); binary = bytearray(binary)
    anim = retime(doc, binary)
    write_glb(dst, doc, bytes(binary))
    print('RETIMED', CLIP, src.name, '->', dst.name, len(anim['channels']), 'channels')
