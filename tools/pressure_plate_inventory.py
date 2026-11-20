#!/usr/bin/env python3
"""Inventory of a world's pressure plates: what each plate event does, and whether Levitate skips it
(the map script's levitateTrapEvents, written by tools/LegacyLuaExport.cpp isSimplePressureTrapEvent and
isAuditedMm6PressureTrap).

    python3 tools/pressure_plate_inventory.py [--world mm6] [--json out.json] [--all]

Categories, from the generated Lua of each event:
  pure_harm    spells, damage or summons only            safe for Levitate to skip
  penalty      harm plus map variables reset to 0        safe to skip (a reset is part of the trap)
  mixed        harm plus progress (doors, teleports, variables set, rewards)   review: skipping loses the progress
  no_harm      progress or messages only                 must not be skipped
  status_only  status text only
  missing      the face's event has no script            the original has none either (checked for MM6)
It prints the rows that need a look (mixed, and pure harm Levitate does not skip); --all prints every row.
A puzzle plate Levitate skips silently breaks its puzzle for a levitating party (Shadow Guild 22/23, 2026-11-04).
"""

import argparse
import collections
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from util.map_export import parse_blv_file, parse_odm_file  # noqa: E402

PRESSURE_PLATE = 0x04000000


def plate_faces(path):
    faces = collections.defaultdict(list)
    if path.suffix == '.blv':
        for face in parse_blv_file(path)['payload']['faces']:
            event = (face['face_param'] or {}).get('cog_triggered') or 0
            if event and face['attributes'] & PRESSURE_PLATE:
                faces[event].append(face['index'])
    else:
        for model in parse_odm_file(path)['payload']['bmodels']:
            for face in model['faces']:
                event = face.get('cog_triggered_number') or 0
                if event and face['attributes'] & PRESSURE_PLATE:
                    faces[event].append(f"{model['index']}:{face['index']}")
    return faces


def event_bodies(source):
    bodies = {}
    starts = [(m.start(), int(m.group(1))) for m in re.finditer(r'^RegisterEvent\((\d+),', source, re.M)]
    for index, (start, event) in enumerate(starts):
        bodies[event] = source[start:starts[index + 1][0] if index + 1 < len(starts) else len(source)]
    return bodies


def classify(body):
    ops = set()
    if 'evt.CastSpell' in body:
        ops.add('spell')
    if 'evt.DamagePlayer' in body:
        ops.add('damage')
    if 'evt.SummonMonsters' in body:
        ops.add('summon')
    for match in re.finditer(r'SetValue\(MapVar\(\d+\), (-?\d+)\)', body):
        ops.add('reset' if match.group(1) == '0' else 'progress_var')
    if re.search(r'(AddValue|SubtractValue)\(MapVar', body):
        ops.add('progress_var')
    for name, pattern in (('door', 'evt.SetDoorState'), ('move', 'evt.MoveToMap'), ('texture', 'evt.SetTexture'),
                          ('chest', 'evt.OpenChest')):
        if pattern in body:
            ops.add(name)
    if re.search(r'evt\.(GiveItem|SetQBit|ClearQBit)|SetValue\(QBit|AddValue\((Gold|Food|Experience)', body):
        ops.add('reward')
    if re.search(r'(SetValue|AddValue|SubtractValue)\((?!MapVar)\w+', body):
        ops.add('party_value')
    if re.search(r'evt\.(SimpleMessage|SpeakNPC|EnterHouse)', body):
        ops.add('message')
    if re.search(r'evt\.(SetFacetBit|SetSprite|SetLight)', body):
        ops.add('world_change')
    harm = ops & {'spell', 'damage', 'summon'}
    progress = ops - {'spell', 'damage', 'summon', 'reset'}
    if harm and not progress:
        category = 'penalty' if 'reset' in ops else 'pure_harm'
    elif harm:
        category = 'mixed'
    elif ops:
        category = 'no_harm'
    else:
        category = 'status_only'
    return category, sorted(ops)


def inventory(world):
    events_dir = REPO / 'assets_dev' / 'worlds' / world / 'events' / 'maps'
    maps_dir = REPO / 'assets_dev' / 'worlds' / world / 'maps'
    rows = []
    for path in sorted(list(maps_dir.glob('*.blv')) + list(maps_dir.glob('*.odm'))):
        faces = plate_faces(path)
        if not faces:
            continue
        lua = events_dir / f'{path.stem}.lua'
        source = lua.read_text(errors='replace') if lua.exists() else ''
        match = re.search(r'levitateTrapEvents = \{([^}]*)\}', source)
        skipped = {int(x) for x in match.group(1).split(',')} if match else set()
        bodies = event_bodies(source)
        for event, face_list in sorted(faces.items()):
            body = bodies.get(event, '')
            category, ops = classify(body) if body else ('missing', [])
            title = re.match(r'RegisterEvent\(\d+, (nil|"[^"]*")', body)
            rows.append(dict(map=path.name, event=event, faces=len(face_list),
                             title=title.group(1).strip('"') if title and title.group(1) != 'nil' else '',
                             category=category, ops=ops, levitate_skips=event in skipped))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--world', default='mm6')
    parser.add_argument('--json', type=Path)
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()
    rows = inventory(args.world)
    print(f"{len({r['map'] for r in rows})} maps, {len(rows)} plate events, {sum(r['faces'] for r in rows)} faces")
    for (category, skips), count in sorted(collections.Counter((r['category'], r['levitate_skips']) for r in rows).items()):
        print(f'  {category:12} {"skipped by Levitate" if skips else "fires when levitating":22} {count}')
    print()
    for r in rows:
        if args.all or r['category'] == 'mixed' or (r['category'] == 'pure_harm' and not r['levitate_skips']):
            print(f"{r['map']:12} {r['event']:4} {r['category']:11} {'skip' if r['levitate_skips'] else '    '} "
                  f"{r['title']!r:22} {r['ops']}")
    if args.json:
        args.json.write_text(json.dumps(rows, indent=1))


if __name__ == '__main__':
    main()
