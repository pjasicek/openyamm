"""Export static native decoration alpha cards for the optional Cycles sun-shadow bake.

Runs with system Python (Pillow/PyYAML), independently of Blender's Python packages.
No artwork is authored: indexed BMP palette entry zero supplies native transparency.
"""
import argparse
import collections
import csv
import json
import math
from pathlib import Path
import re
import sys

from PIL import Image, ImageChops, ImageOps
import yaml

from bake_assets import texture_paths

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file


def sprite_states(text, script):
    """Read literal SetSprite calls without interpreting Lua or matching comments/string contents.

    All branches contribute possibilities. Computed calls and aliases are deliberately unsupported.
    """
    pattern = re.compile(
        r'--\[(=*)\[.*?\]\1\]|--[^\n]*|\[(=*)\[.*?\]\2\]|'
        r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_][A-Za-z_0-9]*|[0-9]+|[^\s]', re.S)
    tokens = [m.group() for m in pattern.finditer(text)
              if not m.group().startswith('--')]
    states = collections.defaultdict(set)
    for i, token in enumerate(tokens):
        if token != 'SetSprite':
            continue
        end = next((j for j in range(i + 1, min(i + 9, len(tokens))) if tokens[j] == ')'), i + 1)
        call = tokens[i + 1:end + 1]
        valid = (tokens[max(0, i - 2):i] == ['evt', '.'] and len(call) in (5, 7)
                 and call[0] == '(' and call[2] == ',' and call[-1] == ')'
                 and call[1].isdigit() and call[3] in ('0', '1', 'false', 'true'))
        if valid and len(call) == 7:
            valid = (call[4] == ',' and re.fullmatch(r'''["'][a-zA-Z0-9_. -]*["']''', call[5])
                     and call[5][0] == call[5][-1])
        if not valid:
            raise ValueError('Unresolved SetSprite call or alias in ' + str(script)
                             + '; expected evt.SetSprite(literal index, 0|1, literal sprite name)')
        name = call[5][1:-1].strip().lower() if len(call) == 7 else ''
        # Legacy SetSprite uses "0", like an omitted name, to change visibility only.
        if name == '0':
            name = ''
        states[int(call[1])].add((call[3] in ('1', 'true'), name))
    return states


def intersect_states(states):
    """Intersect masks at their bottom-center world anchor, including scale and mirroring.

    Use the smallest common canvas and the finest source sampling; resampling never stretches
    one state's silhouette to match another. Values are minimum opacity across all states.
    """
    width = min(s['width'] for s in states)
    height = min(s['height'] for s in states)
    density = max(max(s['alpha'].width / s['width'], s['alpha'].height / s['height']) for s in states)
    size = (max(1, math.ceil(width * density)), max(1, math.ceil(height * density)))
    if max(size) > 8192:
        raise ValueError('Shared decoration mask exceeds 8192 pixels')
    result = Image.new('L', size, 255)
    for state in states:
        alpha = ImageOps.mirror(state['alpha']) if state['mirrored'] else state['alpha']
        sx, sy = alpha.width / state['width'], alpha.height / state['height']
        # PIL coordinates are top-down; all state bottoms share z=0.
        transform = (width / size[0] * sx, 0, (state['width'] - width) * sx / 2,
                     0, height / size[1] * sy, (state['height'] - height) * sy)
        aligned = alpha.transform(size, Image.Transform.AFFINE, transform,
                                  resample=Image.Resampling.BILINEAR, fillcolor=0)
        result = ImageChops.darker(result, aligned)
    return result, width, height


def export_cards(profile, output):
    assets = ROOT / 'assets_dev'
    world = assets / 'worlds' / profile['world']
    source = world / 'maps' / profile['map']
    dependencies = set()

    def use(path):
        dependencies.add(str(path.relative_to(assets)))
        return path

    scene = yaml.safe_load(use(source.with_suffix('.scene.yml')).read_text())
    entities = parse_odm_file(use(source))['payload']['entities']
    overrides = {entry['entity_index']: entry for entry in scene.get('entities', [])}
    for entity in entities:
        entity.update(overrides.get(entity['index'], {}))
    override_keys = {e['event_id_primary'] or e['index'] for e in entities}
    table = use(assets / 'engine/data_tables/decoration_data.txt')
    with table.open() as stream:
        rows = [r for r in csv.reader(stream, delimiter='\t') if r and r[0].isdigit()]
    by_name = {r[1].lower(): r for r in rows}
    by_id = {int(r[0]) - 1: r for r in rows}
    aliases = {alias.strip().lower(): r for r in rows if len(r) > 14
               for alias in r[14].split('|') if alias.strip()}
    sprite_paths = texture_paths(assets, profile['world'], 'sprites')
    frames_path = use(assets / 'engine/rendering/sprite_frame_data_common.yml')
    groups = {s['sprite_id']: s for s in yaml.safe_load(frames_path.read_text())['sprites']}
    groups_by_name = {s['sprite_name'].lower(): s for s in groups.values()}
    changes = collections.defaultdict(set)
    scripts = [world / 'events/maps' / (source.stem + '.lua')]
    scripts.extend(sorted((world / 'events/maps').glob(source.stem + '_*.lua')))
    for script in scripts:
        if not script.exists():
            continue
        # Lua strings/comments retain legacy STR bytes and need not be UTF-8. Latin-1
        # maps bytes losslessly for this ASCII syntax scanner; it does not transcode assets.
        text = script.read_bytes().decode('latin-1')
        for index, states in sprite_states(text, script).items():
            if index not in override_keys:
                raise ValueError('SetSprite target has no matching map entity event key: ' + str(index))
            changes[index].update(states)

    texture_overrides = {}
    manifest = world / 'rendering/decoration_overrides' / source.name / 'manifest.yml'
    if manifest.exists():
        data = yaml.safe_load(use(manifest).read_text())
        if data['schema_version'] != 1:
            raise ValueError('Unsupported decoration texture override schema')
        texture_overrides = {(t['name'].lower(), t['palette_id']): t for t in data['textures']}

    cards, skipped, textures = [], [], {}
    output.mkdir(parents=True, exist_ok=True)
    def resolve_state(entity, name, initial=False):
        # DecorationTable::resolveMapDecoration resolves an empty initial name to null,
        # even if the map's raw descriptor ID points at a pending or visible entry.
        if initial and not name:
            return None, 'marker_or_no_visible_sprite'
        row = by_name.get(name)
        if row is None and initial:
            row = by_id.get(entity['decoration_list_id'])
            if row is None or row[1].lower() == 'pending':
                row = aliases.get(name)
        if row is None and not initial and name in groups_by_name:
            flags = set()
            sprite_id = groups_by_name[name]['sprite_id']
        else:
            if row is None or row[1].lower() == 'pending':
                raise ValueError('Unresolved decoration or sprite state: ' + name)
            flags = set(row[11].split(','))
            sprite_id = int(row[12])
        reason = None
        if not name or not sprite_id or 'DontDraw' in flags or 'Marker' in flags:
            reason = 'marker_or_no_visible_sprite'
        elif flags & {'EmitFire', 'EmitSmoke'}:
            reason = 'fire_or_smoke_emitter'
        group = groups.get(sprite_id)
        if reason is None and (group is None or not group['frames']):
            raise ValueError('Missing sprite group: ' + str(sprite_id))
        if reason is None and len(group['frames']) != 1:
            reason = 'animated_sprite'
        if reason:
            return None, reason
        frame = group['frames'][0]
        frame_flags = frame['flags']
        if 'Fidget' in frame_flags:
            raise ValueError('Unsupported decoration fidget texture selection: ' + name)
        # Match renderer octants, using the sun as the virtual observer.
        angle = math.radians(entity['facing'] - profile['azimuth']) + math.pi / 8
        octant = math.floor(angle / (math.pi / 4)) & 7
        mirrored = 'Mirror' + str(octant) in frame_flags
        texture = frame['texture_name'].lower()
        if 'Image1' not in frame_flags and not texture.endswith('0'):
            if 'Images3' in frame_flags:
                suffix = 4 if octant in (3, 4, 5) else 2 if octant in (2, 6) else 0
            else:
                suffix = (8 - octant) % 8 if mirrored else octant
            texture += str(suffix)
        key = (texture, frame['palette_id'])
        if key not in textures:
            override = texture_overrides.get(key)
            if override:
                path = use(manifest.parent / override['file'])
                image = Image.open(path).convert('RGBA')
                width, height = override['logical_size']
                if image.size != (width * override['pixel_scale'], height * override['pixel_scale']):
                    raise ValueError('Decoration override dimensions disagree: ' + str(path))
                alpha = image.getchannel('A')
            else:
                path = sprite_paths.get(texture)
                if path is None:
                    raise ValueError('Missing decoration BMP: ' + texture)
                image = Image.open(use(path))
                if image.mode != 'P':
                    raise ValueError('Expected indexed native sprite: ' + str(path))
                width, height = image.size
                alpha = image.point([0] + [255] * 255, mode='L')
            mask_path = output / (texture + '_' + str(frame['palette_id']) + '.png')
            alpha.save(mask_path)
            textures[key] = dict(mask=str(mask_path.resolve()), alpha=alpha, width=width, height=height,
                                 source=str(path.relative_to(assets)))
        scale = max(float(frame.get('scale', 1)), .01)
        texture_data = textures[key]
        return dict(name=name, width=texture_data['width'] * scale, height=texture_data['height'] * scale,
                    alpha=texture_data['alpha'], mask=texture_data['mask'],
                    source=texture_data['source'], mirrored=mirrored), None

    for entity in entities:
        name = entity['name'].strip().lower()
        override_key = entity['event_id_primary'] or entity['index']
        possible = changes[override_key] | {(True, name)}
        state_names = sorted({state_name for visible, state_name in possible})
        reason = None
        if entity.get('initial_decoration_flag', entity['ai_attributes']) & 0x20:
            reason = 'initially_hidden'
        elif any(not visible for visible, _ in possible):
            reason = 'can_be_hidden'
        resolved = []
        if reason is None:
            for state_name in state_names:
                # An empty replacement name keeps the existing appearance in the runtime.
                if not state_name and name:
                    continue
                state, reason = resolve_state(entity, state_name, initial=state_name == name)
                if reason:
                    break
                resolved.append(state)
        if reason:
            skipped.append(dict(index=entity['index'], name=name, states=state_names, reason=reason))
            continue
        card = {k: v for k, v in resolved[0].items() if k != 'alpha'}
        if len(resolved) > 1:
            alpha, width, height = intersect_states(resolved)
            if alpha.getbbox() is None:
                skipped.append(dict(index=entity['index'], name=name, states=state_names,
                                    reason='no_shared_silhouette'))
                continue
            path = output / ('shared_' + str(entity['index']) + '.png')
            alpha.save(path)
            card.update(mask=str(path.resolve()), width=width, height=height, mirrored=False)
        card.update(index=entity['index'], name=name, position=entity['position'], states=state_names,
                    override_key=override_key,
                    sources=sorted({s['source'] for s in resolved}),
                    policy='shared_states' if len(resolved) > 1 else 'static')
        cards.append(card)
    result = dict(cards=cards, skipped=skipped, dependencies=sorted(dependencies),
                  counts=dict(casters=len(cards), skipped=len(skipped)),
                  skip_reasons=dict(collections.Counter(s['reason'] for s in skipped)))
    (output / 'cards.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = export_cards(json.loads(args.profile.read_text()), args.output)
    print(json.dumps(result))
