#!/usr/bin/env python3
"""Dressing check (devdocs/xeen/formats/DRESSING.md, the user's rule of 2026-11-20): every free-standing prop of the
map (decorations not hung on a wall, furniture platforms, chests, the placeholder) against the room's openings (portal
faces of the exported, installed blv) and the walking lines between them (segments between the openings' centres in
each room). Prints each prop's gap to the nearest opening and to the nearest walking line, flagged under the
clearances (CLEAR_OPEN to an opening's middle, CLEAR_LINE to a line). python3 props_check.py <export.json>"""
import json, math, sys
from pathlib import Path
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen
CLEAR_OPEN, CLEAR_LINE = 256, 96
d = json.load(open(sys.argv[1]))['map']
lock = yaml.safe_load((gen.B / 'L4' / 'ids.lock.yml').read_text())['sectors']
V = d['vertices']
ports = {}
for f in d['faces']:
    if not f['is_portal']:
        continue
    p = [V[i] for i in f['vertices']]
    xs = [v[0] for v in p]; ys = [v[1] for v in p]
    c = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    half = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
    for s in (f['room'], f['room_behind']):
        ports.setdefault(s, []).append((c, half))
def seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)
props = []
for r in gen.rooms:
    for p in r.get('platforms', []):
        props.append((r['id'], p.get('id', 'platform(%d,%d)' % tuple(p['at'])), p['at'], max(p['size']) / 2))
for x in gen.objects['decorations']:
    if 'wall' not in x:
        props.append((x['room'], x['id'] + ' ' + x['decoration'], x['at'], 48))
for x in gen.objects['chests']:
    props.append((x['room'], x['id'], x['at'], max(x.get('size', [96, 96])[:2]) / 2))
for x in gen.objects.get('placeholders', []):
    props.append((x['room'], x['id'], x['at'], max(x['size'][:2]) / 2))
start = gen.objects['start']
bad = 0
for room, name, at, r in props:
    s = lock[room]
    ps = ports.get(s, [])
    # openings of a room merge per centre (a doorway is two portal faces at most)
    cs = []
    for c, h in ps:
        if all(math.hypot(c[0] - k[0][0], c[1] - k[0][1]) > 8 for k in cs):
            cs.append((c, h))
    if room == start.get('room'):
        cs.append(((start['at'][0], start['at'][1]), 0))
    go = min((math.hypot(at[0] - c[0], at[1] - c[1]) - h - r for c, h in cs), default=1e9)
    gl = min((seg(at, a[0], b[0]) - r for i, a in enumerate(cs) for b in cs[i + 1:]), default=1e9)
    flag = go < CLEAR_OPEN or gl < CLEAR_LINE
    bad += flag
    print('%-3s %-18s %-40s at %-14s opening %6.0f line %6.0f' % ('!!' if flag else '', room, name, at, go, gl))
print('flagged', bad, 'of', len(props))
