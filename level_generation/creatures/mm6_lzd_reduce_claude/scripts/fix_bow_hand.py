"""Turn the left (bow) hand from hyper-supinated (palm out, thumb back) to a neutral hold (palm toward the thigh,
thumb forward) by a twist of THETA degrees about the forearm axis (Forearm local +Y), spread along the arm:
Forearm FA (fraction), ForearmTwist TW, Hand 1. The sign passes the palm through 'forward' (de-supination).
In Death the bow is released at RELEASE s (mm6_lzd_codex/gates.json) and falls on its own (Bow keyed relative to the
hand): from the release it blends from the corrected hand to its original world path by RELEASE + 0.35 s (it lands
at about 1.0 s), so the fall starts where the hand holds it and lands where it did. Weight per clip: 1 for the lowered-bow clips, by forearm drop for Attack/Cast (0 once the bow arm is raised for the
draw), fading out between 15 and 25 % of Death (finished before the release), 0 for Dead. The changed channels get new accessors (the source shares
output accessors between clips) resampled on the union of their key times, LINEAR. Bow, Arrow and sockets are
children of the hand and follow it. Usage: fix_bow_hand.py <in.glb> <out.glb> [THETA=200] [FA=0.25] [TW=0.6]"""
import copy
import os
import struct
import sys
from pathlib import Path
import numpy as np
from gltf_fk import Gltf, qmul, qaxis, qmat, matq, slerp, read_glb  # noqa: F401
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import write_glb, append_accessor  # noqa: E402
import bow_hand_probe as probe  # noqa: E402

src, dst = sys.argv[1], sys.argv[2]
THETA, FA, TW = (float(x) for x in (sys.argv[3:] + ['200', '0.25', '0.6'][len(sys.argv[3:]):]))
g = Gltf(src); probe.g = g; N = g.names
FORE, TWIST, HAND, BOW = N['B_L_Forearm'], N['B_L_ForearmTwist'], N['B_L_Hand'], N['Bow']
RELEASE, BLEND = 0.5, 0.35
Y = np.array([0.0, 1.0, 0.0])


def keys(t):
    """sorted key times, unique after float32 storage and at least 1e-4 s apart (glTF needs strictly increasing)"""
    t = np.unique(np.asarray(t, np.float32)).astype(float); out = [t[0]]
    for x in t[1:]:
        if x - out[-1] > 1e-4: out.append(x)
    return np.array(out)


def smooth(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def weight(clip, t):
    if clip == 'Dead':
        return 0.0
    if clip == 'Death':  # fade out between DEATH_FADE=start,end fractions of the clip (default 0.15,0.25: done by the release at 0.5 s; later fades swept the falling bow through the neck, earlier ones the calf)
        a, b = (float(x) * g.duration(clip) for x in os.environ.get('DEATH_FADE', '0.15,0.25').split(','))
        return 1 - float(smooth((t - a) / (b - a)))
    if clip in ('Attack', 'Cast'):
        return float(smooth(probe.frame(clip, t)['forearm_down'] / 0.8))  # unwinds over the whole raise (~0.28 s)
    return 1.0


def corrected(clip, t, theta):
    """new local rotations of Forearm, ForearmTwist, Hand at time t for a total twist theta (radians)"""
    a = theta * FA
    qf = qmul(g.sample(clip, FORE, 'rotation', t), qaxis(Y, a))              # about its own axis
    qt = qmul(qaxis(Y, theta * TW - a), g.sample(clip, TWIST, 'rotation', t))  # about the parent's (forearm) axis
    qh = qmul(qaxis(Y, theta - a), g.sample(clip, HAND, 'rotation', t))
    return qf, qt, qh


# sign: at half the twist the palm must face forward (Standing, frame 0)
sign = None
for s in (1, -1):
    qf, qt, qh = corrected('Standing', 0.0, s * np.radians(THETA) / 2)
    ov = {(FORE, 'rotation'): lambda t, q=qf: q, (TWIST, 'rotation'): lambda t, q=qt: q, (HAND, 'rotation'): lambda t, q=qh: q}
    if probe.frame('Standing', 0.0, ov)['palm_fwd'] > 0:
        sign = s
assert sign is not None
theta = sign * np.radians(THETA)
doc = copy.deepcopy(g.doc); binary = bytearray(g.bin)
for a in doc['animations']:
    clip = a['name']
    chans = {}
    for c in a['channels']:
        if c['target']['path'] == 'rotation' and c['target']['node'] in (FORE, TWIST, HAND):
            chans[c['target']['node']] = c
    times = np.unique(np.concatenate([np.atleast_1d(g.floats(a['samplers'][c['sampler']]['input'])) for c in chans.values()]))
    if clip in ('Attack', 'Cast', 'Death'):  # weights vary: key every source frame
        times = np.concatenate([times, np.arange(0, g.duration(clip) + 1e-6, 1 / 48)])
    times = keys(times)
    ws = [weight(clip, t) for t in times]
    if max(ws) == 0:
        continue
    vals = {FORE: [], TWIST: [], HAND: []}
    for t, w in zip(times, ws):
        for node, q in zip((FORE, TWIST, HAND), corrected(clip, t, theta * w)):
            vals[node].append(q / np.linalg.norm(q))
    tin = append_accessor(doc, binary, {'componentType': 5126, 'type': 'SCALAR', 'count': len(times),
                                        'min': [float(times[0])], 'max': [float(times[-1])]},
                          struct.pack(f'<{len(times)}f', *times))
    for node, c in chans.items():
        out = append_accessor(doc, binary, {'componentType': 5126, 'type': 'VEC4', 'count': len(times)},
                              struct.pack(f'<{4 * len(times)}f', *np.array(vals[node]).reshape(-1)))
        a['samplers'].append({'input': tin, 'output': out, 'interpolation': 'LINEAR'})
        c['sampler'] = len(a['samplers']) - 1
    if clip == 'Death':
        btimes = keys(np.concatenate([times, np.atleast_1d(g.floats(g.channel(clip, BOW, 'rotation')[1]['input']))]))
        bt, br = [], []
        qs = corrected(clip, RELEASE, theta * weight(clip, RELEASE))
        ov = {(nd, 'rotation'): (lambda tt, q=q: q) for nd, q in zip((FORE, TWIST, HAND), qs)}
        orig_r = g.world(clip, BOW, RELEASE)
        held_r = g.world(clip, HAND, RELEASE, ov) @ np.linalg.inv(g.world(clip, HAND, RELEASE)) @ orig_r
        release_dp = held_r[:3, 3] - orig_r[:3, 3]; release_dq = matq(held_r[:3, :3] @ orig_r[:3, :3].T)
        for t in btimes:
            w = weight(clip, t); qs = corrected(clip, t, theta * w)
            ov = {(nd, 'rotation'): (lambda tt, q=q: q) for nd, q in zip((FORE, TWIST, HAND), qs)}
            hand = g.world(clip, HAND, t, ov); orig = g.world(clip, BOW, t)
            if t <= RELEASE:
                loc = np.linalg.inv(g.world(clip, HAND, t)) @ orig      # held: unchanged local
            else:  # the original throw, offset by the release-moment difference, which decays to zero
                f = float(smooth((t - RELEASE) / BLEND))
                dq = slerp(release_dq, np.array([0.0, 0, 0, 1]), f)
                W = np.eye(4); W[:3, 3] = orig[:3, 3] + release_dp * (1 - f)
                W[:3, :3] = qmat(dq) @ orig[:3, :3]
                loc = np.linalg.inv(hand) @ W
            bt.append(loc[:3, 3]); br.append(matq(loc[:3, :3]))
        bin_ = append_accessor(doc, binary, {'componentType': 5126, 'type': 'SCALAR', 'count': len(btimes),
                                             'min': [float(btimes[0])], 'max': [float(btimes[-1])]},
                               struct.pack(f'<{len(btimes)}f', *btimes))
        for path, vals_ in (('translation', bt), ('rotation', br)):
            c = next(c for c in a['channels'] if c['target']['node'] == BOW and c['target']['path'] == path)
            out = append_accessor(doc, binary, {'componentType': 5126, 'type': 'VEC3' if path == 'translation' else 'VEC4',
                                                'count': len(btimes)}, struct.pack(f'<{len(btimes) * len(vals_[0])}f', *np.array(vals_).reshape(-1)))
            a['samplers'].append({'input': bin_, 'output': out, 'interpolation': 'LINEAR'}); c['sampler'] = len(a['samplers']) - 1
    print('FIXED', clip, len(times), 'keys, weight', round(min(ws), 2), '-', round(max(ws), 2))
# drop now unused samplers? keep them: glTF allows unreferenced samplers; compact below removes nothing referenced
for a in doc['animations']:
    used = sorted({c['sampler'] for c in a['channels']}); remap = {o: i for i, o in enumerate(used)}
    a['samplers'] = [a['samplers'][i] for i in used]
    for c in a['channels']:
        c['sampler'] = remap[c['sampler']]
write_glb(Path(dst), doc, bytes(binary))
print('THETA', round(np.degrees(theta), 1), 'FA', FA, 'TW', TW, '->', dst)
