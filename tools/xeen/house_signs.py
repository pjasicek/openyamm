#!/usr/bin/env python3
"""The sign a Xeen town house hangs by its door, by the house's kind (lane A4; TOWNS_FORMAT.md section 5).

    python3 -I tools/xeen/house_signs.py      # every built town map's house signs against their kinds; exit 1 on an error

MM6-MM8 give each kind of service one picture board, the same in every town (measured on the shipped outdoor maps,
2026-11-22): the Adventurer's Inn the key and heart (`sginn`: MM8 Ravenshore and Dagger Wound, MM7 Tatalia, MM6),
a tavern the mug (`7sgtvrn` MM7, `sgtvrn` MM8), the bank the coins, training the target, stables the horse, the
weaponsmith the crossed blades, the armourer the helm or gauntlet, the magic shop the wizard's hat or staves, the
alchemist the flask, a guild its school's sign (MM7) or the spell sign (`sgspell`, MM8's sign for every guild), a
temple the caduceus (MM7; MM8's temples have none), a dock the anchor board. A town hall has none.

Xeen's own boards (Sandcaster's lettered signs, the Crossroads stalls, Castleview's jail and Public Storage) count
for their kind. The town generators of the map lanes pass these names to their kits; this table is what they must
match. `towns.py` runs the check below on every built town map: a house whose sign is not of its kind is an error,
a service of a signed kind hanging none is a warning.
"""

import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
BRIEFS = REPO / 'devdocs' / 'xeen' / 'briefs'
TOWNS = REPO / 'assets_dev' / 'worlds' / 'xeen' / 'source' / 'towns'

GUILD_SIGNS = {'fire': 'sgfire', 'air': 'sgair', 'water': 'sgwater', 'earth': 'sgearth', 'spirit': 'sgspirit',
               'mind': 'sgmind', 'body': 'sgbody', 'light': 'sglight', 'dark': 'sgdark'}

# kind -> the boards it may hang: MM7's, MM8's, then Xeen's own of that kind (source/textures.yml `kind: sign`)
SIGNS = {
    'inn': {'sginn'},
    'tavern': {'7sgtvrn', 'sgtvrn', 'xstavern', 'xsstfood'},
    'weapon_shop': {'sgweapon', 'sgweap', 'xsweapons'},
    'armor_shop': {'7sgarm', 'sgarm', 'xsarmour', 'xsstrobes', 'xsstbelts', 'xsstboots'},
    'magic_shop': {'sgmagi', 'sgmagic', 'xsmagic', 'xsstneck'},
    'alchemist': {'7sgalch', 'sgalch', 'xspotions'},
    'bank': {'7sgbank', 'sgbank'},
    'training': {'7sgtrain', 'sgtrain', 'xstraining'},
    'stables': {'7sgstabl', 'sgstabl', 'xscaravan'},
    'boats': {'sgdock'},
    'temple': {'sgtempl', 'xstemple'},
    **{f'{school}_guild': {sign, 'sgspell'} for school, sign in GUILD_SIGNS.items()},
    # no sign in MM6-MM8; a residence only a named board of its own (Caleb's stall, the jail, Public Storage)
    'town_hall': set(),
    'throne': set(),
    'residence': {'xscaleb', 'xljail', 'xlstorage'},
}
# kinds whose missing sign is only a note: MM8's temples hang none
UNSIGNED_OK = {'temple', 'town_hall', 'throne', 'residence', 'mirror'}


def sketch_houses(sketch):
    """(door id, house id, [sign textures]) for each building of an L4 sketch that opens a house."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            if 'house' in node and isinstance(node.get('parts'), list):
                name = node.get('building') or node.get('id')
                if node.get('index') is not None:
                    name = f'{name}#{node["index"]}'
                signs = [s.get('texture') for p in node['parts'] for s in (p.get('signs') or [])]
                found.append((name, node['house'], signs))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(sketch)
    return found


def sign_problems(key, sketch, houses):
    """(errors, warnings) for one map: `houses` maps a house id to its town-file entry."""
    errors, warnings = [], []
    for door, house_id, signs in sketch_houses(sketch):
        house = houses.get(house_id)
        if house is None:
            continue    # towns.py reports a door without a house
        kind = house['kind']
        allowed = SIGNS.get(kind)
        if allowed is None:
            errors.append(f'{key}: house {house_id} {house["name"]} ({door}): kind {kind} has no sign rule '
                          '(tools/xeen/house_signs.py SIGNS)')
            continue
        for sign in signs:
            if sign not in allowed:
                want = ', '.join(sorted(allowed)) or 'none'
                errors.append(f'{key}: house {house_id} {house["name"]} ({door}, {kind}) hangs {sign}; '
                              f'its kind hangs {want}')
        if not signs and allowed and kind not in UNSIGNED_OK:
            warnings.append(f'{key}: house {house_id} {house["name"]} ({door}, {kind}) hangs no sign '
                            f'({", ".join(sorted(allowed))})')
    return errors, warnings


def check_all():
    """Every town file whose map has an L4 sketch: (errors, warnings)."""
    errors, warnings = [], []
    for path in sorted(TOWNS.glob('*.yml')):
        town = yaml.safe_load(path.read_text())
        if not isinstance(town, dict) or not town.get('houses'):
            continue
        sketch_path = BRIEFS / town['key'].lower().replace('-', '') / 'L4' / 'sketch.yml'
        if not sketch_path.exists():
            continue
        houses = {h['id']: h for h in town['houses']}
        e, w = sign_problems(town['key'], yaml.safe_load(sketch_path.read_text()), houses)
        errors += e
        warnings += w
    return errors, warnings


def main():
    errors, warnings = check_all()
    for line in warnings:
        print(f'  WARN  {line}')
    for line in errors:
        print(f'  ERROR {line}')
    print(f'house signs: {len(errors)} errors, {len(warnings)} warnings')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
