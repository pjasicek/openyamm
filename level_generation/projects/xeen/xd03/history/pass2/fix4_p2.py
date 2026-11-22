#!/usr/bin/env python3
"""Pass two, fix 4: after the first look in the game (a torch in the alcove's mouth, levers too small to read, gold
heaps that gave nothing, lamps whose wall grew, the gong's sound)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import sys
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd03/pass2')
import yio
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd03/L4/'
rooms = yio.load(L + 'rooms.yml'); objects = yio.load(L + 'objects.yml'); wiring = yio.load(L + 'wiring.yml')
D = {d['id']: d for d in objects['decorations']}
D['deco:barracks_torch_3'].pop('at'); D['deco:barracks_torch_3']['along'] = 0.742   # it hung in the alcove's mouth
D['deco:buffer_lamp']['along'] = 0.357
D['deco:ledge_lamp']['along'] = 0.4286
for s in objects['switches']:
    if s.get('kind') == 'lever':
        s['size'] = [12, 48]
        s['reach'] = 24 if s['id'] == 'switch:cage_call' else 56
# The hoard: no lying gold piles (a picked-up pile gives no gold); three heaps of coins (generated xncoins), each
# clicked once for its gold and then gone.
objects['items'] = [i for i in objects['items'] if not i['id'].startswith('item:hoard_gold_')]
coins = {'texture': 'xncoins', 'size': [128, 128]}
R = {r['id']: r for r in rooms['rooms']}
heaps = [('platform:gold_heap_1', [3130, 7160], [192, 128], [96, 56], 40, 150),
         ('platform:gold_heap_2', [2920, 6990], [160, 128], [72, 48], 32, 100),
         ('platform:gold_heap_3', [3420, 7010], [160, 112], [72, 40], 32, 100)]
R['room:king_hoard'].setdefault('platforms', [])
for pid, at, size, top, rise, gold in heaps:
    R['room:king_hoard']['platforms'].append({'id': pid, 'at': at, 'size': size, 'top_size': top, 'rise': rise,
                                              'surface': dict(coins), 'top_surface': dict(coins),
                                              'notes': 'A heap of the King\'s gold coins (clicked).'})
    n = pid.split('_')[-1]
    wiring['events'].append({'id': f'evt:gold_heap_{n}', 'preset': 'script', 'source': pid, 'title': 'Heap of gold',
                             'once': True,
                             'effects': [{'gold': gold}, {'hide': pid}, {'passable': pid}],
                             'text': f'You shovel the King\'s coins into your packs: {gold} gold.',
                             'notes': 'The hoard: a heap of coins, taken once.'})
objects['decorations'] += [
    {'id': 'deco:hoard_urn_1', 'room': 'room:king_hoard', 'decoration': 'tcurn', 'at': [2880, 7240]},
    {'id': 'deco:hoard_urn_2', 'room': 'room:king_hoard', 'decoration': 'urn', 'at': [3520, 7240]},
    {'id': 'deco:hoard_plates', 'room': 'room:king_hoard', 'decoration': 'dec39', 'at': [3260, 7060]},
]
for p in objects['placeholders']:
    if p['id'] == 'placeholder:gong_model':
        p['stands_for'] = ('A great bronze gong in a timber frame with a swing clip (built of eight slabs under one'
                           ' picture until a model exists)')
E = {e['id']: e for e in wiring['events']}
gong_sound = 'evt.PlaySound(42682, 4912, 3640)'
for e in wiring['events']:
    if e['id'].startswith('evt:gong') or e['id'] == 'evt:sentry_rings':
        for eff in e['effects']:
            if 'lua' in eff and 'CameraShake' in eff['lua']:
                eff['lua'] = 'evt.CameraShake(0.4, 0.8); ' + gong_sound
c = E['evt:crystal_wall']
c['effects'] = [{'lua': 'evt.PlaySound(42270, 96, 384)'}]
yio.save(L + 'rooms.yml', rooms); yio.save(L + 'objects.yml', objects); yio.save(L + 'wiring.yml', wiring)
