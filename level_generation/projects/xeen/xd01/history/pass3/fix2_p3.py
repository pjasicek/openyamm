#!/usr/bin/env python3
"""Pass 3, step 5, after the first look in the game: the office plaster one picture high again (its ceiling rose),
the desk a pedestal under an overhanging top, the bucket and candle standing on what holds them (a decoration's
height counts from the top of the platform under it), the north lantern off the cabinet, a bigger lever, the scroll
in view on the pair's bed."""
import sys, yio
L = sys.argv[1]
rooms = yio.load(f'{L}/rooms.yml'); objects = yio.load(f'{L}/objects.yml')
R = {r['id']: r for r in rooms['rooms']}
th = next(t for t in rooms['themes'] if t['id'] == 'theme:office')
th['wall']['scale'] = 1.75
th['notes'] = th['notes'].replace('384 at scale 1.5', '448 at scale 1.75')
o = R['room:joes_office']
desk = o['platforms'][0]
desk.update({'size': [200, 88], 'rise': 64})
desk['notes'] = "Joe's desk: a plain plank pedestal (d06's furniture wood) under an overhanging top, not a chest; papers on it (clicked: the bills)."
o['platforms'].insert(1, {'at': [-420, 760], 'size': [232, 120], 'rise': 8, 'base': 64, 'surface': {'texture': 't1books1', 'size': [128, 128]},
    'top_surface': {'texture': 't1books1', 'size': [128, 128]}, 'bottom_surface': {'texture': 't1books1', 'size': [128, 128]}, 'notes': "The desk's top, overhanging the pedestal by 16 all round."})
for d in objects['decorations']:
    if d['id'] == 'deco:office_bucket': d['height'] = 0; d['floor_height'] = 374
    if d['id'] == 'deco:office_candle': d['height'] = 0; d['floor_height'] = 136
    if d['id'] == 'deco:office_lantern_n': d['along'] = 0.35
for s in objects['switches']:
    if s['id'] == 'switch:feeding_time': s['size'] = [16, 64]; s['reach'] = 64
for i in objects['items']:
    if i['id'] == 'item:rival_scroll': i['at'] = [2150, 7350]
yio.save(f'{L}/rooms.yml', rooms); yio.save(f'{L}/objects.yml', objects)
