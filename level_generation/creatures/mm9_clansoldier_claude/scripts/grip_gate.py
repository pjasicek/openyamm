#!/usr/bin/env python3
"""Grip gate, both hands, every clip: finger skin against the weapon's grip: verts inside the grip cylinder (depth, count), per finger how far it wraps round the axis, thumb reach, and the weapon's rigid lock to the hand across the clip. Grip centres and axes from work/grips.json (finish_clan.py, Blender rest frame without the lift). Args: <glb> [out]"""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
g = Glb(Path(sys.argv[1])); m = Model(g)
names = [n.get('name') for n in g.json['nodes']]; jn = [names[j] for j in m.joints]
P = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
dom = np.concatenate([np.array([jn[j] for j in p['joints'][np.arange(len(p['joints'])), p['weights'].argmax(1)]]) for p in P]).astype(str)
def allpos(w): return np.vstack([m.skinned_positions(w)[i][0] for i in range(len(P))])
GR = json.load(open('work/grips.json'))
W = {'R': ('Ybasesword', 0.0130, 0.058), 'L': ('Ybaseshield', 0.0135, 0.075)}          # bone, grip radius, half length of the hold
rest = allpos(m.world({}))
lift = rest[:, 1].min()
conv = lambda v: np.array([v[0], v[2], -v[1]])
w0 = m.world({})
out = []
for S, (bone, R, H) in W.items():
    G0 = conv(GR[S]['G']) + np.array([0, -lift if False else 0, 0]); U0 = conv(GR[S]['U'])
    # the lift: rest hand joint in glTF minus its Blender height is common to all nodes: take it from the weapon bone
    bi = names.index(bone); ji = jn.index(bone)
    bone_rest = w0[bi][:3, 3]
    G0 = bone_rest.copy()                                    # the weapon bone sits on the grip's centre (finish_clan.py)
    F = {f: np.where(np.char.startswith(dom, f'Bip01 {S} {f}'))[0] for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')}
    for clip in [a['name'] for a in g.json['animations']]:
        dur = m.clip_times(clip)[-1]; rows = {}; worst = 0.0; nin = 0; lock = []
        for t in np.linspace(0, dur, 5):
            wc = m.world(m.sample(clip, float(t))); X = allpos(wc)
            Sk = wc[bi] @ m.inverse_binds[ji]
            G = (Sk @ np.r_[G0, 1])[:3]; U = Sk[:3, :3] @ U0
            for f, ids in F.items():
                v = X[ids] - G; a_ = v @ U; pr = v - np.outer(a_, U); r = np.linalg.norm(pr, axis=1)
                on = np.abs(a_) < H
                if on.any():
                    worst = max(worst, float((R - r[on]).max())); nin += int((r[on] < R - 0.001).sum())
                k = on & (r < 0.042)
                if k.sum() > 3:
                    e1 = np.cross(U, [0.3, 0.9, 0.2]); e1 /= np.linalg.norm(e1); e2 = np.cross(U, e1)
                    ang = np.degrees(np.arctan2(pr[k] @ e2, pr[k] @ e1))
                    rows.setdefault(f, []).append(len(np.unique((ang // 15).astype(int))) * 15)
                else: rows.setdefault(f, []).append(0)
            hd = names.index(f'Bip01 {S} Hand'); lock.append(np.linalg.inv(wc[hd]) @ wc[bi])
        dl = max(float(np.degrees(np.arccos(np.clip((np.trace(l[:3, :3].T @ lock[0][:3, :3]) - 1) / 2, -1, 1)))) for l in lock)
        out.append(f"{S} {clip:13s} inside grip: max {worst * 100:4.1f} cm, {nin:4d} vert-samples | wrap deg " + ' '.join(f'{f} {int(np.median(v))}' for f, v in rows.items()) + f' | rigid to hand {dl:.1f} deg')
        print(out[-1], flush=True)
if len(sys.argv) > 2: open(sys.argv[2], 'w').write('\n'.join(out) + '\n')
