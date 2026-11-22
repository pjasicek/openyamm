#!/usr/bin/env python3
"""Where a world's 3D-model monsters launch their missiles and spells, against the body they are drawn with.

A model monster without a release socket (actors.yml `animation.events.attack_ranged` / `cast`: `release` or `glow`)
launches from its collision cylinder: outdoors at max(24, 0.7 x height) above its feet
(OutdoorWorldRuntime::mapActorBodyLaunchPoint), indoors at 0.75 x height for a missile and 0.5 x height for a spell
(indoorActorProjectileSourceHeightFactor). The height is the descriptor's (monster_descriptors.txt); the drawn body is
the binding's model at its bind pose times `scale` (and scale_reference's sprite ratio) plus `z_offset`, as
WorldFxSystem draws it. A descriptor height borrowed from a stand-in sprite (the Doom Bug's 242 from the dragonfly)
puts the launch point in the air above a short model (feedback F4, 2026-11-21).

Every row with a ranged ability (a missile, an Attack2 missile or a spell) is listed. An error is a socketless model
whose outdoor launch point is above its drawn top (or whose descriptor height is over 1.6 x the drawn top); the fix is
the family's `height:` in source/monsters.yml (A2) or a release socket in actors.yml (S).

    python3 tools/xeen/check_actor_heights.py                # Xeen: list, exit 1 on an error
    python3 tools/xeen/check_actor_heights.py --world mm8    # the same over another world (report only)
    python3 tools/xeen/check_actor_heights.py --all          # every row, not only the ranged ones
"""

from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys

import numpy as np
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'assets_dev'
# The descriptor height may exceed the drawn top by this much before it is an error (wings, raised arms in clips).
HEIGHT_SLACK = 1.6


def table_rows(path):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        cells = line.split('\t')
        if cells and cells[0].strip().isdigit():
            rows.append(cells)
    return rows


def node_matrix(node):
    if 'matrix' in node:
        return np.array(node['matrix'], dtype=float).reshape(4, 4).T
    t = node.get('translation', [0, 0, 0])
    r = node.get('rotation', [0, 0, 0, 1])
    s = node.get('scale', [1, 1, 1])
    x, y, z, w = r
    rot = np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])
    m = np.eye(4)
    m[:3, :3] = rot * np.array(s)
    m[:3, 3] = t
    return m


def bind_pose_height_range(path):
    """GltfModelLoader's gltfBindPoseHeightRange: the accessor boxes through each mesh node's bind matrix."""
    data = path.read_bytes()
    if data[:4] != b'glTF':
        return None
    offset = 12
    gltf = None
    binary = b''
    while offset < len(data):
        length, kind = struct.unpack_from('<II', data, offset)
        chunk = data[offset + 8:offset + 8 + length]
        if kind == 0x4E4F534A:
            gltf = json.loads(chunk)
        elif kind == 0x004E4942:
            binary = chunk
        offset += 8 + length
    nodes = gltf.get('nodes', [])
    parents = {}
    for index, node in enumerate(nodes):
        for child in node.get('children', []):
            parents[child] = index

    def world(index):
        m = node_matrix(nodes[index])
        while index in parents:
            index = parents[index]
            m = node_matrix(nodes[index]) @ m
        return m

    low, high = float('inf'), float('-inf')
    for index, node in enumerate(nodes):
        if 'mesh' not in node:
            continue
        m = world(index)
        if 'skin' in node:
            skin = gltf['skins'][node['skin']]
            if skin.get('joints') and 'inverseBindMatrices' in skin:
                accessor = gltf['accessors'][skin['inverseBindMatrices']]
                view = gltf['bufferViews'][accessor['bufferView']]
                start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
                inverse = np.array(struct.unpack_from('<16f', binary, start)).reshape(4, 4).T
                m = world(skin['joints'][0]) @ inverse
        for primitive in gltf['meshes'][node['mesh']]['primitives']:
            accessor = gltf['accessors'][primitive['attributes']['POSITION']]
            if 'min' not in accessor or 'max' not in accessor:
                continue
            lo, hi = accessor['min'], accessor['max']
            for corner in range(8):
                p = np.array([hi[0] if corner & 1 else lo[0], hi[1] if corner & 2 else lo[1],
                              hi[2] if corner & 4 else lo[2], 1.0])
                y = (m @ p)[1]
                low, high = min(low, y), max(high, y)
    return (low, high) if high > low else None


def sprite_scales():
    """First-frame scale of every sprite name (default 1)."""
    scales = {}
    files = list((ASSETS / 'engine/rendering/sprite_frames').rglob('*.yml'))
    files += list(ASSETS.glob('worlds/*/rendering/sprite_frames/**/*.yml'))
    # The engine's shared frames (sprite_frame_data_common.yml): rows sized by another monster's sprite (MP42).
    files += list(ASSETS.glob('engine/rendering/sprite_frame_data*.yml'))
    for path in files:
        document = yaml.safe_load(path.read_text()) or {}
        for sprite in document.get('sprites') or []:
            frames = sprite.get('frames') or [{}]
            scales.setdefault(sprite.get('sprite_name'), float(frames[0].get('scale', 1.0) or 1.0))
    return scales


def ranged_abilities(cells):
    abilities = []
    if len(cells) > 19 and cells[19].strip() not in ('', '0'):
        abilities.append(f'missile {cells[19].strip()}')
    if len(cells) > 23 and cells[20].strip() not in ('', '0') and cells[23].strip() not in ('', '0'):
        abilities.append(f'attack2 {cells[23].strip()}')
    for use, spell in ((24, 25), (26, 27)):
        if len(cells) > spell and cells[use].strip() not in ('', '0') and cells[spell].strip() not in ('', '0'):
            abilities.append('spell ' + cells[spell].strip().strip('"').split(',')[0])
    return abilities


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--world', default='xeen')
    parser.add_argument('--all', action='store_true', help='list every bound row, not only the ranged ones')
    args = parser.parse_args()
    world = ASSETS / 'worlds' / args.world

    descriptors = {}
    for path in (ASSETS / 'engine/data_tables/monster_descriptors.txt', world / 'data_tables/monster_descriptors.txt'):
        for cells in table_rows(path):
            descriptors[cells[1]] = cells
    rows = table_rows(world / 'data_tables/monster_data.txt') if args.world == 'xeen' else \
        table_rows(ASSETS / 'engine/data_tables/monster_data.txt') + table_rows(world / 'data_tables/monster_data.txt')
    document = yaml.safe_load((world / 'models/actors.yml').read_text())
    bindings = {entry['descriptor']: entry for entry in (document.get('actors') if isinstance(document, dict)
                                                         else document) or []
                if isinstance(entry, dict) and 'descriptor' in entry}
    scales = sprite_scales()
    rows_by_id = {int(cells[0]): cells for cells in rows}
    heights = {}

    def drawn(entry):
        model = ASSETS / entry['model']
        if model not in heights:
            heights[model] = bind_pose_height_range(model) if model.exists() else None
        span = heights[model]
        if span is None:
            return None
        scale = float(entry['scale'])
        if entry.get('scale_reference'):
            own = descriptors.get(entry['descriptor'])
            reference = descriptors.get(entry['scale_reference'])
            if own is None or reference is None:
                return None
            scale *= scales.get(own[11], 1.0) / scales.get(reference[11], 1.0)
        return float(entry.get('z_offset', 0.0)) + span[1] * scale

    errors = 0
    lines = []
    seen = set()
    for cells in rows:
        picture = cells[2]
        abilities = ranged_abilities(cells)
        if not abilities and not args.all:
            continue
        entry = bindings.get(picture)
        descriptor = descriptors.get(picture)
        if entry is None or descriptor is None or (picture, tuple(abilities)) in seen:
            continue
        seen.add((picture, tuple(abilities)))
        height = int(descriptor[2])
        top = drawn(entry)
        events = ((entry.get('animation') or {}).get('events') or {})
        socketed = {role for role in ('attack_ranged', 'cast')
                    if isinstance(events.get(role), dict) and (events[role].get('release') or events[role].get('glow'))}
        outdoor = max(24.0, 0.7 * height)
        verdict = 'ok'
        if top is None:
            verdict = 'no model height'
        else:
            needs = [a for a in abilities if ('cast' if a.startswith('spell') else 'attack_ranged') not in socketed]
            if needs and (outdoor > top or height > HEIGHT_SLACK * top):
                verdict = 'ERROR launch above the body'
                errors += 1
            elif not needs:
                verdict = 'ok (socket)'
        lines.append((verdict.startswith('ERROR'), f"{cells[0]:>6} {cells[1][:24]:24} {picture[:26]:26} h={height:4} "
                      f"drawn_top={top if top is None else round(top):>4} launch_out={round(outdoor):4} "
                      f"in={round(0.75 * height):4}/{round(0.5 * height):4} sockets={','.join(sorted(socketed)) or '-':22} "
                      f"{'; '.join(abilities) or '-':32} {verdict}"))
    for _, line in sorted(lines, key=lambda item: (not item[0], item[1])):
        print(line)
    print(f'{args.world}: {len(lines)} ranged model rows, {errors} launching above the drawn body')
    # A placed actor keeps the height its scene was built with (OutdoorWorldRuntime reads the scene's): one built
    # before its row's height changed launches from the old height until the map is rebuilt.
    if args.world == 'xeen':
        import re
        stale = {}
        for scene in sorted((world / 'maps').glob('*.scene.yml')):
            text = scene.read_text(encoding='utf-8')
            for match in re.finditer(r'monster_info_id: (\d+)\n(?:.*\n){0,3}?\s+height: (\d+)', text):
                row = rows_by_id.get(int(match.group(1)))
                descriptor = descriptors.get(row[2]) if row else None
                if descriptor and int(descriptor[2]) != int(match.group(2)):
                    stale.setdefault(scene.name[:-len('.scene.yml')], set()).add(row[2])
        for stem, pictures in stale.items():
            print(f'warning: {stem} places actors built at an old height ({", ".join(sorted(pictures))}): '
                  f'rebuild the map')
    return 1 if errors and args.world == 'xeen' else 0


if __name__ == '__main__':
    sys.exit(main())
