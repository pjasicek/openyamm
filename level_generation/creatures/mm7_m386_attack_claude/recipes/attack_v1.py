# Robot m386 Attack v1 (attacks-2, 2026-11-11). Faces +Z, +Y up. Native m386aa-ag and the user's design (2026-10):
# "attack = shot with the gun". The installed clip keeps the gun swing, charge, the 0.44 s shot (slide-back and kick),
# jaw snap and re-stow. Added: the whole chassis braces (drops 7 mm, the spikes' retraction limit, leans in, the scorpion tail cocks up over the
# back, the neck stretches to aim) and at the shot the recoil throws the chassis back 6 cm and nose-up 7°, the tail
# whips over and the head snaps back, then it settles with a wobble (length 0.875 s and the 0.441 s impact kept). The
# spike tips stay planted where the installed clip puts them: each sleeve re-aims at its tip and the spike slides
# along it (the walk's own leg mechanism), clamped to the slide range the installed clips use.
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'audit_mm678_20261111/fixes/attacks2_tools'))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared/floor'))
import author_clip as AC  # noqa: E402

CLIP = 'Attack'
SOURCE = 'Attack'
X, Y, Z = [1, 0, 0], [0, 1, 0], [0, 0, 1]
TAIL = {f'Tail{i}': 1.0 for i in range(1, 9)}
LEGS = ['FL', 'FR', 'RL', 'RR']
SLIDE = (-0.127, -0.004)   # Spike_XX local y range of the installed living clips (-0.126 ... -0.0047)

LAYERS = [
    {'joints': {'Body': 1.0}, 'axis': X,
     'keys': [(0, 0), (0.25, 3), (0.4, 3.5), (0.47, -7), (0.55, -6), (0.68, 1.5), (0.78, -0.8), (0.875, 0)]},
    {'joints': {'Neck1': 1.0, 'Neck2': 1.0}, 'axis': X,
     'keys': [(0, 0), (0.25, 4), (0.42, 4), (0.48, -6), (0.6, -3), (0.875, 0)]},
    {'joints': TAIL, 'axis': X,
     'keys': [(0, 0), (0.28, 4.0), (0.42, 4.5), (0.5, 9.0), (0.6, 6.0), (0.75, 1.5), (0.875, 0)]},
    {'joints': TAIL, 'axis': Y,
     'keys': [(0, 0), (0.3, -1.5), (0.48, 3.5), (0.6, -2.5), (0.72, 1.0), (0.875, 0)]},
    {'joints': {'Body': 1.0}, 'axis': Y,
     'keys': [(0, 0), (0.45, 0), (0.5, 2.5), (0.6, -1.5), (0.7, 0.8), (0.875, 0)]},
]
MOVES = [
    {'joint': 'Body', 'keys': [(0, [0, 0, 0]), (0.25, [0, -0.006, 0.012]), (0.42, [0, -0.007, 0.015]),
                               (0.47, [0, 0.008, -0.06]), (0.55, [0, 0.005, -0.065]), (0.68, [0, -0.002, -0.01]),
                               (0.78, [0, 0.002, -0.012]), (0.875, [0, 0, 0])]},
]

_tips = {}


def tip_setup(model, names):
    by = {v: k for k, v in names.items()}
    for leg in LEGS:
        s = by[f'Spike_{leg}']
        j = model.joints.index(s)
        best = 0.0   # the rod's far end along the spike's local Y (its sign depends on the leg's frame)
        inv = model.inverse_binds[j]   # bind space -> the spike's own frame
        for prim in model.primitives:
            if not prim['skinned']:
                continue
            w = np.where(prim['joints'] == j, prim['weights'], 0).sum(axis=1)
            pts = prim['positions'][w > 0.9]
            if len(pts):
                loc = (np.c_[pts, np.ones(len(pts))] @ inv.T)[:, 1]
                far = loc[np.argmax(np.abs(loc))]
                best = far if abs(far) > abs(best) else best
        _tips[leg] = np.array([0.0, best, 0.0, 1.0])


def POST(t, local, ctx):
    model, names, by = ctx['model'], ctx['names'], ctx['by_name']
    if not _tips:
        tip_setup(model, names)
    wb = ctx['base_world']
    for leg in LEGS:
        lg, sp = by[f'Leg_{leg}'], by[f'Spike_{leg}']
        for n in (lg, sp):
            local.setdefault(n, [p.copy() for p in model.rest[n]])
        w = model.world(local)
        target = (wb[sp] @ _tips[leg])[:3]
        pivot = w[lg][:3, 3]
        cur = (w[sp] @ _tips[leg])[:3]
        unit = w[lg][:3, :3] / np.linalg.norm(w[lg][:3, :3], axis=0, keepdims=True)
        w = AC.set_world_rotation(model, local, w, lg, AC.rotation_between(cur - pivot, target - pivot) @ unit)
        cur = (w[sp] @ _tips[leg])[:3]
        scale = np.linalg.norm(w[lg][:3, :3], axis=0)
        axis = w[lg][:3, 1] / scale[1]
        slide = float(np.dot(target - cur, axis)) / scale[1]
        tr = local[sp][0].copy()
        tr[1] = float(np.clip(tr[1] + slide, *SLIDE))
        local[sp] = [tr, local[sp][1], local[sp][2]]
