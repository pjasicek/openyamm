#!/usr/bin/env python3
"""Secret faces (FaceAttribute::IsSecret, 0x2) for BLV maps without authored ones (MM6): the faces a perceptive party
sees pulsing. See README.md for the method, the MM7 calibration and the review decisions.

    python3 tools/secret_faces/secret_faces.py calibrate           # score the rules against MM7's own flags
    python3 tools/secret_faces/secret_faces.py select [--json out]  # list the MM6 selection
    python3 tools/secret_faces/secret_faces.py apply [--check]      # write (or verify) the scene overrides

The selection has three parts:
- hidden doors: doors opened by clicking them, whose front looks like the wall around it (its texture is mostly a
  static-wall texture of the map and is on the static walls of its rooms), at least 128x128, with no hover text, "Wall"
  or "Flickering Torch";
- remote hidden walls: camouflaged doors opened only from elsewhere, by an unlabelled plate or face (a wall behind a
  visible lever is a puzzle the player sees), minus the reviewed exclusions;
- triggers: hand-reviewed bookcase-style objects and hidden switches.
apply ORs the bit into each scene's initial_state.face_attribute_overrides (written through a temp file and rename:
the scenes are hard-linked to mirrors).
"""

import argparse
import collections
import json
import os
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from util.map_export import parse_blv_file  # noqa: E402

SECRET = 0x2
CLICKABLE = 0x02000000
PRESSURE_PLATE = 0x04000000
MIN_FRONT_AREA = 16384          # 128x128: smaller fronts were hatches, blocks and trims in the review
MIN_WALL_SHARE = 0.7            # share of the texture's wall area that is on static (non-door) walls in the map
HIDDEN_DOOR_HINTS = {'', 'Wall', 'Flickering Torch'}
CONTROL_HINTS = {'Button', 'Lever', 'Switch', 'Drawer'}
VISIBLE_TRIGGER = re.compile(r'switch|lever|button|door|key|monolith|altar|lord|panel|lift|elevator|statue|chest', re.I)

# Remote hidden walls the screenshot review rejected (README.md, "Review decisions").
REMOTE_EXCLUDED = {
    ('cd2', 10): 'the water-tile barrier that clears once the way is open',
    ('6d07', 42): 'a large moving section of the hall, not a hidden wall',
    ('6d08', 2): 'the second leaf of an ordinary door pair',
}
# Hand-reviewed triggers: bookcase-style objects and unlabelled switches.
TRIGGERS = {
    'zdtl01': [159, 161],       # Dresser that slides aside
    'cd2': [4521, 4556],        # Signs ("The crimson embers will lead the way") opening hidden walls 11 and 13
    'pyramid': [2066],          # unlabelled patterned panel that teleports the party
}


def face_area(face, vertices):
    points = []
    for index in face['vertex_indices']:
        vertex = vertices[index]
        points.append((vertex['x'], vertex['y'], vertex['z']) if isinstance(vertex, dict) else tuple(vertex))
    sx = sy = sz = 0.0
    for a, b in zip(points, points[1:] + points[:1]):
        sx += a[1] * b[2] - a[2] * b[1]
        sy += a[2] * b[0] - a[0] * b[2]
        sz += a[0] * b[1] - a[1] * b[0]
    return 0.5 * (sx * sx + sy * sy + sz * sz) ** 0.5


def event_bodies(source):
    bodies = {}
    starts = [(m.start(), int(m.group(1))) for m in re.finditer(r'^RegisterEvent\((\d+),', source, re.M)]
    for index, (start, event) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(source)
        bodies[event] = source[start:end]
    return bodies


def event_hint(body):
    match = re.match(r'RegisterEvent\(\d+, (nil|"[^"]*")', body)
    return match.group(1).strip('"') if match and match.group(1) != 'nil' else ''


def map_features(world, path):
    """Clickable wall faces and doors of one map, with the features the rules use."""
    scene = path.with_suffix('.scene.yml')
    payload = parse_blv_file(path)['payload']
    faces, vertices = payload['faces'], payload['vertices']
    data = yaml.load(scene.read_text(), Loader=yaml.CSafeLoader)
    doors = (data.get('initial_state') or {}).get('doors') or []
    face_door = {}
    for door in doors:
        for index in door.get('face_ids') or []:
            face_door.setdefault(index, door['door_id'])
    areas = [face_area(face, vertices) for face in faces]

    def is_wall(face):
        return face['facet_type'] in (1, 2) and not face['is_portal']

    texture_area = collections.defaultdict(lambda: [0.0, 0.0])      # texture -> [static wall area, door face area]
    static_by_room = collections.defaultdict(collections.Counter)
    static_rooms = collections.defaultdict(set)
    for face in faces:
        if not is_wall(face):
            continue
        texture = face['texture_name'].lower()
        on_door = face['index'] in face_door
        texture_area[texture][1 if on_door else 0] += areas[face['index']]
        if not on_door:
            for room in (face['room_number'], face['room_behind_number']):
                static_by_room[room][texture] += 1
                static_rooms[texture].add(room)

    def wall_share(texture):
        static, door = texture_area[texture]
        return static / max(1.0, static + door)

    lua = REPO / 'assets_dev' / 'worlds' / world / 'events' / 'maps' / f'{path.stem}.lua'
    bodies = event_bodies(lua.read_text(errors='replace') if lua.exists() else '')
    openers = collections.defaultdict(set)
    for event, body in bodies.items():
        for door_id in re.findall(r'evt\.SetDoorState\((\d+),', body):
            openers[int(door_id)].add(event)
    faces_by_event = collections.defaultdict(list)
    for face in faces:
        event = (face['face_param'] or {}).get('cog_triggered') or 0
        if event:
            faces_by_event[event].append(face)

    clickable = []
    for face in faces:
        if not face['attributes'] & CLICKABLE or face['facet_type'] not in (1, 2):
            continue
        event = (face['face_param'] or {}).get('cog_triggered') or 0
        body = bodies.get(event, '')
        opened = {int(x) for x in re.findall(r'evt\.SetDoorState\((\d+),', body)}
        texture = face['texture_name'].lower()
        rooms = (face['room_number'], face['room_behind_number'])
        clickable.append(dict(
            face=face['index'], event=event, hint=event_hint(body), texture=face['texture_name'],
            door=face_door.get(face['index']), opens_own=face_door.get(face['index']) in opened,
            opens_door=bool(opened), on_static=sum(static_by_room[room].get(texture, 0) for room in rooms),
            wall_share=wall_share(texture), area=areas[face['index']], secret=bool(face['attributes'] & SECRET)))

    door_rows = []
    for door in doors:
        ids = [index for index in (door.get('face_ids') or []) if index < len(faces)]
        walls = [faces[index] for index in ids if is_wall(faces[index])]
        if not walls:
            continue
        front = max(walls, key=lambda face: areas[face['index']])
        texture = front['texture_name'].lower()
        door_events = {(faces[i]['face_param'] or {}).get('cog_triggered') for i in ids
                       if faces[i]['attributes'] & CLICKABLE}
        door_openers = openers[door['door_id']]
        trigger_kinds = set()
        for event in door_openers:
            hint = event_hint(bodies.get(event, ''))
            if not faces_by_event.get(event):
                trigger_kinds.add('decoration/script')
            for face in faces_by_event.get(event, []):
                if face['attributes'] & PRESSURE_PLATE:
                    trigger_kinds.add('hidden plate')
                elif hint and VISIBLE_TRIGGER.search(hint):
                    trigger_kinds.add('visible trigger')
                else:
                    trigger_kinds.add('hidden click' if face['attributes'] & CLICKABLE else 'other face')
        if 'visible trigger' in trigger_kinds:
            trigger = 'visible'
        elif trigger_kinds & {'hidden plate', 'hidden click'}:
            trigger = 'hidden'
        else:
            trigger = 'decoration/script'
        same_panels = [face['index'] for face in walls if face['texture_name'] == front['texture_name']
                       and areas[face['index']] >= 0.25 * areas[front['index']]]
        door_rows.append(dict(
            door=door['door_id'], front=front['index'], texture=front['texture_name'], front_area=areas[front['index']],
            wall_share=wall_share(texture), on_room_walls=bool(static_rooms[texture] & set(door.get('sector_ids') or [])),
            self_open=bool(door_events & door_openers), openers=sorted(door_openers), trigger=trigger,
            panels=same_panels, secret=[index for index in ids if faces[index]['attributes'] & SECRET]))
    return clickable, door_rows


def world_features(world):
    maps = {}
    for path in sorted((REPO / 'assets_dev' / 'worlds' / world / 'maps').glob('*.blv')):
        if path.with_suffix('.scene.yml').exists():
            maps[path.stem] = map_features(world, path)
    return maps


def hidden_doors(clickable):
    """Doors opened by clicking them whose clickable front is camouflaged: {door: (front row, face ids)}."""
    groups = collections.defaultdict(list)
    for row in clickable:
        if row['door'] is not None and row['opens_own']:
            groups[row['door']].append(row)
    result = {}
    for door, rows in groups.items():
        front = max(rows, key=lambda row: row['area'])
        if front['on_static'] > 0 and front['wall_share'] >= MIN_WALL_SHARE:
            result[door] = (front, [row['face'] for row in rows])
    return result


def remote_walls(door_rows):
    return [row for row in door_rows if not row['self_open'] and row['openers'] and row['on_room_walls']
            and row['wall_share'] >= MIN_WALL_SHARE]


def select(world):
    selection = []
    for map_name, (clickable, door_rows) in world_features(world).items():
        for door, (front, face_ids) in sorted(hidden_doors(clickable).items()):
            if front['hint'] in HIDDEN_DOOR_HINTS and front['area'] >= MIN_FRONT_AREA:
                selection.append(dict(map=map_name, kind='hidden door', door=door, faces=sorted(face_ids),
                                      hint=front['hint'], texture=front['texture']))
        for row in remote_walls(door_rows):
            if (row['trigger'] == 'hidden' and row['front_area'] >= MIN_FRONT_AREA
                    and (map_name, row['door']) not in REMOTE_EXCLUDED):
                selection.append(dict(map=map_name, kind='remote hidden wall', door=row['door'],
                                      faces=sorted(row['panels']), hint='', texture=row['texture']))
        if map_name in TRIGGERS:
            selection.append(dict(map=map_name, kind='trigger', door=None, faces=TRIGGERS[map_name], hint='',
                                  texture=''))
    return selection


def score(pairs, name):
    counts = collections.Counter(pairs)
    tp, fp, fn = counts[(True, True)], counts[(True, False)], counts[(False, True)]
    print(f'  {name:58} tp {tp:3} fp {fp:4} fn {fn:3}  precision {tp / max(1, tp + fp):.2f}  recall {tp / max(1, tp + fn):.2f}')


def calibrate(args):
    maps = world_features('mm7')
    print('MM7, doors opened by clicking them (a door counts as secret when any of its faces is flagged):')
    pairs, pairs_hint = [], []
    for clickable, door_rows in maps.values():
        flagged = {row['door'] for row in door_rows if row['secret']}
        groups = collections.defaultdict(list)
        for row in clickable:
            if row['door'] is not None and row['opens_own']:
                groups[row['door']].append(row)
        chosen = hidden_doors(clickable)
        for door in groups:
            front = chosen[door][0] if door in chosen else None
            pairs.append((front is not None, door in flagged))
            pairs_hint.append((front is not None and front['hint'] in HIDDEN_DOOR_HINTS | {'Door'}, door in flagged))
    score(pairs, 'camouflaged front')
    score(pairs_hint, 'camouflaged front, no hint or "Door"')
    print('MM7, camouflaged doors opened only from elsewhere:')
    remote = [row for _, door_rows in maps.values() for row in remote_walls(door_rows)]
    for trigger in ('hidden', 'visible', 'decoration/script'):
        rows = [row for row in remote if row['trigger'] == trigger]
        print(f'  trigger {trigger:18} doors {len(rows):3}  flagged {sum(bool(row["secret"]) for row in rows)}')


def write_overrides(map_name, face_ids, check):
    """ORs the secret bit into the scene's face overrides; returns the faces that lacked it."""
    scene = REPO / 'assets_dev' / 'worlds' / 'mm6' / 'maps' / f'{map_name}.scene.yml'
    faces = parse_blv_file(scene.with_name(f'{map_name}.blv'))['payload']['faces']
    lines = scene.read_text().split('\n')
    start = next(i for i, line in enumerate(lines) if line.startswith('  face_attribute_overrides:'))
    end = start + 1
    if lines[start].strip() != 'face_attribute_overrides: []':
        while end < len(lines) and (lines[end].startswith('    ') or lines[end].strip() == ''):
            end += 1
    existing = {}
    for i in range(start + 1, end):
        match = re.match(r'    - face_index: (\d+)$', lines[i])
        if match:
            existing[int(match.group(1))] = i
    missing, added = [], []
    for face in sorted(set(face_ids)):
        if face in existing:
            i = existing[face] + 1
            while i < end and not lines[i].startswith('    - '):
                match = re.match(r'(      legacy_attributes: )(\d+)$', lines[i])
                if match:
                    if not int(match.group(2)) & SECRET:
                        missing.append(face)
                        lines[i] = f'{match.group(1)}{int(match.group(2)) | SECRET}'
                    break
                i += 1
            else:
                missing.append(face)
                lines.insert(existing[face] + 1, f'      legacy_attributes: {faces[face]["attributes"] | SECRET}')
                end += 1
            continue
        missing.append(face)
        added += [f'    - face_index: {face}', f'      legacy_attributes: {faces[face]["attributes"] | SECRET}']
    if missing and not check:
        if lines[start].strip() == 'face_attribute_overrides: []':
            lines[start] = '  face_attribute_overrides:'
        lines[end:end] = added
        temporary = scene.with_suffix('.yml.tmp')
        temporary.write_text('\n'.join(lines))
        os.chmod(temporary, os.stat(scene).st_mode & 0o777)
        os.replace(temporary, scene)
    return missing


def apply(args):
    selection = select('mm6')
    by_map = collections.defaultdict(list)
    for entry in selection:
        by_map[entry['map']].extend(entry['faces'])
    counts = collections.Counter(entry['kind'] for entry in selection)
    print(f'{dict(counts)}: {sum(len(v) for v in by_map.values())} faces in {len(by_map)} maps')
    missing_total = 0
    for map_name, face_ids in sorted(by_map.items()):
        missing = write_overrides(map_name, face_ids, args.check)
        missing_total += len(missing)
        if missing:
            print(f'  {map_name}: {"missing" if args.check else "flagged"} {missing}')
    if args.check:
        print('all selected faces carry the secret bit' if not missing_total else f'{missing_total} faces lack it')
        sys.exit(1 if missing_total else 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('calibrate', help='score the rules against MM7 flags')
    select_parser = commands.add_parser('select', help='print the MM6 selection')
    select_parser.add_argument('--json', type=Path, help='also write it as JSON (for review_shots.py)')
    apply_parser = commands.add_parser('apply', help='write the overrides')
    apply_parser.add_argument('--check', action='store_true', help='only report selected faces without the bit')
    args = parser.parse_args()
    if args.command == 'calibrate':
        calibrate(args)
    elif args.command == 'select':
        selection = select('mm6')
        for entry in selection:
            print(f"{entry['map']:8} {entry['kind']:18} door {str(entry['door']):4} {entry['hint']!r:18} "
                  f"{entry['texture']:10} faces {entry['faces']}")
        if args.json:
            args.json.write_text(json.dumps(selection, indent=1))
    else:
        apply(args)


if __name__ == '__main__':
    main()
