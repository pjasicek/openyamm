#!/usr/bin/env python3
"""Pass 3, step 1: move the grain hall and aisle north by 256 (the bay grows) and the whole cellar and culvert
by (+256, +512) (the aisle grows; the cellar stair comes out of its north wall at its middle). Pure translation:
every coordinate of every room of a group and of every object in such a room. Written to the project in place;
the project was copied to output/studio_cal/xd01/pass3_backup/ first."""
import sys, yio
L = sys.argv[1]
UP = {'room:grain_hall', 'room:hall_aisle'}
CELLAR = {'room:cellar_stair', 'room:cellar_landing', 'room:cellar_stair_lower', 'room:breeding_pens', 'room:feed_store',
          'room:joes_stash', 'room:mated_pair_pen', 'room:shipping_room', 'room:culvert', 'room:culvert_lower',
          'room:culvert_shaft', 'room:culvert_outfall', 'room:river_sill'} | {'room:pen_%d' % i for i in range(1, 7)}
def shift_of(room):
    if room in UP: return (0, 256)
    if room in CELLAR: return (256, 512)
    return (0, 0)
KEYS = {'outline', 'path', 'top_outline', 'floor_lines', 'floor_points', 'at', 'from', 'to', 'exit'}
def is_point(v):
    return isinstance(v, list) and len(v) in (2, 3) and all(isinstance(c, (int, float)) for c in v)
def move_points(v, d):
    if is_point(v):
        return [v[0] + d[0], v[1] + d[1]] + v[2:]
    if isinstance(v, list):
        return [move_points(x, d) for x in v]
    return v
count = 0
def walk(node, d):
    global count
    if isinstance(node, dict):
        for k in list(node):
            v = node[k]
            if k == 'section':
                continue
            if k in KEYS and isinstance(v, list):
                node[k] = move_points(v, d); count += 1
            elif isinstance(v, (dict, list)):
                walk(v, d)
    elif isinstance(node, list):
        for x in node:
            walk(x, d)
def load(n): return yio.load(f'{L}/{n}')
def save(n, d): yio.save(f'{L}/{n}', d)
rooms = load('rooms.yml')
for r in rooms['rooms']:
    walk(r, shift_of(r['id']))
save('rooms.yml', rooms)
objects = load('objects.yml')
for key, lst in objects.items():
    if not isinstance(lst, list): continue
    for o in lst:
        if isinstance(o, dict) and 'room' in o:
            walk(o, shift_of(o['room']))
walk(objects['start'], shift_of(objects['start']['room']))
save('objects.yml', objects)
wiring = load('wiring.yml')
for e in wiring['events']:
    for eff in e.get('effects', []) or []:
        if 'summon' in eff:
            eff['summon']['at'] = move_points(eff['summon']['at'], (256, 512)); count += 1
save('wiring.yml', wiring)
print('moved', count, 'coordinate fields')
