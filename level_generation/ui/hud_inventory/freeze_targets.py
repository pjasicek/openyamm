"""Create exact-canvas targets and native rendering fingerprints. No image generation."""
import collections
import csv
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

from finalize_classification import HERE, ROOT, digest, read, write
import native_metadata


PROFILES = {
    'hud': dict(magenta=True, teal=True),
    'hud_black': dict(magenta=True, teal=True, black=True),
    'item': dict(magenta=True, teal=True, palette_zero=True),
    'menu_bmp': dict(magenta=True, teal=True, pink=True),
    'menu_pcx': dict(magenta=True, teal=True, pink=True, blue=True),
    'menu_png': dict(magenta=True, teal=True),
}


def rendered(image, profile):
    pixels = np.array(image.convert('RGBA'))
    r, g, b = (pixels[:, :, i] for i in range(3))
    options = PROFILES[profile]
    mask = np.zeros(pixels.shape[:2], dtype=bool)
    if options.get('magenta'):
        mask |= (r >= 248) & (g <= 8) & (b >= 248)
    if options.get('teal'):
        mask |= (r <= 8) & (g >= 248) & (b >= 248)
    if options.get('black'):
        mask |= (r <= 8) & (g <= 8) & (b <= 8)
    if options.get('pink'):
        mask |= (r >= 248) & (g >= 48) & (g <= 64) & (b >= 248)
    if options.get('blue'):
        mask |= (r <= 8) & (g <= 8) & (b >= 248)
    if options.get('palette_zero') and image.mode == 'P':
        mask |= np.array(image) == 0
    pixels[mask, 3] = 0
    # RGB under alpha zero does not affect rendering, but the source/palette hashes retain it.
    pixels[pixels[:, :, 3] == 0, :3] = 0
    return Image.fromarray(pixels)


def rendering_profiles(row):
    usages = row['usages']
    profiles = set()
    for usage in usages:
        source = usage['source']
        if '/ui/menu/' in source or '/ui/screens/' in source:
            profiles.add('menu_' + Path(row['path']).suffix.lower()[1:])
        elif usage['kind'] in {'item_table', 'equipment_variant_family'}:
            profiles.add('item')
        else:
            profiles.add('hud_black' if Path(row['path']).stem.lower().startswith(('mapdir', 'micon')) else 'hud')
    if not profiles:
        # Unknown historical consumers are conservatively kept in the original indexed format.
        profiles = {'hud', 'item', 'menu_' + Path(row['path']).suffix.lower()[1:]}
    return sorted(profiles)


def frame_metadata(row):
    name = Path(row['path']).stem.lower()
    portrait = next((u for u in row['usages'] if u['kind'] == 'portrait_table_family'), None)
    if portrait:
        prefix = portrait['prefix'].lower()
        suffix = name[len(prefix):]
        assert name.startswith(prefix) and suffix.isdigit(), f'Unrecognized portrait frame: {name}'
        return dict(family=prefix.rstrip('-'), ordinal=int(suffix),
                    timing='portrait_frame_data.txt expression selection', identity_seed_required=True,
                    character_id=portrait['character_id'], prefix=prefix)
    match = re.fullmatch(r'((?:[678])?pc\d+)-(\d+)', name)
    if match:
        return dict(family=match[1], ordinal=int(match[2]), timing='portrait_frame_data.txt expression selection',
                    identity_seed_required=True)
    match = re.fullmatch(r'((?:[678])?(?:terra|hglas))(\d+)', name)
    if match:
        family, ordinal = match[1], int(match[2])
        timing = ('floor(minutes_of_day / 1440 * 244), clamped 0..243' if family == 'terra' else
                  'frames 60..119 over 4 seconds (15 fps)' if family == 'hglas' else
                  'Historical sequence: preserve source order; no active timing claimed for prefixed legacy copy.')
        return dict(family=family, ordinal=ordinal, timing=timing)
    if re.fullmatch(r'ia02-\d+', name):
        return dict(family='ia02', ordinal=int(name.split('-')[-1]), timing='frames 1..10; 50 ms/frame')
    animations = [u for u in row['usages'] if u['kind'] in {'hud_animation_table', 'journal_animation_family'}]
    if animations:
        return dict(families=animations, timing='icon_frame_data raw lengths * 8 ticks; journal IRA groups 10 fps',
                    ordinal=int(re.search(r'\d+$', name).group()) if re.search(r'\d+$', name) else 0)
    return None


def namespace_path(row):
    path = Path(row.get('runtime_source', row['path']))
    parts = path.parts
    if parts[1] == 'engine':
        namespace, local = 'engine', Path(*parts[2:])
    else:
        namespace, local = 'worlds/' + parts[2], Path(*parts[3:])
    return namespace, local


def spell_crops(targets):
    pages = {}
    for target in targets:
        for usage in target['usages']:
            if usage.get('screen') == 'Spellbook' and target['treatment'] == 'spellbook_page':
                pages[usage['element']] = target
    for target in targets:
        if target['treatment'] != 'spell_icon_pair':
            continue
        recipes = []
        for usage in target['usages']:
            if usage.get('screen') != 'Spellbook':
                continue
            page_name = max((n for n in pages if usage['element'].startswith(n + 'Spell')), key=len)
            node = usage['layout_chain'][-1]
            parent = usage['layout_chain'][-2]
            width, height = float(node['width']), float(node['height'])
            x, y = float(node.get('offset_x', 0)), float(node.get('offset_y', 0))
            assert node.get('anchor') == 'center', f'Unhandled spell anchor: {usage}'
            x += (float(parent['width']) - width) / 2
            y += (float(parent['height']) - height) / 2
            rect = [x * 2, y * 2, width * 2, height * 2]
            assert all(v.is_integer() for v in rect), f'Fractional x2 crop: {usage}'
            rect = [int(v) for v in rect]
            recipes.append(dict(element=usage['element'], state=usage['state'], page_target=pages[page_name]['id'],
                native_draw_rect=[x, y, width, height], x2_draw_rect=rect, context_pixels_x2=16,
                accepted_page_hash_required=True,
                rule='Crop accepted page at this draw rectangle, with clipped 16px context. Export at the state\'s '
                     'own exact x2 native canvas. Preserve common page pixels outside icon/state art; review both '
                     'states composited at this rectangle. A changed page hash invalidates dependent acceptance.'))
        target['page_dependencies'] = recipes


def main():
    classification = read('classification.json')
    for name, sha in classification['inputs'].items():
        assert digest(HERE / name) == sha, f'Classification input drift: {name}'
    targets, appearances = [], collections.defaultdict(list)
    metadata = native_metadata.load()
    table_lines = {}
    for row in classification['files']:
        if row['disposition'] != 'restore':
            continue
        source = ROOT / row['path']
        assert digest(source) == row['sha256'] and row['baseline']['native_baseline_verified']
        namespace, local = namespace_path(row)
        profiles = rendering_profiles(row)
        with Image.open(source) as image:
            assert list(image.size) == row['native_size']
            palette = image.getpalette()
            fingerprints = {}
            for profile in profiles:
                rgba = rendered(image, profile)
                fingerprints[profile] = dict(
                    rgba_sha256=hashlib.sha256(str(image.size).encode() + rgba.tobytes()).hexdigest(),
                    opaque_bounds=list(rgba.getbbox()) if rgba.getbbox() else None,
                    alpha_sha256=hashlib.sha256(rgba.getchannel('A').tobytes()).hexdigest(),
                    alpha_range=list(rgba.getchannel('A').getextrema()))
            palette_hash = hashlib.sha256(bytes(palette)).hexdigest() if palette else None
            raw_rgba_hash = hashlib.sha256(str(image.size).encode() + image.convert('RGBA').tobytes()).hexdigest()
        differing_masks = len({v['alpha_sha256'] for v in fingerprints.values()}) > 1
        # Retain a key/index-aware source format when a single RGBA mask cannot serve its consumers.
        suffix = source.suffix.lower() if differing_masks else '.png'
        output_local = Path(local.parts[0] + '_x2', *local.parts[1:]).with_suffix(suffix)
        output_local = output_local.with_name(output_local.name.lower())
        target_id = namespace.replace('/', '-') + '--' + local.as_posix().lower().replace('/', '--')
        target = dict(id=target_id, source_path=row['path'], source_sha256=row['sha256'], namespace=namespace,
            runtime_name=local.stem.lower(), native_size=row['native_size'], x2_size=row['x2_size'],
            treatment=row['treatment'], native_baseline=row['baseline'], usages=row['usages'],
            logical_canvas=[0, 0, *row['native_size']], placement='Preserve the full canvas; never trim or recenter. '
                'Use each YAML layout_chain or referenced native table for actual drawing anchors.',
            frame=frame_metadata(row), native_palette_sha256=palette_hash, native_rgba_sha256=raw_rgba_hash,
            compositing=dict(profiles=profiles, fingerprints=fingerprints, preserve_indexed_keys=differing_masks,
                cleanup='key_aware_native_format' if differing_masks else
                        'opaque_canvas' if all(v['alpha_range'] == [255, 255]
                                               for v in fingerprints.values()) else 'alpha_cutout_or_effect',
                rule='Decode native palette first. Preserve alpha, native key roles and thin/glowing features. '
                     'Remove generation matte spill without eroding silhouettes. If consumers differ, preserve '
                     'native key/index semantics in BMP/PCX; do not flatten them into one incompatible alpha mask.'),
            output_path=(HERE / 'exports' / namespace / output_local).relative_to(ROOT).as_posix(),
            runtime_output_path=(Path('assets_dev') / namespace / output_local).as_posix(),
            disposition='restore', acceptance='pending', aliases=[], generation_started=False)
        state_groups = collections.defaultdict(set)
        target['native_table_rows'] = []
        for usage in row['usages']:
            if usage['kind'] == 'yaml':
                state_groups[(usage['source'], usage['element'])].add(usage['state'])
            source_name = usage['source']
            if '/data_tables/' in source_name and usage.get('line', 0) > 0:
                if source_name not in table_lines:
                    table_lines[source_name] = (ROOT / source_name).read_text(errors='replace').splitlines()
                table_row = dict(source=source_name, line=usage['line'],
                                 fields=table_lines[source_name][usage['line'] - 1].split('\t'))
                if table_row not in target['native_table_rows']:
                    target['native_table_rows'].append(table_row)
        target['state_aliases'] = [dict(source=s, element=e, states=sorted(states), artifact_target=target_id)
                                  for (s, e), states in state_groups.items() if len(states) > 1]
        native_metadata.attach(target, metadata)
        targets.append(target)
        # Candidates only: neither runtime namespace semantics nor accepted generated art is deduced from this key.
        key = hashlib.sha256(json.dumps([row['native_size'], profiles, fingerprints], sort_keys=True).encode()).hexdigest()
        appearances[key].append(target_id)
    spell_crops(targets)
    assert len({t['id'] for t in targets}) == len(targets)
    assert len({t['output_path'].lower() for t in targets}) == len(targets)
    inputs = {str(HERE.relative_to(ROOT) / 'classification.json'): digest(HERE / 'classification.json')}
    dependencies = set()
    for target in targets:
        dependencies.update(u['source'] for u in target['usages'])
    dependencies.update(['assets_dev/engine/data_tables/complex_item_pictures.txt',
        'assets_dev/engine/data_tables/doll_types.txt', 'assets_dev/engine/data_tables/complex_item_picture_offsets.txt',
        'assets_dev/engine/data_tables/portrait_frame_data.txt',
        'assets_dev/engine/data_tables/icon_frame_data.txt', 'assets_dev/engine/data_tables/arcomage_cards.txt'])
    dependencies.update(p.relative_to(ROOT).as_posix()
                        for p in (ROOT / 'assets_dev/worlds').glob('*/data_tables/complex_item*.txt'))
    # Consumer code is descriptive provenance, not a restoration input.
    # Freeze asset/data contracts without coupling queue readiness to engine development.
    dependencies = {name for name in dependencies
                    if Path(name).suffix.lower() not in {'.c', '.cc', '.cpp', '.cxx', '.h', '.hh', '.hpp', '.hxx', '.inl'}}
    for name in sorted(dependencies):
        assert (ROOT / name).is_file(), f'Missing placement/consumer evidence: {name}'
        inputs[name] = digest(ROOT / name)
    fonts = []
    for font in classification['fonts']:
        fonts.append(dict(**font, disposition='retain_non_target', owner='tools/font_upscale/README.md',
            reason='Font glyphs remain owned by faithful TrueType/legacy bitmap rendering; no AI-painted text atlas.',
            source_hashes={p: digest(ROOT / p) for p in font['files']}))
    for font in fonts:
        inputs.update(font['source_hashes'])
    for name in ['repairs/source_repairs.json', 'repairs/mobile_duplicate_immolation.patch', 'native_metadata.py']:
        inputs[str(HERE.relative_to(ROOT) / name)] = digest(HERE / name)
    write('expected_targets.json', dict(schema_version=1, preparation_only=True, inputs=inputs,
        summary=dict(targets=len(targets), by_treatment=dict(collections.Counter(t['treatment'] for t in targets)),
                     native_render_candidate_groups=sum(len(v) > 1 for v in appearances.values()),
                     generation_started=False, accepted=0),
        rendering_profiles=PROFILES, targets=targets,
        appearance_candidates=[dict(fingerprint=k, targets=v, shared_generation_approved=False)
                               for k, v in sorted(appearances.items()) if len(v) > 1],
        missing_references=classification['missing_references'], fonts=fonts,
        source_repair_prerequisites=read('repairs/source_repairs.json'),
        generated_and_external=[dict(**r, disposition='retain_non_target',
            owners=(['level_generation/creatures/SPRITE_ATLAS_VARIANTS_PIPELINE.md', 'game/audio/HouseVideoPlayer.cpp']
                    if r['name'] == 'Actor inspection and house movies' else [r['source']]))
            for r in classification['generated_and_external']]))
    print(json.dumps(dict(targets=len(targets), spell_states=sum(t['treatment'] == 'spell_icon_pair' for t in targets),
                         mask_sensitive_sources=sum(t['compositing']['preserve_indexed_keys'] for t in targets)), indent=2))


if __name__ == '__main__':
    main()
