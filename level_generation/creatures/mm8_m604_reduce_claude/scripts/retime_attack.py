#!/usr/bin/env python3
"""Retime the Ether Knight Attack clip inside its length (1.7333 s) and impact (0.9833 s, actors.yml events), user
review 2026-10-18: "0-39 is a wind-up ... quicker wind-up and slightly less frantic slash".
The source clip (Mixamo SwordAttackR6 with an added lead) lowers the guard for 0.65 s, raises the sword behind in
0.15 s, holds 0.1 s, cuts a full arc in 0.15 s (impact mid-arc at 0.9833 s, peak 125 m/s) and then swings a second,
fast backhand across the front (1.2-1.4 s, ~20 m/s) before returning to guard; that backhand reads as the slash.
New timing, MM8 native m604 attack proportions (8 x 0.125 s: raise 2 frames, cut 2, follow-through/recovery 3):
  wind-up      0.00-0.42 s  eased pose blend from the guard (source 0) to the cock pose (source 0.82): the source's
                            dip to the low left before the raise is skipped, as in native frames 0-2
  held cock    0.42-0.68 s  source 0.82-0.90, drifting slowly into the slash
  slash        0.68-1.12 s  source 0.90-1.05, eased in and out, source 0.9833 stays at 0.9833 (impact)
  overshoot    1.12-1.25 s  source 1.05-1.067 (the blade hangs past the cut)
  recovery     1.25-1.733 s eased pose blend from source 1.067 to the clip's final pose (source 1.7333), which
                            replaces the backhand; the end pose, loop and idle blend are unchanged.
The pose blends apply to the upper body (spine, arms, head, sword, sockets) only: blending the pelvis and legs
dipped the feet 4 cm under the floor, so the pelvis and legs follow the source's own poses (planted stance and steps).
Review 2 ("transition frames attack 13-16 too fast and abrupt", viewer 48 fps = 0.27-0.33 s): the source legs stand
still until 0.667 s and then start a stance shift at full speed (~1,100 deg/s within one key, the splice of the added
lead); a plain time warp squeezed it to 1,600 deg/s at 0.30 s. Now the legs travel the source path by arc length
(summed lower-body joint rotation, pelvis translation 1 cm = 1 deg) at smootherstep speed: 0-0.52 s from the guard
to the cocked stance (source 0.82), overlapping the upper-body wind-up, and 1.25-1.733 s for the recovery. The
upper body ends its wind-up on the settled cock pose (source 0.82, after the raise decelerates) at 0.42 s; the hold
drifts slowly (Hermite, slope 0.1 -> the slash warp's slope) into the slash at 0.68 s. Legs follow the same hold.
Arc length smooths the total leg motion, but the source switches abruptly from a slow sway to a thigh-only burst,
so single bones still stepped; the legs are low-passed over 0-0.62 s (Gaussian sigma 0.06 s, tapered to the window
ends so the start pose and the cocked stance are kept).
Every channel keeps its key times (120 Hz) and interpolation; only output values change, in place.
Usage: retime_attack.py <in.glb> <out.glb> [clip]"""
import struct
import sys
from pathlib import Path

import numpy as np
from scipy.interpolate import Akima1DInterpolator, CubicHermiteSpline, PchipInterpolator

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

WINDUP = (0.42, 0.82)          # upper-body blend end (new time, source time): the settled cock pose
LEGS = (0.52, 0.82)            # leg arc-length window end (runs into the hold)
HOLD_END = (0.68, 0.90)        # slash start
WARP = [HOLD_END, (0.9833, 0.9833), (1.12, 1.05), (1.25, 1.0667)]
LEG_SMOOTH = (0.0, 0.76, 0.06)  # leg low-pass window and Gaussian sigma (s), tapered to the window ends
UPPER_SMOOTH = (0.36, 0.74, 0.03)  # upper body around the hold (review 3), tapered the same way
SPLINE_UNTIL = 0.90            # source time: spline sampling before the slash (a key, so both samplers meet there);
                               # the slash and recovery keep glTF lerp, as accepted in review 1
SLASH_ANCHOR = (0.40, 0.80)    # shapes the slash spline as accepted in review 1 (used for t >= 0.68 only)
LOWER = ('B_Pelvis', 'B_L_Thigh', 'B_R_Thigh', 'B_L_Calf', 'B_R_Calf', 'B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0')
BLEND = (1.25, 1.7333)          # recovery: blend from source WARP[-1] to the final pose
END = 1.7333


def view(doc, binary, index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    comp = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a['type']]
    assert a['componentType'] == 5126 and v.get('byteStride', comp * 4) == comp * 4
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return off, np.frombuffer(binary, np.float32, a['count'] * comp, off).reshape(a['count'], comp).copy()


def slerp(q0, q1, f):
    q0 = q0 / np.linalg.norm(q0, axis=-1, keepdims=True); q1 = q1 / np.linalg.norm(q1, axis=-1, keepdims=True)
    d = (q0 * q1).sum(-1, keepdims=True); q1 = np.where(d < 0, -q1, q1); d = np.abs(d)
    th = np.arccos(np.clip(d, -1, 1)); s = np.sin(th)
    small = s < 1e-6
    a = np.where(small, 1 - f, np.sin((1 - f) * th) / np.where(small, 1, s))
    b = np.where(small, f, np.sin(f * th) / np.where(small, 1, s))
    q = a * q0 + b * q1
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


def knots(times, values, path):
    """key indices of the source's own cadence: the 120 Hz keys are a linear resampling of 30 Hz Mixamo keys, so
    every 4th key reproduces the others (checked); else every key"""
    idx = np.r_[np.arange(0, len(times) - 1, 4), len(times) - 1]
    if len(times) < 9 or abs(np.median(np.diff(times)) - 1 / 120) > 1e-4:
        return np.arange(len(times))
    lin = sample_linear(times[idx], values[idx], path, times)
    err = np.abs(np.abs((lin * values).sum(1)) - 1).max() if path == 'rotation' else np.abs(lin - values).max()
    return idx if err < 1e-5 else np.arange(len(times))


def sample(times, values, interp, path, t, smooth=True):
    """channel value at source times t. STEP = previous key; LINEAR is sampled through a velocity-continuous
    spline (modified Akima, no overshoot on still stretches) over the source keys: the retime slows parts of the clip
    down, and lerping between the 30 Hz source keys then shows each key as a sudden speed change (review 3, viewer
    frames 28-29 = the 0.867 s source key during the hold). smooth=False keeps glTF lerp / slerp: the legs, whose
    floor contacts the source places at its keys (a spline floated the feet 1 cm in the slash step)"""
    t = np.clip(t, times[0], times[-1])
    if interp == 'STEP':
        i = np.clip(np.searchsorted(times, t, side='right') - 1, 0, len(times) - 2)
        return values[np.where(t >= times[-1], len(times) - 1, i)]
    if not smooth:
        return sample_linear(times, values, path, t)
    idx = knots(times, values, path)
    k, v = times[idx], values[idx].astype(np.float64)
    if len(k) < 3:
        return sample_linear(times, values, path, t)
    if path == 'rotation':
        v = v.copy()
        for j in range(1, len(v)):
            if (v[j] * v[j - 1]).sum() < 0:
                v[j] = -v[j]
    out = Akima1DInterpolator(k, v, axis=0, method='makima')(t)
    if path == 'rotation':
        out /= np.linalg.norm(out, axis=1, keepdims=True)
    late = t > SPLINE_UNTIL
    out[late] = sample_linear(times, values, path, t[late])
    return out.astype(values.dtype)


def sample_linear(times, values, path, t):
    """glTF LINEAR semantics: lerp / slerp between keys"""
    t = np.clip(t, times[0], times[-1])
    i = np.clip(np.searchsorted(times, t, side='right') - 1, 0, len(times) - 2)
    f = ((t - times[i]) / np.maximum(times[i + 1] - times[i], 1e-9))[:, None]
    if path == 'rotation':
        return slerp(values[i], values[i + 1], f)
    return values[i] * (1 - f) + values[i + 1] * f


def low_pass(times, out, path, window=LEG_SMOOTH):
    t0, t1, sigma = window
    sel = np.where((times >= t0 - 5 * sigma) & (times <= t1 + 5 * sigma))[0]
    v = out[sel].astype(np.float64).copy()
    if path == 'rotation':
        for i in range(1, len(v)):
            if (v[i] * v[i - 1]).sum() < 0:
                v[i] = -v[i]
    dt = float(np.median(np.diff(times))); k = np.arange(-int(4 * sigma / dt), int(4 * sigma / dt) + 1)
    g = np.exp(-0.5 * (k * dt / sigma) ** 2); g /= g.sum()
    pad = np.concatenate([np.repeat(v[:1], len(k) // 2, 0), v, np.repeat(v[-1:], len(k) // 2, 0)])
    sm = np.stack([np.convolve(pad[:, c], g, 'valid') for c in range(v.shape[1])], 1)
    if path == 'rotation':
        sm /= np.linalg.norm(sm, axis=1, keepdims=True)
    tt = times[sel]; w = smoother(np.minimum((tt - t0) / 0.08, (t1 - tt) / 0.08))[:, None]
    res = slerp(v, sm, w) if path == 'rotation' else v * (1 - w) + sm * w
    out[sel] = res.astype(out.dtype)


def smoother(u):
    u = np.clip(u, 0, 1)
    return u * u * u * (u * (u * 6 - 15) + 10)


def lower_arc(doc, binary, anim):
    """cumulative lower-body motion D(t) over source time (deg; pelvis translation 1 cm = 1 deg) on a dense grid"""
    grid = np.linspace(0, END, 4001); acc = np.zeros(len(grid))
    for ch in anim['channels']:
        if doc['nodes'][ch['target']['node']]['name'] not in LOWER or ch['target']['path'] == 'scale':
            continue
        s = anim['samplers'][ch['sampler']]
        _, times = view(doc, binary, s['input']); _, vals = view(doc, binary, s['output'])
        v = sample(times[:, 0], vals, s.get('interpolation', 'LINEAR'), ch['target']['path'], grid, smooth=False)
        if ch['target']['path'] == 'rotation':
            step = np.degrees(2 * np.arccos(np.clip(np.abs((v[1:] * v[:-1]).sum(1)), 0, 1)))
        else:
            step = np.linalg.norm(np.diff(v, axis=0), axis=1) * 100
        acc[1:] += step
    D = np.cumsum(acc) + grid * 1e-6            # strictly increasing
    return grid, D


def retime(doc, binary, clip='Attack'):
    anim = next(a for a in doc['animations'] if a['name'] == clip)
    warp = PchipInterpolator([p[0] for p in [SLASH_ANCHOR] + WARP], [p[1] for p in [SLASH_ANCHOR] + WARP])
    slope = float(warp.derivative()(HOLD_END[0]))
    hold_up = CubicHermiteSpline([WINDUP[0], HOLD_END[0]], [WINDUP[1], HOLD_END[1]], [0.1, slope])
    hold_legs = CubicHermiteSpline([LEGS[0], HOLD_END[0]], [LEGS[1], HOLD_END[1]], [0.0, slope])
    grid, D = lower_arc(doc, binary, anim)
    arc = lambda t, n0, n1, o0, o1: np.interp(np.interp(o0, grid, D) + smoother((t - n0) / (n1 - n0))
                                              * (np.interp(o1, grid, D) - np.interp(o0, grid, D)), D, grid)

    def lower_time(t):
        return np.select([t <= LEGS[0], t <= HOLD_END[0], t <= WARP[-1][0]],
                         [arc(t, 0, LEGS[0], 0, LEGS[1]), hold_legs(t), warp(t)],
                         arc(t, WARP[-1][0], END, WARP[-1][1], END))
    done = set()
    # the exporter shares constant output accessors between clips: a shared constant channel needs no retiming and
    # must stay byte-identical for the other clips; a shared varying one gets its own copy first
    shared = {s['output'] for a in doc['animations'] if a is not anim for s in a['samplers']}
    for ch in anim['channels']:
        s = anim['samplers'][ch['sampler']]
        if s['output'] in done:
            continue
        done.add(s['output'])
        _, times = view(doc, binary, s['input']); times = times[:, 0]
        off, vals = view(doc, binary, s['output'])
        if s['output'] in shared:
            if np.allclose(vals, vals[0], atol=1e-7):
                continue
            from build_actor_lods import append_accessor
            s['output'] = append_accessor(doc, binary, doc['accessors'][s['output']], vals.tobytes())
            done.add(s['output']); off, vals = view(doc, binary, s['output'])
        interp = s.get('interpolation', 'LINEAR'); path = ch['target']['path']
        assert abs(times[-1] - END) < 1e-3, times[-1]
        out = np.empty_like(vals)

        def blend(sel, t0, t1, src0, src1):
            a = sample(times, vals, interp, path, np.full(sel.sum(), src0))
            b = sample(times, vals, interp, path, np.full(sel.sum(), src1))
            u = np.clip((times[sel] - t0) / (t1 - t0), 0, 1)
            f = (u * u * u * (u * (u * 6 - 15) + 10))[:, None]          # smootherstep: eased in and out
            out[sel] = slerp(a, b, f) if path == 'rotation' else a * (1 - f) + b * f
            if interp == 'STEP':
                out[sel] = np.where(f < .5, a, b)
        if doc['nodes'][ch['target']['node']]['name'] in LOWER:
            out[:] = sample(times, vals, interp, path, lower_time(times), smooth=False)
            if interp != 'STEP' and path != 'scale':
                low_pass(times, out, path)
            binary[off:off + out.nbytes] = out.astype(np.float32).tobytes()
            continue
        first = times < WINDUP[0]
        blend(first, 0.0, WINDUP[0], 0.0, WINDUP[1])
        hold = ~first & (times < HOLD_END[0])
        out[hold] = sample(times, vals, interp, path, hold_up(times[hold]))
        mid = (times >= HOLD_END[0]) & (times <= WARP[-1][0])
        out[mid] = sample(times, vals, interp, path, warp(times[mid]))
        last = times > WARP[-1][0]
        blend(last, BLEND[0], BLEND[1], WARP[-1][1], END)
        if interp != 'STEP' and path != 'scale':
            low_pass(times, out, path, UPPER_SMOOTH)
        binary[off:off + out.nbytes] = out.astype(np.float32).tobytes()
    return anim


if __name__ == '__main__':
    src, dst = Path(sys.argv[1]), Path(sys.argv[2]); clip = sys.argv[3] if len(sys.argv) > 3 else 'Attack'
    doc, binary = read_glb(src); binary = bytearray(binary)
    anim = retime(doc, binary, clip)
    write_glb(dst, doc, bytes(binary))
    print('RETIMED', clip, 'in', src.name, '->', dst.name, len(anim['channels']), 'channels')
