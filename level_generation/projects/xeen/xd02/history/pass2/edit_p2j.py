#!/usr/bin/env python3
"""XD-02 second pass, step 10: a mined vein says so without its gold coming back (a condition with `locked_text` and
no `else_effects`: the switch then keeps its mined picture); the brake a hand wheel on a post (a clicked block, so it
has no handle to spring back), its chain running from the cart to it; the winch a capstan (an eight-sided drum with
its bars), not a box; the points lever a switch whose handle is down while the east line is live. Run once."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import math, sys
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd02/pass2')
import yio
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4/'
R = yio.load(L + 'rooms.yml'); O = yio.load(L + 'objects.yml'); W = yio.load(L + 'wiring.yml')
room = lambda rid: next(r for r in R['rooms'] if r['id'] == rid)
obj = lambda col, oid: next(o for o in O[col] if o['id'] == oid)
evt = lambda eid: next(e for e in W['events'] if e['id'] == eid)
TIMBER = {'texture': 't3d2abe', 'size': [256, 32]}
POST = {'texture': 't3d2abs', 'size': [32, 256]}
IRON = {'texture': 'xnrustirn', 'size': [64, 64]}
PLANK = {'texture': 'd2ceil2', 'size': [256, 256]}


def octagon(cx, cy, r):
    return [[round(cx + r * math.cos(math.radians(22.5 + 45 * k))), round(cy + r * math.sin(math.radians(22.5 + 45 * k)))]
            for k in range(8)]


for name in ('sorting', 'flooded', 'rim', 'se', 'sw', 'rich'):
    e = evt(f'evt:vein_{name}')
    e.pop('else_effects', None)
    e['locked_text'] = 'Only bare rock is left where the seam was.'

# the brake: a hand wheel lying on a post by the north wall, the chain from the cart's end to it
O['switches'] = [s for s in O['switches'] if s['id'] != 'switch:brake']
ds = room('room:deep_station')
ds['platforms'] += [
    {'at': [4239, 4856], 'size': [24, 24], 'rise': 96, 'surface': POST, 'top_surface': POST,
     'notes': "The brake's post"},
    {'id': 'platform:brake_wheel', 'outline': octagon(4239, 4856, 40), 'base': 96, 'rise': 10, 'surface': IRON,
     'top_surface': IRON, 'notes': "The Deep Line's brake: an iron hand wheel on its post (clicked), the chain padlocked to it."},
]
ch = obj('movers', 'mover:chain')
for k in ('at', 'size'):
    ch.pop(k)
ax, ay, bx, by = 4150, 4448, 4239, 4844
ln = math.hypot(bx - ax, by - ay)
px, py = -(by - ay) / ln * 4, (bx - ax) / ln * 4
ch['outline'] = [[round(ax - px), round(ay - py)], [round(bx - px), round(by - py)], [round(bx + px), round(by + py)],
                 [round(ax + px), round(ay + py)]]
ch['bottom'] = 36
ch['height'] = 8
ch['notes'] = "The chain from the cart's end to the brake wheel: it drops into the rail bed when the brake key is used."
e = evt('evt:brake')
e['source'] = 'platform:brake_wheel'
e['title'] = 'Brake wheel'
e['else_effects'][0]['lua'] = e['else_effects'][0]['lua'].replace('brake lever', 'brake wheel')
evt('evt:exit_deep')['locked_text'] = 'The Deep Line cart is chained to its brake wheel.'

# the winch: a capstan in front of the fall
ca = room('room:collapsed_adit')
ca['platforms'] = [p for p in ca['platforms'] if p.get('id') != 'platform:winch' and p.get('notes') != 'Winch frame']
ca['platforms'] += [
    {'id': 'platform:winch', 'outline': octagon(2920, 5300, 56), 'rise': 80, 'surface': TIMBER, 'top_surface': PLANK,
     'notes': "The winch: a capstan drum of dark timber, its rope made fast round the fall's props (clicked)."},
    {'outline': octagon(2920, 5300, 32), 'base': 80, 'rise': 28, 'surface': IRON, 'top_surface': IRON,
     'notes': "The capstan's iron head"},
]
ca.setdefault('beams', []).extend([
    {'path': [[2830, 5300], [3010, 5300]], 'width': 12, 'depth': 12, 'bottom': 336, 'surface': TIMBER,
     'notes': "Capstan bar"},
    {'path': [[2920, 5210], [2920, 5390]], 'width': 12, 'depth': 12, 'bottom': 336, 'surface': TIMBER,
     'notes': "Capstan bar"},
])
ca['notes'] = ca['notes'].replace('the winch on its frame', 'the winch (a capstan)')

# the points lever: a switch, its handle down while the east line is live
e = evt('evt:points')
e['preset'] = 'switch'
e['condition'] = {'not': {'map_var': 'turntable_east'}}
e['effects'] = [{'set': {'var': {'map_var': 'turntable_east'}, 'value': 1}}, {'lights_on': 'light:signal_east'},
                {'lights_off': 'light:signal_trestle'}]
e['else_effects'] = [{'set': {'var': {'map_var': 'turntable_east'}, 'value': 0}}, {'lights_on': 'light:signal_trestle'},
                     {'lights_off': 'light:signal_east'},
                     {'text': 'The turntable grinds round: the trestle line is live.'}]
e['text'] = 'The turntable grinds round: the east line is live.'
e['notes'] = ("set:turntable: toggles turntable_east (the trestle by default); the lever's handle is down while the "
              "east line is live, and the green lamps show which line is.")
yio.save(L + 'rooms.yml', R); yio.save(L + 'objects.yml', O); yio.save(L + 'wiring.yml', W)
print('edited')
