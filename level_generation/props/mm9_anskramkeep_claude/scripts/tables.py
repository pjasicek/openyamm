#!/usr/bin/env python3
"""The keep props' decoration variants (one per prop and placement scale) -> work/decorations_plan.json, and the rows
they need in the MM9 world's decoration contribution (devdocs/WORLD_DECORATION_CONTRIBUTIONS.md), printed (default) or
appended with --apply, in the formats the isle props project's tables.py writes:
  - worlds/mm9/data_tables/decoration_data.txt: one row each, next free numbers of the world range (world.yml idRanges
    decorations 2001-2999; an entity's decoration_list_id is the number minus 1). Collision: MM9 Solid props get radius
    = half the smaller footprint side and the model height; walk-through props, the scrolls and the wall torches 0.
    Only the Imp gate fires carry a light (EXTRA); each wall torch's light is the BLV light MM9 placed beside it (41-93 units away, one per
    torch; the map build pairs them, work/... in the map project), so nothing doubles;
  - worlds/mm9/rendering/sprite_frame_data_world_decorations.yml: one 'pending' sprite each (ids 24801-24999);
  - worlds/mm9/models/indoor_decorations.yml: the bindings for BLV maps (height = model height x MM9 scale, yaw:
    facing); the keep is a BLV, and the outdoor decorations.yml is a dependency of baked outdoor maps.
Rows already present keep their numbers. --apply re-reads each file right before writing, refuses a name the engine
already has, only appends, and writes assets_dev files as a new file renamed over the old one (the MM9 review mirror
hard-links them; level_generation/projects/mm9r_common/review_root.py refresh then links the new file).
Usage: tables.py [--apply]"""
import json
import os
import sys
import tempfile

import yaml

import props_table

REPO = props_table.REPO
WORLD = REPO / 'assets_dev/worlds/mm9'
DECORATIONS = WORLD / 'data_tables/decoration_data.txt'
SPRITES = WORLD / 'rendering/sprite_frame_data_world_decorations.yml'
BINDINGS = WORLD / 'models/indoor_decorations.yml'        # BLV maps read the indoor manifest
ENGINE_DECORATIONS = REPO / 'assets_dev/engine/data_tables/decoration_data.txt'
ENGINE_SPRITES = REPO / 'assets_dev/engine/rendering/sprite_frame_data_common.yml'
ENGINE_BINDINGS = REPO / 'assets_dev/engine/models/indoor_decorations.yml'
SPRITE_RANGE = (24801, 24999)
HINTS = {'barrel': 'wooden barrel', 'barrel03': 'wooden barrel', 'bed': 'bed', 'bedmedium': 'bed', 'bookcase02ew': 'bookcase',
         'bookcase02ns': 'bookcase', 'chair': 'chair', 'chair02': 'chair', 'chest': 'chest', 'chest1': 'chest',
         'crate': 'crate', 'desk01': 'desk', 'desk01ns': 'desk', 'dresserns': 'dresser', 'scroll': 'scroll',
         'tablebench': 'broken table', 'tableround': 'table', 'trashpile': 'bone pile', 'walltorch': 'torch',
         'weaponrack': 'weapon rack', 'weaponscabinet01': 'weapons cabinet', 'weaponscabinet04': 'weapons cabinet',
         'gatefire': 'fire', 'spikepit': 'spikes'}
# Decorations without a prop model in the DAT: the Imp gates' fires (MM9 Fire objects ImpGateFire0-7, LightMaxRadius
# 80 LT = 205, LightColor1). They carry their light (MM9's Fire object is its own light; no BLV light is near them).
EXTRA = [{'prop': 'gatefire', 'decoration': 'mm9_gatefire', 'scale': 1.0, 'light': [205, 255, 190, 130],
          'objects': ['Fire']}]
NO_COLLISION = {'walltorch', 'scroll'}
HEADERS = {BINDINGS: "# The MM9 world's indoor (BLV) decoration models (extends engine/models/indoor_decorations.yml; see its\n"
                     "# header). Written by level_generation/props/mm9_anskramkeep_claude/scripts/tables.py.\ndecorations:\n"}


def variants():
    raw = {o['index']: o for o in props_table.objects()}
    seen = {}
    for idx, prop in props_table.placements():
        p = raw[idx]['props']
        scale = round(float(p.get('Scale', 1.0)), 3)
        seen.setdefault(prop, {}).setdefault(scale, []).append((idx, int(p.get('Solid', 0) or 0)))
    out = []
    for prop in sorted(seen):
        meta = json.loads((props_table.HERE / f'work/{prop}_meta.json').read_text())
        for k, scale in enumerate(sorted(seen[prop])):
            name = f'mm9_{prop}' if k == 0 else f'mm9_{prop}_x{int(round(scale * 100))}'
            solid = max(s for _, s in seen[prop][scale]) and prop not in NO_COLLISION
            ex, ey, _ = meta['extent_m']
            height = round(meta['height_units'] * scale, 1)
            out.append({'prop': prop, 'decoration': name, 'scale': scale, 'height': height,
                        'radius': int(round(min(ex, ey) * 81.7 * scale / 2)) if solid else 0,
                        'collision_height': int(round(height)) if solid else 0,
                        'model': f'worlds/mm9/models/mm9_deco_{prop}.glb',
                        'placements': [i for i, _ in seen[prop][scale]], 'triangles': meta['triangles']})
    for extra in EXTRA:
        meta = json.loads((props_table.HERE / f"work/{extra['prop']}_meta.json").read_text())
        placements = [o['index'] for o in props_table.objects() if o['class'] in extra['objects']]
        out.append(dict(extra, height=round(meta['height_units'], 1), radius=0, collision_height=0,
                        model=f"worlds/mm9/models/mm9_deco_{extra['prop']}.glb", placements=placements,
                        triangles=meta['triangles']))
    return out


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


def main():
    apply = '--apply' in sys.argv
    plan = variants()
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
    row_text, sprite_text, binding_text = [], [], []
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
                d['sprite_id'], next_sprite = next_sprite, next_sprite + 1
            light = [str(v) for v in d.get('light', [0, 0, 0, 0])]
            row_text.append('\t'.join([str(d['number']), name, HINTS[d['prop']], '0', str(d['radius']),
                                       str(d['collision_height']), *light, '0', '0', str(d['sprite_id']),
                                       '-']) + '\n')
        if not begin <= d['number'] <= end or not SPRITE_RANGE[0] <= d['sprite_id'] <= SPRITE_RANGE[1]:
            sys.exit(f"{name}: number {d['number']} or sprite {d['sprite_id']} is out of its range")
        if name not in world_sprites:
            sprite_text.append(f"  - sprite_id: {d['sprite_id']}\n    sprite_name: \"{name}\"\n    frames:\n"
                               f"      - texture_name: \"pending\"\n        frame_length_raw: 0\n"
                               f"        flags: [First]\n        scale: 1.0\n")
        if name not in bound:
            binding_text.append(f"  - name: {name}\n    model: {d['model']}\n    height: {d['height']}\n"
                                f"    yaw: facing\n")
    if binding_text:
        binding_text.insert(0, '  # --- MM9 Anskram Keep props (level_generation/props/mm9_anskramkeep_claude/) ---\n')
    (props_table.HERE / 'work/decorations_plan.json').write_text(json.dumps(plan, indent=1) + '\n')
    print(''.join(row_text))
    print(f'{len(row_text)} rows, {len(sprite_text)} sprites, {max(0, len(binding_text) - 1)} bindings')
    if not apply:
        print('dry run (work/decorations_plan.json written); --apply appends the rows, sprites and bindings')
        return
    for path, text in ((DECORATIONS, row_text), (SPRITES, sprite_text), (BINDINGS, binding_text)):
        if not text:
            continue
        current = path.read_text(encoding='latin-1') if path.exists() else HEADERS[path]
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
