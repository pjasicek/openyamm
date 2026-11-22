#!/usr/bin/env python3
"""XD-02 second pass, step 12: every cart stands on its wheels (a box on its side read as a crate in the game, even
with ore spilled from it): the three tipped carts become carts left askew off the rails; wheels 44 across that show
under the tub's flaring rim; the brake wheel gets four iron handles on its rim. Run once."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import math, sys
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd02/pass2')
import yio
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4/'
R = yio.load(L + 'rooms.yml')
TIMBER = {'texture': 't3d2abe', 'size': [256, 32]}
IRON = {'texture': 'xnrustirn', 'size': [64, 64]}
SIDE = {'texture': 'xncartsd', 'size': [128, 64], 'fit': True}
ORE = {'texture': 'crdrf1', 'size': [128, 128]}
DARK = {'texture': 'd2ceil4', 'size': [256, 256]}
A3 = round(math.degrees(math.atan2(3, 4)), 4)   # 36.8699: corners of 200 by 120 and 180 by 100 fall on whole units
A4 = round(math.degrees(math.atan2(4, 3)), 4)   # 53.1301


def at(cx, cy, ang, along, across):
    a = math.radians(ang)
    return [round(cx + math.cos(a) * along - math.sin(a) * across, 1),
            round(cy + math.sin(a) * along + math.cos(a) * across, 1)]


def cart(cx, cy, ang, note, on_blocks=False, wheels=4, load=ORE):
    parts = []
    if on_blocks:
        for s in (-1, 1):
            parts.append({'at': at(cx, cy, ang, s * 52, 0), 'size': [64, 96], 'facing': ang, 'rise': 24,
                          'surface': TIMBER, 'top_surface': TIMBER, 'notes': 'A block under the cart'})
    else:
        parts.append({'at': [cx, cy], 'size': [160, 80], 'facing': ang, 'rise': 24, 'surface': TIMBER,
                      'top_surface': TIMBER, 'notes': "The cart's chassis"})
    parts.append({'at': [cx, cy], 'size': [180, 100], 'top_size': [200, 120], 'facing': ang, 'rise': 88, 'base': 24,
                  'surface': SIDE, 'end_surface': IRON, 'top_surface': load, 'notes': note})
    for along, across in [(-60, -56), (60, -56), (-60, 56), (60, 56)][:wheels]:
        parts.append({'at': at(cx, cy, ang, along, across), 'size': [44, 12], 'facing': ang, 'rise': 44,
                      'surface': IRON, 'top_surface': IRON, 'notes': 'Cart wheel'})
    return parts


CART_NOTES = ('Cart wheel', 'Ore spilled from the cart', "The cart's chassis", 'A block under the cart')
PLACES = {
    'room:stope_floor': [(6050, 3400, A3, 'An abandoned ore cart, full of ore.', {}),
                         (5720, 3000, -A4, 'An abandoned ore cart, empty.', {'load': DARK})],
    'room:repair_niche': [(5420, 5560, 0, 'A cart up on blocks, one wheel off.', {'on_blocks': True, 'wheels': 3,
                                                                               'load': DARK})],
    'room:deep_station': [(4060, 4448, 0, 'The Deep Line cart, chained to its brake.', {})],
    'room:adit_mouth': [(13600, 3900, 0, 'An ore cart the clan pushed off the rails against the north wall.',
                         {'load': DARK})],
    'room:west_line': [(6200, 5184, A3, 'The derailed cart, standing askew across the line.', {'load': DARK})],
}
for r in R['rooms']:
    if r['id'] not in PLACES:
        continue
    plats = r['platforms']
    cartish = [i for i, p in enumerate(plats) if p.get('notes') in CART_NOTES or
               p.get('surface', {}).get('texture') == 'xncartsd' or p.get('top_surface', {}).get('texture') == 'xncartsd']
    first = cartish[0]
    r['platforms'] = [p for i, p in enumerate(plats) if i not in cartish]
    new = []
    for cx, cy, ang, note, kw in PLACES[r['id']]:
        new += cart(cx, cy, ang, note, **kw)
    r['platforms'][first:first] = new
    if r['id'] == 'room:deep_station':
        for k in range(4):
            a = math.radians(45 + 90 * k)
            r['platforms'].append({'at': [round(4239 + 26 * math.cos(a)), round(4856 + 26 * math.sin(a))],
                                   'size': [8, 8], 'base': 106, 'rise': 16, 'surface': IRON, 'top_surface': IRON,
                                   'notes': "A handle on the brake wheel's rim"})
yio.save(L + 'rooms.yml', R)
print('edited')
