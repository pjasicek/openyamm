#!/usr/bin/env python3
"""Ruined Temple's decoration variants (one per prop and placement scale) -> work/decorations_plan.json, and the
rows they need in the MM9 world's decoration contribution (devdocs/WORLD_DECORATION_CONTRIBUTIONS.md), printed
(default) or appended with --apply, in the Anskram Keep's formats (its tables.py helpers and paths are reused):
  - worlds/mm9/data_tables/decoration_data.txt: one row each, next free numbers of the world range (2001-2999);
  - worlds/mm9/rendering/sprite_frame_data_world_decorations.yml: one 'pending' sprite each (24801-24999);
  - worlds/mm9/models/indoor_decorations.yml: the BLV bindings (height = model height x MM9 scale, yaw: facing).
Reused decorations (props_table.REUSED: same ABC model, skin and scale built by another project) are checked against
their existing row and binding (height) and add nothing. Collision: MM9 Solid props get radius = half the smaller
footprint side and the model height (a brazier's without its flame); wall-hung things (torches, tapestries, hanging
bowls) and the small books and key none. No row carries a light: every brazier and torch has its own MM9 Light beside
it, which the BLV keeps as a point light (placements.py names it).

Run --apply under the shared lock, so the next free row is read inside it (another agent appends to the same files):
  flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock python3 scripts/tables.py --apply
Usage: tables.py [--apply]"""
import json
import os
import sys
import tempfile

import yaml

import anskram
import props_table

base = anskram.load('tables')
DECORATIONS, SPRITES, BINDINGS = base.DECORATIONS, base.SPRITES, base.BINDINGS
HINTS = {'chest': 'chest', 'barrel': 'wooden barrel', 'crate': 'crate', 'barrel03': 'wooden barrel', 'bonepile': 'bone pile',
         'pew3ns': 'pew', 'podium01': 'podium', 'scroll': 'scroll', 'urngargoyle': 'urn', 'torchmetal': 'torch',
         'chandelier3': 'chandelier', 'tapestry_bannergeo3': 'tapestry', 'stonedebris04': 'debris',
         'stonedebris05': 'debris', 'skeletonlaying': 'skeleton', 'genielamp': 'lamp', 'treeoflife': 'tree of life'}
NO_COLLISION = {'torchmetal', 'chandelier3', 'tapestry_bannergeo3', 'scroll', 'genielamp', 'treeoflife',
                'skeletonlaying', 'stonedebris04', 'stonedebris05'}
SPRITE_RANGE2 = (26001, 26999)     # devdocs/WORLD_DECORATION_CONTRIBUTIONS.md: the first block is full     # the second block of the world's sprites (devdocs/WORLD_DECORATION_CONTRIBUTIONS.md)
UNITS_PER_METRE = 81.7
LABEL = '  # --- MM9 Ruined Temple props (level_generation/props/mm9_ruinedtemple_claude/) ---\n'


def meta(prop):
    return json.loads((props_table.home(prop) / f'work/{prop}_meta.json').read_text())


def variants():
    raw = {o['index']: o for o in props_table.objects()}
    seen = {}
    for idx, prop in props_table.placements():
        p = raw[idx]['props']
        scale = round(float(p.get('Scale', 1.0)), 3)
        seen.setdefault(prop, {}).setdefault(scale, []).append((idx, int(p.get('Solid', 0) or 0)))
    out = []
    for prop in sorted(seen):
        m = meta(prop)
        for k, scale in enumerate(sorted(seen[prop])):
            name = f'mm9_{prop}' if k == 0 and prop not in props_table.REUSED \
                else f'mm9_{prop}_x{int(round(scale * 100))}'
            existing = next((x for x in base.binding_list(BINDINGS) if x['name'] == f'mm9_{prop}'), None)
            if existing and abs(float(existing['height']) - m['height_units'] * scale) < 0.6:
                name = f'mm9_{prop}'            # the owner's own row is this scale
            solid = max(s for _, s in seen[prop][scale]) and prop not in NO_COLLISION
            ex, ey, _ = m['extent_m']
            height = round(m['height_units'] * scale, 1)
            body = m['flame_head_m'][2] * UNITS_PER_METRE * scale if m.get('flame_head_m') else height
            out.append({'prop': prop, 'decoration': name, 'scale': scale, 'height': height,
                        'radius': int(round(min(ex, ey) * UNITS_PER_METRE * scale / 2)) if solid else 0,
                        'collision_height': int(round(body)) if solid else 0,
                        'model': f'worlds/mm9/models/mm9_deco_{prop}.glb', 'reused': False,
                        'placements': [i for i, _ in seen[prop][scale]], 'triangles': m['triangles']})
    return out


def main():
    apply = '--apply' in sys.argv
    plan = variants()
    declared = yaml.safe_load((base.WORLD / 'world.yml').read_text())['idRanges']['decorations']
    begin, end = declared['begin'], declared['end']
    world_rows = {r[1].strip().lower(): r for r in base.table_rows(DECORATIONS)}
    engine_names = {r[1].strip().lower() for r in base.table_rows(base.ENGINE_DECORATIONS)}
    next_id = max([int(r[0]) for r in world_rows.values()] + [begin - 1]) + 1
    world_sprites = {s['sprite_name'].lower(): s['sprite_id'] for s in base.sprite_list(SPRITES)}
    engine_sprites = {s['sprite_name'].lower() for s in base.sprite_list(base.ENGINE_SPRITES)}
    next_sprite = max([s['sprite_id'] + len(s['frames']) for s in base.sprite_list(SPRITES)] + [base.SPRITE_RANGE[0]])
    bound = {b['name'].lower(): b for b in base.binding_list(BINDINGS)}
    engine_bound = {b['name'].lower() for b in base.binding_list(base.ENGINE_BINDINGS)}
    row_text, sprite_text, binding_text, problems = [], [], [], []
    for d in plan:
        name = d['decoration']
        if name in engine_names or name in engine_sprites or name in engine_bound:
            sys.exit(f'{name} is already an engine decoration, sprite or binding: nothing written')
        if d['reused']:
            row, binding = world_rows.get(name), bound.get(name)
            if row is None or binding is None:
                problems.append(f'{name}: reused but has no row or binding')
                continue
            d['number'], d['sprite_id'] = int(row[0]), int(row[12])
            if abs(float(binding['height']) - d['height']) > 0.15 or binding['model'] != d['model'] or \
                    (int(row[4]), int(row[5])) != (d['radius'], d['collision_height']):
                problems.append(f"{name}: row/binding {row[4]}/{row[5]} h {binding['height']} {binding['model']} != "
                                f"{d['radius']}/{d['collision_height']} h {d['height']}")
            print(f"REUSED {name} row {d['number']} sprite {d['sprite_id']} height {binding['height']} "
                  f"(model {d['height'] / d['scale']:.1f} x {d['scale']}) collision {row[4]}/{row[5]}")
            continue
        if name in world_rows:
            d['number'], d['sprite_id'] = int(world_rows[name][0]), int(world_rows[name][12])
        else:
            d['number'], next_id = next_id, next_id + 1
            d['sprite_id'] = world_sprites.get(name)
            if d['sprite_id'] is None:
                if base.SPRITE_RANGE[1] < next_sprite < SPRITE_RANGE2[0]:
                    next_sprite = SPRITE_RANGE2[0]
                d['sprite_id'], next_sprite = next_sprite, next_sprite + 1
            row_text.append('\t'.join([str(d['number']), name, HINTS[d['prop']], '0', str(d['radius']),
                                       str(d['collision_height']), '0', '0', '0', '0', '0', '0',
                                       str(d['sprite_id']), '-']) + '\n')
        if not begin <= d['number'] <= end or not (base.SPRITE_RANGE[0] <= d['sprite_id'] <= base.SPRITE_RANGE[1]
                                                 or SPRITE_RANGE2[0] <= d['sprite_id'] <= SPRITE_RANGE2[1]):
            sys.exit(f"{name}: number {d['number']} or sprite {d['sprite_id']} is out of its range")
        if name not in world_sprites:
            sprite_text.append(f"  - sprite_id: {d['sprite_id']}\n    sprite_name: \"{name}\"\n    frames:\n"
                               f"      - texture_name: \"pending\"\n        frame_length_raw: 0\n"
                               f"        flags: [First]\n        scale: 1.0\n")
        if name not in bound:
            binding_text.append(f"  - name: {name}\n    model: {d['model']}\n    height: {d['height']}\n"
                                f"    yaw: facing\n")
    if problems:
        sys.exit('\n'.join(problems))
    if binding_text:
        binding_text.insert(0, LABEL)
    (props_table.HERE / 'work/decorations_plan.json').write_text(json.dumps(plan, indent=1) + '\n')
    print(''.join(row_text))
    print(f'{len(row_text)} rows, {len(sprite_text)} sprites, {max(0, len(binding_text) - 1)} bindings')
    if not apply:
        print('dry run (work/decorations_plan.json written); --apply appends the rows, sprites and bindings')
        return
    for path, text in ((DECORATIONS, row_text), (SPRITES, sprite_text), (BINDINGS, binding_text)):
        if not text:
            continue
        current = path.read_text(encoding='latin-1')
        if not current.endswith('\n'):
            current += '\n'
        handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f'.{path.name}.')
        with os.fdopen(handle, 'wb') as stream:
            stream.write((current + ''.join(text)).encode('latin-1'))
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
        print('APPENDED', path, len(text))


if __name__ == '__main__':
    main()
