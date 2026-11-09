#!/usr/bin/env python3
"""The isle props' decoration variants (one per prop and placement scale) -> work/decorations_plan.json, and the
three MM9 world files they need (devdocs/WORLD_DECORATION_CONTRIBUTIONS.md), printed (default) or appended with --apply:
  - worlds/mm9/data_tables/decoration_data.txt: one row each, numbered in the world's decorations range (world.yml
    idRanges, rows 2001-2999; a map entity's decoration_list_id is the number minus 1), next free number first;
    collision radius and height from the model for MM9's Solid props, 0 for the walk-through ones; the fires' lights;
  - worlds/mm9/rendering/sprite_frame_data_world_decorations.yml: one sprite each (ids 24801-24999; one frame of the
    engine's 'pending' texture, never drawn while the model is bound: a decoration's model is found through its sprite);
  - worlds/mm9/models/decorations.yml: the model bindings (height = the model height x the MM9 scale, yaw: facing).
Rows already present keep their numbers (built maps store them). --apply re-reads each file right before writing,
refuses a name that is already an engine decoration, sprite or binding, and only appends (a missing file is created
with its header). --assets <root> reads and writes the files in another asset root instead (the MM9 rework's review
root, output/mm9_rework/assets_dev), through review_root.install so its hard-linked originals stay untouched.
Usage: tables.py [--apply] [--assets <root>]"""
import json
import os
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import props_table  # noqa: E402

ASSETS = Path(sys.argv[sys.argv.index('--assets') + 1]).resolve() if '--assets' in sys.argv else REPO / 'assets_dev'
WORLD = ASSETS / 'worlds/mm9'
DECORATIONS = WORLD / 'data_tables/decoration_data.txt'
SPRITES = WORLD / 'rendering/sprite_frame_data_world_decorations.yml'
BINDINGS = WORLD / 'models/decorations.yml'
ENGINE_DECORATIONS = ASSETS / 'engine/data_tables/decoration_data.txt'
ENGINE_SPRITES = ASSETS / 'engine/rendering/sprite_frame_data_common.yml'
ENGINE_BINDINGS = ASSETS / 'engine/models/decorations.yml'
SPRITE_RANGE = (24801, 24999)
HEADERS = {
    DECORATIONS: 'Decoration Data\t\t\tDescriptor\t\t\t\t\t\t\tComments\tMap aliases\n'
                 '#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\tLightGreen\tLightBlue\t'
                 'SoundId\tFlags\tSpriteId\tComments\tMapAliases\n',
    SPRITES: '# The MM9 world\'s decoration sprites (sprite ids 24801-24999), loaded with the engine\'s sprite frames\n'
             '# while MM9 is the active world. Written by level_generation/props/mm9_isleofashes_claude/scripts/tables.py.\n'
             'format_version: 1\nkind: world_decoration_sprite_frames\npackage_id: mm9\nsprites:\n',
    BINDINGS: '# The MM9 world\'s decoration models (extends engine/models/decorations.yml; see its header). Written by\n'
              '# level_generation/props/mm9_isleofashes_claude/scripts/tables.py.\ndecorations:\n',
}
HINTS = {'skull': 'skull', 'shipwreck': 'shipwreck', 'vikingship': 'longship', 'book': 'book', 'podium': 'lectern',
         'statstone': 'stat stone', 'stonedebris02': 'rubble', 'stonedebris03': 'rubble', 'logsburning': 'burning logs',
         'cot': 'cot', 'stool': 'chair', 'coatrack': 'coat rack', 'dresser': 'dresser', 'roundtable': 'table',
         'well': 'well', 'cookpot': 'cook pot'}
LIGHTS = {'logsburning': (256, 255, 150, 70), 'cookpot': (160, 255, 150, 70)}
SKIP = {561}


def variants():
    raw = {o['index']: o for o in props_table.objects()}
    seen = {}
    for idx, prop in props_table.placements():
        if prop.startswith('ref_') or idx in SKIP:
            continue
        p = raw[idx]['props']
        scale = round(float(p.get('Scale', 1.0)), 3)
        seen.setdefault(prop, {}).setdefault(scale, []).append((idx, int(p.get('Solid', 0))))
    out = []
    for prop in sorted(seen):
        meta = json.loads((HERE / f'work/{prop}_meta.json').read_text())
        scales = sorted(seen[prop])
        for k, scale in enumerate(scales):
            name = f'mm9_{prop}' if k == 0 else f'mm9_{prop}_x{int(round(scale * 100))}'
            solid = max(s for _, s in seen[prop][scale])
            ex, ey, ez = meta['extent_m']           # Blender metres: x, y footprint, z up
            height = round(meta['height_units'] * scale, 1)
            radius = int(round(min(ex, ey) * 81.7 * scale / 2)) if solid else 0
            light = LIGHTS.get(prop, (0, 0, 0, 0))
            out.append({'prop': prop, 'decoration': name, 'scale': scale, 'height': height, 'radius': radius,
                        'collision_height': int(round(height)) if solid else 0, 'light': list(light),
                        'model': f'worlds/mm9/models/mm9_deco_{prop}.glb', 'placements': [i for i, _ in seen[prop][scale]],
                        'triangles': meta['triangles']})
    return out


def table_rows(path):
    rows = []
    if path.exists():
        for line in path.read_text(encoding='latin-1').splitlines():
            cells = line.split('\t')
            if cells and cells[0].strip().isdigit():
                rows.append(cells)
    return rows


def decoration_range():
    """The world's decorations range and its contribution file, as world.yml declares them."""
    world = yaml.safe_load((WORLD / 'world.yml').read_text())
    declared = world.get('idRanges', {}).get('decorations')
    contribution = [c for c in world.get('tableContributions', []) if c.get('table') == 'decorations']
    if not declared or len(contribution) != 1 or contribution[0].get('mode') != 'append' \
            or WORLD / contribution[0].get('path', '') != DECORATIONS:
        sys.exit(f"{WORLD / 'world.yml'} must declare idRanges decorations and one append contribution of "
                 f"{DECORATIONS.relative_to(WORLD)}: nothing written")
    return declared['begin'], declared['end']


def sprite_list(path):
    return (yaml.load(path.read_text(), Loader=yaml.CSafeLoader) or {}).get('sprites') or [] if path.exists() else []


def binding_list(path):
    return (yaml.safe_load(path.read_text()) or {}).get('decorations') or [] if path.exists() else []


def main():
    apply = '--apply' in sys.argv
    plan = variants()
    begin, end = decoration_range()
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
        clash = [what for what, have in (('row', engine_names), ('sprite', engine_sprites),
                                         ('binding', engine_bound)) if name in have]
        if clash:
            sys.exit(f"{name} already has an engine {', '.join(clash)}: nothing written")
        if name in world_rows:                      # placed before: its number and sprite stay
            d['provisional_id'] = int(world_rows[name][0])
            d['sprite_id'] = int(world_rows[name][12])
        else:
            d['provisional_id'], next_id = next_id, next_id + 1
            d['sprite_id'] = world_sprites.get(name)
            if d['sprite_id'] is None:
                d['sprite_id'], next_sprite = next_sprite, next_sprite + 1
            lr, r, g, b = d['light']
            row_text.append('\t'.join([str(d['provisional_id']), name, HINTS[d['prop']], '0', str(d['radius']),
                                       str(d['collision_height']), str(lr), str(r), str(g), str(b), '0', '0',
                                       str(d['sprite_id']), '-']) + '\n')
        if not begin <= d['provisional_id'] <= end or not SPRITE_RANGE[0] <= d['sprite_id'] <= SPRITE_RANGE[1]:
            sys.exit(f"{name}: number {d['provisional_id']} or sprite {d['sprite_id']} is out of its range")
        if name not in world_sprites:
            sprite_text.append(f"  - sprite_id: {d['sprite_id']}\n    sprite_name: \"{name}\"\n    frames:\n"
                               f"      - texture_name: \"pending\"\n        frame_length_raw: 0\n"
                               f"        flags: [First]\n        scale: 1.0\n")
        if name not in bound:
            binding_text.append(f"  - name: {name}\n    model: {d['model']}\n    height: {d['height']}\n"
                                f"    yaw: facing\n")
    if binding_text and not bound:
        binding_text.insert(0, '  # --- MM9 Isle of Ashes props (level_generation/props/mm9_isleofashes_claude/) ---\n')
    (HERE / 'work/decorations_plan.json').write_text(json.dumps(plan, indent=1) + '\n')
    print(''.join(row_text)); print(''.join(sprite_text)); print(''.join(binding_text))
    if not apply:
        print('dry run (work/decorations_plan.json written); --apply appends the rows, sprites and bindings')
        return
    for path, text in ((DECORATIONS, row_text), (SPRITES, sprite_text), (BINDINGS, binding_text)):
        if not text:
            continue
        current = path.read_text(encoding='latin-1') if path.exists() else HEADERS[path]
        if not current.endswith('\n'):
            current += '\n'
        data = (current + ''.join(text)).encode('latin-1')
        if ASSETS == REPO / 'assets_dev':
            # A new file, never an in-place write: mirrors of assets_dev hard-link these files.
            path.parent.mkdir(parents=True, exist_ok=True)
            handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f'.{path.name}.')
            with os.fdopen(handle, 'wb') as stream:
                stream.write(data)
            os.chmod(temporary, 0o644)
            os.replace(temporary, path)
        else:
            sys.path.insert(0, str(REPO / 'level_generation/projects/mm9r_common'))
            import review_root
            review_root.install(path.relative_to(ASSETS), data)
        print('APPENDED', path, len(text))


if __name__ == '__main__':
    main()
