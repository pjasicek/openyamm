#!/usr/bin/env python3
"""Prints each dungeon door's click face and the outside arrival 400 in front of it, from X2's build."""
import json, math, sys
B = sys.argv[1] if len(sys.argv) > 1 else 'output/studio_cal/x2/build'
m = json.load(open(B + '/export.json'))['map']
b = json.load(open(B + '/build.json'))
hm = m['terrain']['height_map']
def ground(X, Y):
    x = X / 512.0 + 64; y = 64 - Y / 512.0
    i, j = int(math.floor(x)), int(math.floor(y)); fx, fy = x - i, y - j
    h = lambda a, c: hm[c * 128 + a] * 32
    return h(i, j) * (1 - fx) * (1 - fy) + h(i + 1, j) * fx * (1 - fy) + h(i, j + 1) * (1 - fx) * fy + h(i + 1, j + 1) * fx * fy
bm = {x['name']: x for x in m['bmodels']}
def face(name):
    x = bm[name]
    for f in x['faces']:
        if f['texture'] == '7solid01':
            vs = [x['vertices'][i] for i in f['vertices']]
            n = f['plane_normal']
            return (round(sum(v[0] for v in vs) / len(vs)), round(sum(v[1] for v in vs) / len(vs)), min(v[2] for v in vs)), (round(n[0] / 65536), round(n[1] / 65536))
out = {}
for k, n in (('xd21', 'thing:den_door'), ('xd27', 'thing:ogre_lair')):
    out[k] = face(n)
for k, n in (('xd06', 'thing:yak_temple'), ('xd12', 'thing:darzog_tower')):
    d = [x for x in b['buildings'] if x['id'] == n][0]
    out[k] = (tuple(d['door']), tuple(d['normal']))
for k, ((x, y, z), (nx, ny)) in out.items():
    ax, ay = x + nx * 400, y + ny * 400
    print(k, 'face', (x, y, z), 'normal', (nx, ny), 'arrival', (ax, ay, round(ground(ax, ay))),
          'cells', (round(x / 512 + 64, 2), round(64 - y / 512, 2)))
