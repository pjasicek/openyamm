#!/usr/bin/env python3
"""Floor pass without per-frame root jitter (brief: corrections are low-passed, never per frame). floor_fix.py's
--ground-loop and --raise shift the root by the exact lowest point at every key, which feeds the kink of every foot
exchange into the body. Here the shift is a smooth curve:
- loops (--loop CLIP): the wanted shift (minus the lowest point) low-passed periodically (Gaussian, sigma LOOP_SIGMA
  of a cycle), plus the constant that puts the lowest point of the clip on the floor; first and last key get the same
  value, so the seam stays closed;
- one-shots (--raise CLIP): the needed lift, dilated by RAISE_HOLD seconds, smoothed by RAISE_SIGMA seconds, scaled until
  it covers every key; it fades in and out with the clip (0 at start/end when the clip does not need it there).
--ground-death DEATH DEAD: the Dead pose on the floor; Death's shift low-passed the same way, ending on that pose.
Usage: floor_smooth.py in.glb out.glb --loop Standing --loop Walking --raise Hit ... --ground-death Death Dead"""
import argparse, sys
from pathlib import Path
import numpy as np
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose
import floor_fix as FF

LOOP_SIGMA = 0.12
RAISE_HOLD = 0.2
RAISE_SIGMA = 0.08
DEATH_SIGMA = 0.07
ap = argparse.ArgumentParser()
ap.add_argument('input'); ap.add_argument('output')
ap.add_argument('--loop', action='append', default=[])
ap.add_argument('--raise', dest='raises', action='append', default=[])
ap.add_argument('--ground-death', nargs=2)
a = ap.parse_args()
glb = glb_pose.Glb(Path(a.input))
base_shift = 0.0
for clip in a.loop:
    m = glb_pose.Model(glb)
    t, low = FF.lowest_series(m, clip)
    n = len(t) - 1            # last key == first key
    want = -low[:n]
    s = LOOP_SIGMA * n
    off = ndimage.gaussian_filter1d(want, s, mode='wrap')
    off = np.append(off, off[0])
    off += -(low + off).min()
    FF.shift_roots(m, clip, t, off)
    if clip == 'Standing':
        base_shift = float(off.mean())
    print(f'{clip}: loop lift {off.min():+.4f}..{off.max():+.4f}; lowest after {(low + off).min():+.4f}, '
          f'highest lowest point {(low + off).max():+.4f}')
for clip in a.raises:
    m = glb_pose.Model(glb)
    t, low = FF.lowest_series(m, clip)
    # the one-shots start from the idle pose: same constant shift as Standing, so no height step at the blend
    if base_shift:
        FF.shift_roots(m, clip, t, np.full(len(t), base_shift))
        m = glb_pose.Model(glb)
        t, low = FF.lowest_series(m, clip)
    need = np.maximum(-low, 0.0)
    dt = float(np.median(np.diff(t)))
    env = ndimage.maximum_filter1d(need, int(RAISE_HOLD / dt) | 1, mode='nearest')
    off = ndimage.gaussian_filter1d(env, RAISE_SIGMA / dt, mode='constant')
    ok = off > 1e-6
    k = float((need[ok] / off[ok]).max()) if ok.any() and need.max() > 0 else 1.0
    off = off * max(1.0, k)
    FF.shift_roots(m, clip, t, off)
    print(f'{clip}: raise max {off.max():+.4f}; lowest after {(low + off).min():+.4f}')
if a.ground_death:
    death, dead = a.ground_death
    m = glb_pose.Model(glb)
    dt_, dl_ = FF.lowest_series(m, dead)
    FF.shift_roots(m, dead, dt_, -dl_)
    corpse = float(dl_[-1])
    m = glb_pose.Model(glb)
    t, low = FF.lowest_series(m, death)
    raw = np.where(low < 0, -low, -np.clip(low, 0.0, max(corpse, 0.0)))
    dt = float(np.median(np.diff(t)))
    off = ndimage.gaussian_filter1d(raw, DEATH_SIGMA / dt, mode='nearest')
    rest = np.maximum(-(low + off), 0.0)     # what the low-pass left below the floor, as a smooth bump
    if rest.max() > 1e-4:
        env = ndimage.maximum_filter1d(rest, int(RAISE_HOLD / dt) | 1, mode='nearest')
        bump = ndimage.gaussian_filter1d(env, RAISE_SIGMA / dt, mode='nearest')
        ok = bump > 1e-6
        off += bump * max(1.0, float((rest[ok] / bump[ok]).max()))
    # the last key lands exactly on the corpse pose
    ease = np.clip((t - (t[-1] - 0.25)) / 0.25, 0, 1)
    ease = ease * ease * (3 - 2 * ease)
    off = off * (1 - ease) + (-corpse) * ease
    FF.shift_roots(m, death, t, off)
    print(f'{dead}: corpse moved by {-corpse:+.4f}; {death}: lift {off.min():+.4f}..{off.max():+.4f}, '
          f'lowest after {(low + off).min():+.4f}')
glb.write(Path(a.output))
