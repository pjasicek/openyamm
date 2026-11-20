"""Export the pinned MM8 handoffs into the existing acceptance server's collection format."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json
import shutil
import sys
import urllib.request

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CREATURES = REPO / 'level_generation/creatures'
VIEWER = CREATURES / 'mm6_remaining/acceptance_viewer'
AUDIT = CREATURES / 'mm7_mm8_packed_outline/session_mm8_08/mm8_m636/readiness_audit_20261002.json'
sys.path.insert(0, str(VIEWER))
sys.path.insert(0, str(CREATURES))
import serve
from mm8_restore_queue import resolve as resolve_native_view


def read(path):
    return json.loads(path.read_text())


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.resolve().relative_to(REPO))


def snapshot_mm6():
    with urllib.request.urlopen('http://127.0.0.1:8767/api/families', timeout=20) as response:
        queue = json.load(response)
    return {'collection': queue['collection'], 'family_count': len(queue['families']),
            'artifacts': {f['id']: f['artifact_sha256'] for f in queue['families']},
            'viewer_revision': queue['viewer_revision']}


def copy_file(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    assert sha(source) == sha(destination)


def palette_actions(sources, ids):
    if 'bindings' in sources:
        return {key: copy.deepcopy(value['actions']) for key, value in sources['bindings'].items()
                if int(key) in ids}
    actors = {}
    for identifier in ids:
        actions = {}
        for name, group_name in sources['descriptor_bindings'][str(identifier)].items():
            group = sources['groups'][group_name.lower()]
            views = {}
            for view in range(8):
                sequence = []
                for frame in group['frames']:
                    texture, mirrored = resolve_native_view(frame, view)
                    sequence.append({'frame': None if texture.startswith('null') else texture,
                                     'native_texture': texture, 'mirrored': mirrored,
                                     'duration_raw': frame['frame_length_raw'],
                                     'duration_ticks': frame['frame_length_raw'] * 8,
                                     'duration_ms': frame['frame_length_raw'] * 62.5,
                                     'palette': frame.get('palette_id', 0), 'scale': frame.get('scale', 1),
                                     'flags': frame.get('flags', []),
                                     'anchor': 'center' if 'Center' in frame.get('flags', []) else 'bottom-center'})
                views[str(view)] = sequence
            actions['attack2' if name == 'shoot' else name] = {
                'native_group': group_name, 'native_group_record': group, 'views': views}
        actors[str(identifier)] = actions
    return actors


def minimum_sampling(original, sources, registration):
    for key in ['generated_detail', 'actual_generated_detail', 'actual_generated_sampling']:
        value = original.get(key, {})
        if isinstance(value, dict):
            for field in ['measured_minimum', 'minimum_sampling', 'minimum']:
                if field in value:
                    return float(value[field])
            if 'actual_sampling_range' in value:
                return float(value['actual_sampling_range'][0])
    if 'generated_sampling_min' in original:
        return float(original['generated_sampling_min'])
    samples = [min(x['effective_sampling_xy']) for x in registration.values()
               if 'effective_sampling_xy' in x]
    if samples:
        return float(min(samples))
    raise ValueError('Missing actual generated-sampling evidence')


def native_canvas(bitmap, table, canvas_size):
    with Image.open(bitmap) as image:
        indices = np.asarray(image)
        if indices.ndim != 2:
            raise ValueError('Expected native indexed BMP: ' + str(bitmap))
        rgb = table[indices]
        pixels = np.dstack((rgb, (indices != 0).astype(np.uint8) * 255))
        native = Image.fromarray(pixels)
    canvas = Image.new('RGBA', canvas_size)
    x = (canvas_size[0] - native.width) // 2
    y = canvas_size[1] - native.height
    assert x >= 0 and y >= 0
    canvas.paste(native, (x, y))
    return canvas


def stage_family(record):
    selected = REPO / record['manifest']
    acceptance = REPO / record['acceptance']
    assert sha(selected) == record['manifest_sha256'], str(selected)
    assert sha(acceptance) == record['acceptance_sha256'], str(acceptance)
    original = read(selected)
    root = selected.parent
    target = HERE / 'families' / ('mm8_' + record['stem'])
    if (target / 'staging_checks.json').exists():
        prior = read(target / 'staging_checks.json')
        metadata = read(target / 'manifest.json')
        provenance = read(target / 'source_provenance.json')
        assert provenance['selected_manifest_sha256'] == record['manifest_sha256']
        assert provenance['selected_acceptance_sha256'] == record['acceptance_sha256']
        assert serve.artifact_digest(target, (target / 'manifest.json').read_bytes(), metadata) == prior['artifact_sha256']
        source_label = {'mixed_imagegen_and_authorized_video_x3': 'Packed outline + authorized ESRGAN Video x3',
                        'latest_method_required_playback_scope': 'Packed outline; four unused poses excluded',
                        'latest_method_with_approved_pose_substitution': 'Packed outline + approved pose substitution'
                        }.get(record['category'], 'Packed outline')
        return {'creature': metadata['creature'], 'label': metadata['review_label'],
                'manifest': str((target / 'manifest.json').relative_to(HERE)),
                'manifest_sha256': sha(target / 'manifest.json'), 'artifact_sha256': prior['artifact_sha256'],
                'source': source_label, 'pipeline_status': 'manual_review_pending',
                'frame_count': len(metadata['frames']), 'minimum_sampling': metadata['generated_detail']['measured_minimum'],
                'descriptor_ids': record['descriptor_ids'], 'coverage_category': record['category']}
    source_path = root / original.get('source_manifest', 'sources.json')
    sources = read(source_path)
    base = str(sources['base_palette'])
    palettes = list(sources['palette_sources'])
    reg_path = root / original.get('placement_registration', 'registration.json')
    registration = read(reg_path) if reg_path.exists() else {}
    minimum = minimum_sampling(original, sources, registration)
    original_actions = palette_actions(sources, record['descriptor_ids'])
    anchors = {step.get('anchor', 'center' if 'Center' in step.get('flags', []) else 'bottom-center')
               for actions in original_actions.values() for action in actions.values()
               for sequence in action['views'].values() for step in sequence if step['frame'] is not None}
    assert len(anchors) == 1, (record['stem'], anchors)
    anchor = anchors.pop()
    canvas = original['logical_canvas']
    manifest = copy.deepcopy(original)
    manifest.update(creature='mm8:' + record['stem'], review_label='MM8 ' + record['label'],
                    quality_status='manual_review_pending', anchor=anchor,
                    logical_pivot=[canvas[0] / 2, canvas[1] / 2 if anchor == 'center' else canvas[1]],
                    installed=False, source_manifest='source_provenance.json',
                    source_run='source_provenance.json', review_record='source_provenance.json')
    manifest['generated_detail'] = {'measured_minimum': minimum, 'physical_export_tier': 2,
                                    'interpolation_is_not_new_detail': True,
                                    'whole_animation_priority': True,
                                    'original_record': copy.deepcopy(original.get('generated_detail',
                                                       original.get('actual_generated_detail', {})))}
    manifest['variants'] = {}
    manifest['animations_by_palette'] = {}
    manifest['review_descriptor_by_palette'] = {}
    manifest['native_descriptor_bindings'] = original_actions
    manifest['native_group_bindings'] = {}
    for palette in palettes:
        actor, actions = next((key, value) for key, value in original_actions.items()
            if any(str(step['palette']) == palette for action in value.values()
                   for sequence in action['views'].values() for step in sequence if step['frame'] is not None))
        actions = copy.deepcopy(actions)
        for action in actions.values():
            group = action['native_group_record']
            action['native_length_raw'] = group.get('animation_length_raw', 0)
            action['sequence_ms'] = sum(frame['frame_length_raw'] * 62.5 for frame in group['frames'])
            for view, sequence in action['views'].items():
                for step in sequence:
                    if step['frame'] is not None:
                        assert step['frame'] in manifest['frames'], step['frame']
                        step['native_scale'] = step['scale']
                if all(step['frame'] is None for step in sequence):
                    action['views'][view] = []
                    action['no_image'] = True
        manifest['variants'][palette] = {'name': 'Native palette ' + palette,
                                        'palette_id': int(palette), 'exact_base_bypass': palette == base}
        manifest['animations_by_palette'][palette] = actions
        manifest['review_descriptor_by_palette'][palette] = int(actor)
        manifest['native_group_bindings'][palette] = {
            'actions': {name: action['native_group_record'] for name, action in actions.items()}}
    manifest['animations'] = copy.deepcopy(manifest['animations_by_palette'][base])
    if isinstance(original.get('regions'), list):
        manifest['regions'] = {'mask_r': '; '.join(original['regions'])} if original['regions'] else {}
    manifest['original_restoration_coverage'] = record['category']
    manifest['excluded_unused_native_images'] = record['excluded_unused_native_images']
    manifest['placement_registration'] = 'registration.json'
    save(target / 'registration.json', registration)
    save(target / 'source_provenance.json', {
        'selected_manifest': record['manifest'], 'selected_manifest_sha256': sha(selected),
        'selected_acceptance': record['acceptance'], 'selected_acceptance_sha256': sha(acceptance),
        'native_sources': rel(source_path), 'native_sources_sha256': sha(source_path),
        'coverage_category': record['category'], 'descriptor_ids': record['descriptor_ids'],
        'purpose': 'Isolated browser review export; source restoration packages and gameplay unchanged',
        'native_reference_padding': 'Integer horizontal centering and bottom padding; reviewer applies exact fractional/center correction',
        'air_center_pivot': 'Review pivot follows the native Center flags; both image coordinate grids remain unchanged'})
    tables = {}
    for palette in palettes:
        palette_path = REPO / sources['palette_sources'][palette]['path']
        if sources['palette_sources'][palette].get('sha256'):
            assert sha(palette_path) == sources['palette_sources'][palette]['sha256']
        tables[palette] = np.frombuffer(palette_path.read_bytes()[:768], np.uint8).reshape(256, 3)
        copy_file(palette_path, target / 'native_palettes' / (palette + '.act'))
    master_sources = {}
    for name, frame in manifest['frames'].items():
        native_record = sources['sources'][name]
        bitmap = REPO / native_record['path']
        assert sha(bitmap) == native_record['sha256']
        frame['source_canvas'] = native_record['size']
        for palette in palettes:
            path = target / 'native_variants' / f'{name}_{palette}.png'
            path.parent.mkdir(parents=True, exist_ok=True)
            native_canvas(bitmap, tables[palette], canvas).save(path, compress_level=3)
        candidates = []
        if frame.get('physical_master'):
            candidates.append(root / frame['physical_master'])
        candidates += [root / 'previews' / f'{name}_{base}.png', root / 'aligned_2x' / f'{name}.png']
        master = next((path for path in candidates if path.is_file()), None)
        if master is None:
            raise ValueError('No accepted material master for ' + name)
        copy_file(master, target / 'aligned_2x' / (name + '.png'))
        master_sources[name] = {'path': rel(master), 'sha256': sha(master)}
        frame['physical_master'] = 'aligned_2x/' + name + '.png'
    alpha_checks = 0
    material_checks = 0
    for page_index, page in enumerate(manifest['pages']):
        inherited = original['pages'][page_index]
        page['base'] = f'atlas/base_{page_index}.png'
        page['mask'] = f'atlas/mask_{page_index}.png'
        copy_file(root / inherited['base'], target / page['base'])
        mask_path = root / inherited['mask']
        with Image.open(mask_path) as mask:
            if mask.mode == 'L' and manifest['regions']:
                mask.convert('RGB').save(target / page['mask'])
                page['review_mask_format'] = 'RGB copies of identical R8 coverage; only mask_r selectable'
            else:
                copy_file(mask_path, target / page['mask'])
        with Image.open(root / inherited['base']) as image:
            base_image = image.convert('RGBA')
        base_alpha = np.asarray(base_image)[:, :, 3]
        page['variant_previews'] = {base: page['base']}
        for palette in palettes:
            if palette == base:
                continue
            destination = f'previews/palette_{palette}_page_{page_index}.png'
            previous = inherited.get('variant_previews', {}).get(palette)
            if previous:
                copy_file(root / previous, target / destination)
                with Image.open(target / destination) as image:
                    variant = image.convert('RGBA')
            else:
                variant = Image.new('RGBA', page['size'])
                occupied = {}
                for name, frame in manifest['frames'].items():
                    if frame['page'] != page_index:
                        continue
                    # Completions may refer back to preserved earlier physical masters/pages.
                    master_parent = (REPO / master_sources[name]['path']).parent.parent
                    candidates = [root / 'previews' / f'{name}_{palette}.png',
                                  master_parent / 'previews' / f'{name}_{palette}.png']
                    preview = next((path for path in candidates if path.is_file()), None)
                    if preview is None:
                        raise ValueError('No accepted palette preview for ' + name + '/' + palette)
                    with Image.open(preview) as image:
                        tile = image.convert('RGBA').crop(frame['crop_in_aligned_px'])
                    x, y, width, height = frame['atlas_xywh']
                    assert tile.size == (width, height)
                    key = tuple(frame['atlas_xywh'])
                    if key in occupied:
                        assert tile.tobytes() == occupied[key]
                    else:
                        occupied[key] = tile.tobytes()
                        variant.paste(tile, (x, y))
                output = target / destination
                output.parent.mkdir(parents=True, exist_ok=True)
                variant.save(output, compress_level=3)
            assert np.array_equal(np.asarray(variant)[:, :, 3], base_alpha), record['stem'] + '/' + palette
            alpha_checks += 1
            page['variant_previews'][palette] = destination
        for name, frame in manifest['frames'].items():
            if frame['page'] != page_index:
                continue
            x, y, width, height = frame['atlas_xywh']
            tile = np.asarray(base_image.crop((x, y, x + width, y + height)))
            with Image.open(target / 'aligned_2x' / f'{name}.png') as image:
                master = np.asarray(image.convert('RGBA').crop(frame['crop_in_aligned_px']))
            assert np.array_equal(master[:, :, 3], tile[:, :, 3]), name + ': master alpha'
            visible = tile[:, :, 3] > 0
            assert np.array_equal(master[:, :, :3][visible], tile[:, :, :3][visible]), name + ': master material'
            material_checks += 1
        page.pop('mask_overlay', None)
    save(target / 'manifest.json', manifest)
    digest = serve.artifact_digest(target, (target / 'manifest.json').read_bytes(), manifest)
    save(target / 'staging_checks.json', {'status': 'passed', 'frames': len(manifest['frames']),
        'source_manifest_unchanged': sha(selected) == record['manifest_sha256'],
        'source_acceptance_unchanged': sha(acceptance) == record['acceptance_sha256'],
        'exact_base_master_alpha_material_crops': material_checks,
        'variant_page_alpha_invariant_checks': alpha_checks, 'whole_cycles_timing_mirrors_scales_preserved': True,
        'native_anchor': anchor, 'master_sources': master_sources,
        'artifact_sha256': digest, 'installed': False})
    source_label = {'mixed_imagegen_and_authorized_video_x3': 'Packed outline + authorized ESRGAN Video x3',
                    'latest_method_required_playback_scope': 'Packed outline; four unused poses excluded',
                    'latest_method_with_approved_pose_substitution': 'Packed outline + approved pose substitution'
                    }.get(record['category'], 'Packed outline')
    return {'creature': manifest['creature'], 'label': manifest['review_label'],
            'manifest': str((target / 'manifest.json').relative_to(HERE)),
            'manifest_sha256': sha(target / 'manifest.json'), 'artifact_sha256': digest,
            'source': source_label, 'pipeline_status': 'manual_review_pending',
            'frame_count': len(manifest['frames']), 'minimum_sampling': minimum,
            'descriptor_ids': record['descriptor_ids'], 'coverage_category': record['category']}


def main():
    if (HERE / 'collection.json').exists():
        raise SystemExit('Collection already pinned; do not overwrite its reviewed images or state')
    before_path = HERE / 'mm6_server_snapshot_before.json'
    if not before_path.exists():
        save(before_path, snapshot_mm6())
    roster = read(AUDIT)
    staged, failures = {}, []
    with ThreadPoolExecutor(max_workers=4) as workers:
        futures = {workers.submit(stage_family, row): row for row in roster['families']}
        for future in as_completed(futures):
            row = futures[future]
            try:
                staged[row['stem']] = future.result()
                print(row['stem'], 'staged', staged[row['stem']]['frame_count'], flush=True)
            except Exception as error:
                failures.append({'stem': row['stem'], 'error': str(error)})
                print(row['stem'], 'FAILED:', str(error), flush=True)
    save(HERE / 'preparation_status.json', {'staged_families': len(staged), 'failures': failures,
         'sources': {'path': rel(AUDIT), 'sha256': sha(AUDIT)}})
    if failures:
        raise SystemExit('Resolve recorded staging failures before pinning the collection')
    families = [staged[row['stem']] for row in roster['families']]
    collection = {'schema_version': 1, 'collection_id': 'mm8_packed_outline_selected_20261002',
                  'title': 'MM8 packed-outline collection', 'prepared_utc': datetime.now(timezone.utc).isoformat(),
                  'pixels_per_logical_pixel': 2, 'family_count': len(families),
                  'frame_count': sum(row['frame_count'] for row in families), 'families': families,
                  'coverage': roster['totals']['family_categories'], 'installed': False}
    save(HERE / 'collection.json', collection)
    after = snapshot_mm6()
    before = read(before_path)
    assert after == before, 'MM6 server collection/pixels changed during preparation'
    save(HERE / 'mm6_server_snapshot_after.json', after)
    print('PINNED', collection['family_count'], 'MM8 families;', collection['frame_count'], 'frames', flush=True)


if __name__ == '__main__':
    main()
