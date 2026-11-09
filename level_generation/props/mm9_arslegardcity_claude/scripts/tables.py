#!/usr/bin/env python3
"""Arslegard City props' decoration variants (one per prop model and placement scale) -> work/decorations_plan.json,
and the rows they need in the MM9 world's decoration contribution (devdocs/WORLD_DECORATION_CONTRIBUTIONS.md), printed
(dry run) or appended with --apply (Hall of the Gods' tables.py, itself Yanmir's Fort's and Lindisfarne Monastery's,
in the isle and Anskram formats):
  - worlds/mm9/data_tables/decoration_data.txt: one row each, the next free numbers of the world range (world.yml
    idRanges decorations 2001-2999; an entity's decoration_list_id is the number minus 1). Collision: MM9 Solid props
    get radius = half the smaller footprint side and the model height; table-top things, wall and ceiling hangings
    none (NO_COLLISION); the trees (not Solid in MM9) Lindisfarne's trunk blocker (COLLISION); a reused model at a new
    scale scales its owner's row (radius and collision height by the scale ratio). No row carries a light: every MM9
    torch, lamp and candle has its Light, kept as a BLV light by the map, and the burning logs under Fire3 get an
    unlit row of their own (OWN_ROW: the isle's mm9_logsburning carries an orange light, an outdoor row);
  - worlds/mm9/rendering/sprite_frame_data_world_decorations.yml: one 'pending' sprite each (sprite block 2,
    26001-26999, once 24801-24999 is full);
  - worlds/mm9/models/indoor_decorations.yml: the bindings for BLV maps (height = model height x MM9 scale,
    yaw: facing).
A variant whose model and height match an existing world binding is that row (other projects' rows are reused by
name). --apply re-reads every file, refuses a name the engine already has, only appends, and writes each file as a new
file renamed over the old one (the review mirror hard-links assets_dev). It does not take the decorations lock itself:
run it under it, so the next free row is read inside the lock:
  flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock python3 scripts/tables.py --apply
Usage: tables.py [--apply]"""
import re
import json
import os
import struct
import sys
import tempfile

import yaml

import props_table

REPO = props_table.REPO
WORLD = REPO / 'assets_dev/worlds/mm9'
DECORATIONS = WORLD / 'data_tables/decoration_data.txt'
SPRITES = WORLD / 'rendering/sprite_frame_data_world_decorations.yml'
BINDINGS = WORLD / 'models/indoor_decorations.yml'
OUTDOOR_BINDINGS = WORLD / 'models/decorations.yml'
ENGINE_DECORATIONS = REPO / 'assets_dev/engine/data_tables/decoration_data.txt'
ENGINE_SPRITES = REPO / 'assets_dev/engine/rendering/sprite_frame_data_common.yml'
ENGINE_BINDINGS = REPO / 'assets_dev/engine/models/indoor_decorations.yml'
SPRITE_RANGE = (24801, 24999)
SPRITE_RANGE2 = (26001, 26999)     # devdocs/WORLD_DECORATION_CONTRIBUTIONS.md: the first block is full
# Hints of the props built here; a reused prop's new row takes its owner's row's hint (hint()).
HINTS = {'clansoldierhelmet': 'helmet', 'dookmilitiahelmet': 'helmet', 'horsestatue3': 'statue',
         'lamppost1': 'lamp post', 'plate1p80': 'plate'}
# Table-top and shelf things, wall and ceiling hangings, lamps and lanterns, the helmets: no collision. The lamp post too:
# its footprint centre (the decoration origin) lies under the arm, away from the post, so a cylinder there would stop the
# party in the air and miss the post (Thjorgard City's lamppost2 has none either).
NO_COLLISION = {'clansoldierhelmet', 'dookmilitiahelmet', 'lamppost1', 'plate1p80',
                # reused (a new-scale row of theirs)
                'scroll', 'scrollpickup', 'bookflat', 'bookstack01', 'beaker01', 'burner', 'jug1',
                'basketfruit', 'basketveggies', 'bagherbs1', 'smithhammer', 'wallcandle', 'chandelier2',
                'chandelier3', 'clawlampup', 'shelfitem01', 'shelfitem02', 'shelfitem03', 'shelfitem03f',
                'shelfitem03hc', 'shelfitem05', 'shelfitem09', 'shelfitem09d', 'shelfitem09g', 'shelfitem09sg',
                'shield1', 'shield2', 'shield3r', 'shield4', 'bucket01', 'platestack1', 'platestack2',
                'steinfancy01', 'winebottle', 'winebottle02', 'winebottle03', 'winebottle04', 'winebottle05',
                'dwarfaxeonside', 'ropecoil', 'vials', 'orblinking', 'scroll1'}
# The trees (not Solid in MM9): Dark Passageway's trunk blockers (radius 22 / 21, height 175 at its Scale 0.7), at scale 1.
COLLISION = {'tree05': (31.4, 250.0), 'tree06': (30.0, 250.0)}
OWN_ROW = set()
EXTRA = []
HEADER = ("# The MM9 world's indoor (BLV) decoration models (extends engine/models/indoor_decorations.yml; see its\n"
          "# header). Written by level_generation/props/mm9_anskramkeep_claude/scripts/tables.py.\ndecorations:\n")


def glb_height_units(path):
    """A decoration GLB's bounds height at MM9 scale 1 (LOD0 y extent, metres x 81.7)."""
    data = path.read_bytes()
    length = struct.unpack('<I', data[12:16])[0]
    document = json.loads(data[20:20 + length])
    node = next(n for n in document['nodes'] if 'mesh' in n)
    low, high = 1e9, -1e9
    for primitive in document['meshes'][node['mesh']]['primitives']:
        accessor = document['accessors'][primitive['attributes']['POSITION']]
        low, high = min(low, accessor['min'][1]), max(high, accessor['max'][1])
    return (high - low) * 81.7


def model_of(prop):
    return f'worlds/mm9/models/mm9_deco_{prop}.glb'


def table_rows(path):
    rows = []
    if path.exists():
        for line in path.read_text(encoding='latin-1').splitlines():
            cells = line.split('\t')
            if cells and cells[0].strip().isdigit():
                rows.append(cells)
    return rows


def sprite_list(path):
    return ((yaml.load(path.read_text(), Loader=yaml.CSafeLoader) or {}).get('sprites') or []) if path.exists() else []


def binding_list(path):
    return ((yaml.safe_load(path.read_text()) or {}).get('decorations') or []) if path.exists() else []


def owner_row(prop):
    """(row, scale) of an existing world row bound to the prop's model (the scale its binding height gives)."""
    base = glb_height_units(REPO / 'assets_source' / model_of(prop))
    rows = {r[1].strip().lower(): r for r in table_rows(DECORATIONS)}
    for binding in binding_list(BINDINGS) + binding_list(OUTDOOR_BINDINGS):
        if binding['model'] == model_of(prop) and binding['name'].lower() in rows:
            return rows[binding['name'].lower()], float(binding['height']) / base
    return None


def hint(prop):
    if prop in HINTS:
        return HINTS[prop]
    existing = owner_row(prop)
    return existing[0][2].strip() if existing else prop


def variants():
    raw = {o['index']: o for o in props_table.objects()}
    seen = {}
    for idx, prop in props_table.placements():
        p = raw[idx]['props']
        scale = round(float(p.get('Scale', 1.0)), 3)
        seen.setdefault(prop, {}).setdefault(scale, []).append((idx, int(p.get('Solid', 0) or 0)))
    known = {}                                       # (model, height) -> existing decoration name
    for binding in binding_list(BINDINGS) + binding_list(OUTDOOR_BINDINGS):
        known.setdefault((binding['model'], round(float(binding['height']), 1)), binding['name'])
    names = {b['name'] for b in binding_list(BINDINGS) + binding_list(OUTDOOR_BINDINGS)}
    out = []
    for prop in sorted(seen):
        if prop in props_table.REUSED:
            base = glb_height_units(REPO / 'assets_source' / model_of(prop))
            extent = None
        else:
            meta = json.loads((props_table.HERE / f'work/{prop}_meta.json').read_text())
            base, extent = meta['height_units'], meta['extent_m']
        for scale in sorted(seen[prop], key=lambda v: (abs(v - 1.0), v)):     # scale 1 takes the plain name
            height = round(base * scale, 1)
            name = None if prop in OWN_ROW else \
                next((n for (m, h), n in known.items() if m == model_of(prop) and abs(h - height) <= 0.6), None)
            reused = name is not None
            if name is None:
                name = f'mm9_{prop}' if f'mm9_{prop}' not in names else f'mm9_{prop}_x{int(round(scale * 100))}'
                names.add(name)
            solid = max(s for _, s in seen[prop][scale]) and prop not in NO_COLLISION
            collision_height = int(round(height)) if solid else 0
            if prop in COLLISION:
                radius = int(round(COLLISION[prop][0] * scale))
                collision_height = int(round(COLLISION[prop][1] * scale))
            elif extent is None and solid:
                # the owner's row of this model (any scale), scaled by the ratio of the scales
                existing = owner_row(prop)
                ratio = scale / existing[1] if existing else 0.0
                radius = int(round(int(existing[0][4]) * ratio)) if existing else 0
                collision_height = int(round(int(existing[0][5]) * ratio)) if existing else 0
            else:
                radius = int(round(min(extent[0], extent[1]) * 81.7 * scale / 2)) if solid else 0
            out.append({'prop': prop, 'decoration': name, 'scale': scale, 'height': height, 'reused_row': reused,
                        'radius': radius, 'collision_height': collision_height,
                        'model': model_of(prop), 'placements': [i for i, _ in seen[prop][scale]]})
    for extra in EXTRA:
        out.append(dict(extra, reused_row=extra['decoration'] in names))
    return out


def write(path, text):
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f'.{path.name}.')
    with os.fdopen(handle, 'wb') as stream:
        stream.write(text.encode('latin-1'))
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def plan_rows(plan):
    """Under the lock: the rows, sprites and bindings to append, with numbers from the files as they are now."""
    declared = yaml.safe_load((WORLD / 'world.yml').read_text())['idRanges']['decorations']
    begin, end = declared['begin'], declared['end']
    world_rows = {r[1].strip().lower(): r for r in table_rows(DECORATIONS)}
    engine_names = {r[1].strip().lower() for r in table_rows(ENGINE_DECORATIONS)}
    next_id = max([int(r[0]) for r in world_rows.values()] + [begin - 1]) + 1
    world_sprites = {s['sprite_name'].lower(): s['sprite_id'] for s in sprite_list(SPRITES)}
    engine_sprites = {s['sprite_name'].lower() for s in sprite_list(ENGINE_SPRITES)}
    next_sprite = max([s['sprite_id'] + len(s['frames']) for s in sprite_list(SPRITES)] + [SPRITE_RANGE[0]])
    bound = {b['name'].lower() for b in binding_list(BINDINGS)}
    engine_bound = {b['name'].lower() for b in binding_list(ENGINE_BINDINGS)}
    rows, sprites, bindings = [], [], []
    for d in plan:
        name = d['decoration']
        if name in engine_names or name in engine_sprites or name in engine_bound:
            sys.exit(f'{name} is already an engine decoration, sprite or binding: nothing written')
        if name in world_rows:
            d['number'], d['sprite_id'] = int(world_rows[name][0]), int(world_rows[name][12])
        else:
            d['number'], next_id = next_id, next_id + 1
            d['sprite_id'] = world_sprites.get(name)
            if d['sprite_id'] is None:
                if SPRITE_RANGE[1] < next_sprite < SPRITE_RANGE2[0]:
                    next_sprite = SPRITE_RANGE2[0]
                d['sprite_id'], next_sprite = next_sprite, next_sprite + 1
            rows.append('\t'.join([str(d['number']), name, hint(d['prop']), '0', str(d['radius']),
                                   str(d['collision_height']), '0', '0', '0', '0', '0', '0', str(d['sprite_id']),
                                   '-']) + '\n')
        if not begin <= d['number'] <= end or not (SPRITE_RANGE[0] <= d['sprite_id'] <= SPRITE_RANGE[1]
                                                   or SPRITE_RANGE2[0] <= d['sprite_id'] <= SPRITE_RANGE2[1]):
            sys.exit(f"{name}: number {d['number']} or sprite {d['sprite_id']} is out of its range")
        if name not in world_sprites:
            sprites.append(f"  - sprite_id: {d['sprite_id']}\n    sprite_name: \"{name}\"\n    frames:\n"
                           f"      - texture_name: \"pending\"\n        frame_length_raw: 0\n"
                           f"        flags: [First]\n        scale: 1.0\n")
            world_sprites[name] = d['sprite_id']
        if name not in bound:
            bindings.append(f"  - name: {name}\n    model: {d['model']}\n    height: {d['height']}\n    yaw: facing\n")
            bound.add(name)
    if bindings:
        bindings.insert(0, "  # --- MM9 Arslegard City props (level_generation/props/mm9_arslegardcity_claude/) ---\n")
    return rows, sprites, bindings


def main():
    apply = '--apply' in sys.argv
    plan = variants()
    rows, sprites, bindings = plan_rows(plan)
    (props_table.HERE / 'work/decorations_plan.json').write_text(json.dumps(plan, indent=1) + '\n')
    print(''.join(rows))
    print(f'{len(rows)} rows, {len(sprites)} sprites, {max(0, len(bindings) - 1)} bindings; reused rows:',
          sorted({d['decoration'] for d in plan if d['reused_row']}))
    if not apply:
        print('dry run (work/decorations_plan.json written); --apply appends the rows, sprites and bindings')
        return
    for path, text in ((DECORATIONS, rows), (SPRITES, sprites), (BINDINGS, bindings)):
        if not text:
            continue
        current = path.read_text(encoding='latin-1') if path.exists() else HEADER
        if not current.endswith('\n'):
            current += '\n'
        write(path, current + ''.join(text))
        print('APPENDED', path, len(text))


if __name__ == '__main__':
    main()
