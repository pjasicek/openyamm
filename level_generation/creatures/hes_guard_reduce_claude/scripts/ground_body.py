#!/usr/bin/env python3
"""Corpse body onto the floor, cloth left out (guard fix 2026-10-22, step 1 of 3).

At the end of Death (and in Dead) the guard lay face down with his body 19-35 cm above the floor: the source
project's death_floor.py counted the rifle (rigid in the right fist, pointing straight down) and the coat skirt
(Robe_* chains, hanging straight down under the lying body) as floor contacts. floor_fix.py --ground-death counts
every visible vertex too, so the hanging skirt alone still held the body 19 cm up.
This step moves the root joint like --ground-death, but measures only the body (vertices whose Robe_* weight is at
most ROBE_MAX): DEAD's corpse onto the floor, DEATH raised where the body goes under it and lowered toward the corpse
height while above it, on a 1/120 s grid (root keys there). The skirt then hangs under the floor; step 2 is floor_fix.py --lift-joints Death Dead
--lift-only 'Robe_*' --ground-death Death Dead (bends the strips onto the floor, settles any rest), step 3
death_rifle_floor.py (the rifle laid down). Usage: ground_body.py <in.glb> <out.glb>"""
from pathlib import Path
import sys
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
import glb_pose  # noqa: E402
from floor_fix import shift_roots  # noqa: E402
ROBE_MAX, TOL = 0.5, 0.001
src, out = Path(sys.argv[1]), Path(sys.argv[2])
model = glb_pose.Model(glb_pose.Glb(src)); nodes = model.glb.json['nodes']
robe_joint = np.array([nodes[j].get('name', '').startswith('Robe_') for j in model.joints])
body_masks = []
for p in model.primitives:
    if p['skinned']:
        body_masks.append((p['weights'] * robe_joint[p['joints']]).sum(1) <= ROBE_MAX)
    else:
        body_masks.append(np.ones(len(p['positions']), bool))


def body_lows(clip, dense=False):
    times = model.clip_times(clip)
    if dense:   # the kneeling impact is fast: root keys only at the clip keys dipped 3.5 cm between frames 42 and 43
        # grid times within 0.1 ms of a clip key are dropped: 2.1 (grid) and the stored key 2.0999999 (float32) were
        # merged as two keys that are equal once stored as float32 (B_Pelvis Death keys 294/295; the engine rejected
        # the model). check_key_times.py gates every export for this.
        keys = np.array(times)
        grid = [g for g in np.arange(0, times[-1], 1 / 120) if np.abs(keys - g).min() > 1e-4]
        times = sorted(set(float(x) for x in np.float32(list(times) + grid)))
    lows = []
    for t in times:
        posed = model.skinned_positions(model.world(model.sample(clip, t)))
        lows.append(min(float(pts[m, 1].min()) for (pts, _), m in zip(posed, body_masks) if m.any()))
    return np.array(times), np.array(lows)


dt, dl = body_lows('Dead'); shift_roots(model, 'Dead', dt, -dl); corpse = float(dl[-1])
t, low = body_lows('Death', dense=True)
off = np.where(low < -TOL, -low, -np.clip(low, 0.0, max(corpse, 0.0)))
shift_roots(model, 'Death', t, off)
_, after = body_lows('Death', dense=True)
print(f'GROUNDBODY Dead corpse body moved {-corpse:+.4f}; Death body lowest {low.min():+.4f}..{low[-1]:+.4f} -> '
      f'{after.min():+.4f}..{after[-1]:+.4f}')
model.glb.write(out)
