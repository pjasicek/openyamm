#!/usr/bin/env python3
"""Exit look check (F12, the user 2026-11-21): every way out of a Xeen dungeon looks like MM7's and MM8's, a black face
(7solid01) in its doorway, not a daylight picture or a door that turns out to lead outside.

  tools/xeen/check_exits.py [<key>...]      (keys as in devdocs/xeen/briefs/<key>/, default every L4 project)

Errors:
- `exits.not_black`: an `exits:` object of objects.yml whose surface is not 7solid01.
- `exits.door_leaf`: a door whose click leaves the map (its wiring event has an `exit` effect) with a front picture
  that is not 7solid01 (a shut door that is really an exit; the gated doors that throw the party out on a failed
  check are listed in SPECIAL until their design is settled).
SPECIAL lists the exits kept on purpose (ladders, grates, water, sky and cloud ways, a throne): one line of reason
each; add a line there, never a texture to the rule. Exit 1 on an error.
"""
import glob
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRIEFS = os.path.join(ROOT, 'devdocs', 'xeen', 'briefs')
BLACK = '7solid01'
SPECIAL = {
    ('dd01', 'exit:hatch'): 'a ladder up through the hatch (MM6 d1ladder exits)',
    ('dd18', 'exit:shaft'): 'a ladder up the shaft',
    ('dd20', 'exit:shaft'): 'a ladder up the jetty shaft',
    ('dd01', 'exit:outfall'): 'the outfall grate the sewer drains through',
    ('dd26', 'exit:grate'): 'the iron grate at the stair head',
    ('xd01', 'exit:river'): 'the river itself (water you swim out by)',
    ('xd04', 'exit:cloud_stair'): 'the stair of cloud to the sky (X8)',
    ('p1', 'exit:way_up'): "the crater's way up on the Plane of Fire",
}


def load(path):
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def front_textures(door):
    out = []
    if door.get('surface'):
        out.append(door['surface'].get('texture'))
    for row in door.get('pictures') or []:
        for picture in row:
            out.append(picture.get('texture'))
    return out


def check(key):
    errors = []
    l4 = os.path.join(BRIEFS, key, 'L4')
    objects = load(os.path.join(l4, 'objects.yml'))
    wiring = load(os.path.join(l4, 'wiring.yml'))
    for ex in objects.get('exits') or []:
        texture = (ex.get('surface') or {}).get('texture')
        if texture != BLACK and (key, ex['id']) not in SPECIAL:
            errors.append(f'error exits.not_black: {key} {ex["id"]} shows {texture}, not the black exit face {BLACK}')
    leaving = set()
    for event in wiring.get('events') or []:
        source = str(event.get('source', ''))
        if source.startswith('door:') and any(isinstance(e, dict) and ('exit' in e or 'leave' in e)
                                              for e in (event.get('effects') or []) + (event.get('else_effects') or [])):
            leaving.add(source)
    for door in objects.get('doors') or []:
        if door.get('id') in leaving and (key, door['id']) not in SPECIAL:
            bad = [t for t in front_textures(door) if t != BLACK]
            if bad:
                errors.append(f'error exits.door_leaf: {key} {door["id"]} leads out of the map but shows {bad}')
    return errors


def main():
    keys = sys.argv[1:] or sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(f'{BRIEFS}/*/L4'))
    errors = [e for key in keys for e in check(key)]
    for e in errors:
        print(e)
    print(f'{len(keys)} projects, {len(errors)} errors; {len(SPECIAL)} special exits kept')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
