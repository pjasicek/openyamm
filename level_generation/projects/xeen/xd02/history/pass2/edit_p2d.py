#!/usr/bin/env python3
"""XD-02 second pass, step 4 (after edit_p2c.py): ore carts that read as carts (a flared iron tub on a timber chassis
over four wheels, at the generated cart side's own 2:1 shape; the tipped ones lying on a side with that side up and
their wheels out of the bottom), the flatcars' side boards in iron at its size, the trestle's caps and ties between
its legs, the hoist cage's posts proud of its rails, the Deep Line's exit face the whole end wall. Run once."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import math
import sys

sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd02/pass2')
import yio

L = _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4/'
R = yio.load(L + 'rooms.yml')
O = yio.load(L + 'objects.yml')

TIMBER = {'texture': 't3d2abe', 'size': [256, 32]}
IRON = {'texture': 'xnrustirn', 'size': [64, 64]}
SIDE = {'texture': 'xncartsd', 'size': [128, 64], 'fit': True}
ORE = {'texture': 'crdrf1', 'size': [128, 128]}


def room(rid):
    return next(r for r in R['rooms'] if r['id'] == rid)


def obj(col, oid):
    return next(o for o in O[col] if o['id'] == oid)


def at(cx, cy, ang, along, across):
    a = math.radians(ang)
    return [round(cx + math.cos(a) * along - math.sin(a) * across, 1),
            round(cy + math.sin(a) * along + math.cos(a) * across, 1)]


def standing_cart(cx, cy, ang, note, base=0, on_blocks=False, wheels=4):
    """Tub 176 by 104 at its foot, flaring to 200 by 128 at its rim, 88 deep, on a chassis 24 high; wheels 36 across
    and 10 thick just outside the tub's foot."""
    parts = []
    if on_blocks:
        for s in (-1, 1):
            parts.append({'at': at(cx, cy, ang, s * 52, 0), 'size': [64, 96], 'facing': ang, 'rise': 24,
                          'surface': TIMBER, 'top_surface': TIMBER, 'base': base, 'notes': 'A block under the cart'})
    else:
        parts.append({'at': [cx, cy], 'size': [160, 80], 'facing': ang, 'rise': 24, 'surface': TIMBER,
                      'top_surface': TIMBER, 'base': base, 'notes': "The cart's chassis"})
    parts.append({'at': [cx, cy], 'size': [176, 104], 'top_size': [200, 128], 'facing': ang, 'rise': 88,
                  'base': base + 24, 'surface': SIDE, 'end_surface': IRON, 'top_surface': ORE, 'notes': note})
    spots = [(-60, -58), (60, -58), (-60, 58), (60, 58)][:wheels]
    for along, across in spots:
        parts.append({'at': at(cx, cy, ang, along, across), 'size': [36, 10], 'facing': ang, 'rise': 36,
                      'surface': IRON, 'top_surface': IRON, 'base': base, 'notes': 'Cart wheel'})
    return parts


def tipped_cart(cx, cy, ang, note, bottom_side):
    """A cart lying on its long side: that side (176 by 88, the generated cart side) is its top, its bottom faces
    `bottom_side` (+1 or -1 across), its wheels stand out of the bottom, ore spills from its mouth."""
    parts = [{'at': [cx, cy], 'size': [176, 88], 'facing': ang, 'rise': 104, 'surface': IRON, 'top_surface': SIDE,
              'notes': note}]
    for along in (-60, 60):
        for up in (0, 52):
            parts.append({'at': at(cx, cy, ang, along, bottom_side * 47), 'size': [36, 10], 'facing': ang,
                          'rise': 36, 'base': up, 'surface': IRON, 'top_surface': IRON, 'notes': 'Cart wheel'})
    mouth = at(cx, cy, ang, 0, -bottom_side * 84)
    parts.append({'at': mouth, 'size': [168, 80], 'facing': ang, 'rise': 0, 'surface': ORE, 'top_surface': ORE,
                  'top_heights': [2, 2, 20, 20] if bottom_side > 0 else [20, 20, 2, 2], 'notes': 'Ore spilled from the cart'})
    return parts


def is_old_cart_part(p):
    tex = p.get('surface', {}).get('texture')
    if tex == 'xncartsd':
        return True
    return tex == 'xnrustirn' and p.get('rise') in (30, 48) and 'outline' in p


def replace_carts(rid, new_parts):
    r = room(rid)
    first = next(i for i, p in enumerate(r['platforms']) if is_old_cart_part(p))
    r['platforms'] = [p for p in r['platforms'] if not is_old_cart_part(p)]
    r['platforms'][first:first] = new_parts


# the wheel blocks (a wheel 36 across and 10 thick, standing just outside the tub's foot) stand at height 0..36
replace_carts('room:stope_floor',
              standing_cart(6050, 3400, 30, 'An abandoned ore cart, full of ore.')
              + tipped_cart(5720, 3000, -69.9, 'An abandoned cart on its side.', 1))
replace_carts('room:repair_niche',
              standing_cart(5420, 5560, 0, 'A cart up on blocks, one wheel off.', on_blocks=True, wheels=3))
replace_carts('room:deep_station', standing_cart(4060, 4448, 0, 'The Deep Line cart, chained to its brake.'))
replace_carts('room:adit_mouth', tipped_cart(13600, 3920, 0, 'An ore cart the clan tipped against the north wall.', 1))
replace_carts('room:west_line', tipped_cart(6200, 5184, 7.95, 'The derailed cart, on its side.', 1))

# the flatcars' low side boards: iron plates at their size, not the cart side stretched 8 to 1
for mid in ('mover:trestle_car', 'mover:east_cart'):
    for part in obj('movers', mid)['parts']:
        if part.get('surface', {}).get('texture') == 'xncartsd':
            part['surface'] = IRON

# the trestle: caps and ties span between the legs' inner faces (they crossed the legs' faces before)
ch = room('room:chasm')
for p in ch['platforms']:
    if p.get('notes') == 'Trestle leg':
        p['rise'] += 2
for b in ch['beams']:
    if b['path'][0][1] == 5048 and b['path'][1][1] == 5320:
        b['path'] = [[b['path'][0][0], 5092], [b['path'][1][0], 5276]]

# the hoist cage: corner posts a little thicker and taller than the rails between them
hoist = obj('movers', 'mover:hoist')
for part in hoist['parts'][:4]:
    xs = [q[0] for q in part['outline']]
    ys = [q[1] for q in part['outline']]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    part['outline'] = [[round(cx), round(cy - 13)], [round(cx + 13), round(cy)], [round(cx), round(cy + 13)],
                       [round(cx - 13), round(cy)]]
    part['height'] = 244

# the Deep Line: its exit face is the whole end wall of the cutting, and a lamp at its mouth shows the way on
ex = obj('exits', 'exit:deep')
ex['size'] = [320, 376]
O['decorations'].append({'id': 'deco:deep_mouth_121', 'room': 'room:deep_mouth', 'decoration': 'torch02', 'wall': 0,
                         'along': 0.25, 'height': 200})

yio.save(L + 'rooms.yml', R)
yio.save(L + 'objects.yml', O)
print('edited')
