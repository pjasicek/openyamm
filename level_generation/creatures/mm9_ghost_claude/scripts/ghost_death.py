#!/usr/bin/env python3
"""MM9's Ghost has no death clip (MONSTERS row, GHOST.scr: the body just goes). Ours dissolves, with what the renderer allows: alpha cannot animate, so the spirit whirls up and shrinks to nothing.
Death: the start of winceAir2 (it throws the arms and the head) up to T_FREEZE, then the source slows to a stop while the Scene Root turns TURN degrees about the vertical, rises RISE metres and
scales to END with an ease-in. Dead: the last pose held; 1 mm of geometry is left at the corpse's place (the native corpse is empty, as the air elemental's).
Uniform scale on the root only: joints carry uniform scale. Usage: ghost_death.py in.glb out.glb"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb
DUR, T_FREEZE, T_SRC_END, TURN, RISE, END, FADE0, FPS = 1.75, 0.42, 0.66, 300.0, 0.34, 0.002, 0.45, 30
g = Glb(sys.argv[1])
doc = g.json
nodes = doc['nodes']
root = next(i for i, n in enumerate(nodes) if n.get('name') == 'Scene Root')
anims = {a['name']: a for a in doc['animations']}
A = anims['Death']; D = anims['Dead']
times = np.arange(0, DUR + 1e-6, 1 / FPS)


def src_time(t):
    t = np.asarray(t)
    out = t.copy()
    u = np.clip((t - T_FREEZE) / (DUR - T_FREEZE), 0, 1)
    # continuous speed at T_FREEZE, slowing to rest at the end
    return np.where(t < T_FREEZE, t, T_FREEZE + (T_SRC_END - T_FREEZE) * (1 - (1 - u) ** 2))


st = src_time(times)
u = np.clip((times - FADE0) / (DUR - FADE0), 0, 1)
scale = END ** (u ** 2.2)
turn = np.radians(TURN) * u ** 1.6
rise = RISE * u ** 1.5
samplers = A['samplers']; channels = A['channels']
root_t = root_r = None
for ch in channels:
    s = samplers[ch['sampler']]
    path = ch['target']['path']
    tin = g.accessor(s['input'])[:, 0]
    val = g.accessor(s['output']).astype(np.float64)
    if path == 'rotation':
        for i in range(1, len(val)):
            if val[i] @ val[i - 1] < 0:
                val[i] = -val[i]
    new = np.stack([np.interp(st, tin, val[:, c]) for c in range(val.shape[1])], 1)
    if path == 'rotation':
        new /= np.linalg.norm(new, axis=1, keepdims=True)
    if ch['target']['node'] == root:
        if path == 'translation':
            new[:, 1] += rise; root_t = True
        if path == 'rotation':
            q = np.stack([np.zeros_like(turn), np.sin(turn / 2), np.zeros_like(turn), np.cos(turn / 2)], 1)
            x1, y1, z1, w1 = q.T; x2, y2, z2, w2 = new.T
            new = np.stack([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2], 1)
            root_r = True
    s['input'] = g.append_accessor(times[:, None], 'SCALAR')
    s['output'] = g.append_accessor(new, 'VEC3' if new.shape[1] == 3 else 'VEC4')
    s['interpolation'] = 'LINEAR'
assert root_t and root_r, 'Scene Root needs its channels in Death'
base = np.array(nodes[root].get('scale', [1, 1, 1]), float)
samplers.append({'input': g.append_accessor(times[:, None], 'SCALAR'), 'output': g.append_accessor(base[None] * scale[:, None], 'VEC3'), 'interpolation': 'LINEAR'})
channels.append({'sampler': len(samplers) - 1, 'target': {'node': root, 'path': 'scale'}})
# Dead = last pose of the new Death
for ch in D['channels']:
    s = D['samplers'][ch['sampler']]
    node, path = ch['target']['node'], ch['target']['path']
    src = next(c for c in channels if c['target'] == ch['target'])
    v = g.accessor(samplers[src['sampler']]['output'])[-1:]
    s['output'] = g.append_accessor(np.repeat(v, g.json['accessors'][s['input']]['count'], 0), 'VEC3' if v.shape[1] == 3 else 'VEC4')
tt = g.accessor(D['samplers'][0]['input'])
D['samplers'].append({'input': D['samplers'][0]['input'], 'output': g.append_accessor(np.repeat(base[None] * END, len(tt), 0), 'VEC3'), 'interpolation': 'LINEAR'})
D['channels'].append({'sampler': len(D['samplers']) - 1, 'target': {'node': root, 'path': 'scale'}})
# the speck rests on the floor: Dead's root moved down by its height
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Model
g.write(sys.argv[2])
g2 = Glb(sys.argv[2])
low = Model(g2).lowest('Dead', 0.0)
doc2 = g2.json
D2 = next(a for a in doc2['animations'] if a['name'] == 'Dead')
c = next(c for c in D2['channels'] if c['target'] == {'node': root, 'path': 'translation'})
s_ = D2['samplers'][c['sampler']]
v = g2.accessor(s_['output']).copy(); v[:, 1] -= low
s_['output'] = g2.append_accessor(v, 'VEC3')
g2.write(sys.argv[2])
print('DEATH', DUR, 's, scale end', END)
