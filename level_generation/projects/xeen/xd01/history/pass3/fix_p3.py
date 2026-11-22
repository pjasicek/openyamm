#!/usr/bin/env python3
"""Pass 3, step 4: faces in one plane the build found (tank posts against tank bodies, the store's crossing joists,
the hall's posts against its tie beams, the dock's hoist arm against its beam)."""
import sys, yio
L = sys.argv[1]
rooms = yio.load(f'{L}/rooms.yml')
R = {r['id']: r for r in rooms['rooms']}
for p in R['room:breeding_pens']['platforms']:
    tid = p.get('id', '')
    if tid.startswith('platform:tank_'):
        cracked = p['rise'] == 42
        p['base'] = 136; p['rise'] = 40 if cracked else 54
    elif p.get('base') == 134 and p['surface']['texture'] == 'd8dorf':
        p['rise'] = 46 if p['rise'] == 42 else 58
for p in R['room:grain_hall']['platforms']:
    if p.get('rise') == 592: p['rise'] = 576
for b in R['room:feed_store']['beams']:
    if b['path'][0][0] == b['path'][1][0]: b['bottom'] = 104
for b in R['room:loading_dock']['beams']:
    if b['path'] == [[1088, -768], [1088, -576]]: b['bottom'] = 472
yio.save(f'{L}/rooms.yml', rooms)
