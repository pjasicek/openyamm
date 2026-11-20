#!/usr/bin/env python3
"""How MM6/MM7/MM8 BLVs build the things the party uses (levers, buttons, switches, lifts, consoles).

Joins each clickable face (data/sectors.json) with its exported event (events/maps/<map>.lua: hint title and the
evt.* calls it makes) and with the scene's door records (is the clicked face itself part of a moving door?).
Also lists decorations that carry an event. Writes data/mechanisms.json and prints a summary.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1] / 'data'
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file  # noqa: E402

MECH = re.compile(r'lever|switch|button|wheel|valve|crank|lift|elevator|panel|console|control|pump|gear', re.I)
EVENT = re.compile(r'RegisterEvent\((\d+), "([^"]*)", function\(\)(.*?)\nend', re.S)


def events(world, stem):
    path = ROOT / 'assets_dev/worlds' / world / 'events/maps' / (stem + '.lua')
    if not path.exists():
        return {}
    out = {}
    for m in EVENT.finditer(path.read_text(errors='replace')):
        body = m.group(3)
        out[int(m.group(1))] = dict(hint=m.group(2), ops=Counter(re.findall(r'evt\.(\w+)', body)),
                                    textures=re.findall(r'evt\.SetTexture\(\d+, "([^"]+)"', body))
    return out


def door_faces(world, stem):
    path = ROOT / 'assets_dev/worlds' / world / 'maps' / (stem + '.scene.yml')
    scene = yaml.load(path.read_text(), Loader=yaml.CSafeLoader)
    faces = {}
    for d in (scene.get('initial_state') or {}).get('doors') or []:
        for f in d.get('face_ids') or []:
            faces[f] = d['door_id']
    return faces


def main():
    sectors = json.loads((OUT / 'sectors.json').read_text())
    by_map = defaultdict(list)
    for r in sectors:
        by_map[(r['world'], r['map'])].append(r)
    records, deco_records = [], []
    for (world, name), rows in sorted(by_map.items()):
        stem = name[:-4]
        evs = events(world, stem)
        doors = door_faces(world, stem)
        for r in rows:
            for c in r['clickable']:
                ev = evs.get(c['event'], dict(hint='', ops=Counter(), textures=[]))
                if not MECH.search(ev['hint']):
                    continue
                records.append(dict(world=world, map=name, sector=r['sector'], face=c['face'], event=c['event'],
                                    hint=ev['hint'], texture=c['texture'], area=c['area'], centre=c['centre'],
                                    face_moves=c['face'] in doors, ops=dict(ev['ops']),
                                    swaps_to=ev['textures']))
        p = parse_blv_file(ROOT / 'assets_dev/worlds' / world / 'maps' / name)['payload']
        for e in p['entities']:
            eid = e['event_id_secondary'] or e['event_id_primary']
            if eid:
                ev = evs.get(eid, dict(hint='', ops=Counter(), textures=[]))
                deco_records.append(dict(world=world, map=name, name=e['name'], event=eid, hint=ev['hint'],
                                         ops=dict(ev['ops'])))
    (OUT / 'mechanisms.json').write_text(json.dumps(dict(faces=records, decorations=deco_records), indent=1))
    for world in ('mm6', 'mm7', 'mm8'):
        rs = [r for r in records if r['world'] == world]
        print(f'== {world}: {len(rs)} mechanism faces, {sum(r["face_moves"] for r in rs)} of them part of a door')
        print('  hints   ', Counter(r['hint'] for r in rs).most_common(8))
        print('  textures', Counter(r['texture'] for r in rs).most_common(14))
        print('  swap to ', Counter(t for r in rs for t in r['swaps_to']).most_common(10))
        print('  ops     ', sum((Counter(r['ops']) for r in rs), Counter()).most_common(8))
        print('  area med', sorted(r['area'] for r in rs)[len(rs) // 2] if rs else None)
        ds = [d for d in deco_records if d['world'] == world]
        print('  decorations with events', Counter((d['name'], d['hint']) for d in ds).most_common(12))


if __name__ == '__main__':
    main()
