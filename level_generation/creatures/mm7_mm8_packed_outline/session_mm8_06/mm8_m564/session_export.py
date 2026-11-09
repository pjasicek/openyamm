"""Reuse the shared atlas packer for this session's unsupported MM8 descriptor schema.

The packer owns raster packing, extrusion, crop reconstruction and atlas checks.
This local entry point supplies current MM8 groups and preserves every descriptor,
including multiple descriptor scales sharing the same palette and artwork.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

from PIL import Image

REPO = Path.cwd().resolve()
STAGE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / 'level_generation/creatures/mm6_peasants'))
import package_family as packer


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def asset(root, path):
    path = (REPO / path).resolve()
    assert path.is_relative_to(root)
    return dict(path=str(path.relative_to(root)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def export(family):
    root = STAGE / family
    assert root.parent == STAGE and root.is_dir()
    out = root / 'redo_2x'
    os.environ['MM8_RESTORE_FAMILY'] = family
    source, config = read(root / 'sources.json'), read(root / 'config.json')
    run = read(root / 'redo_2x/run.json')
    registration = read(root / 'redo_2x/registration.json')
    assert set(registration) == set(source['sources']), 'Complete source coverage is required for family export'
    assert not any(rec['raw_clip'] for rec in registration.values()), 'Resolve clipping before export'
    jobs = {job['id']: job for job in run['jobs']}
    batches = {}
    for key in {rec['batch'] for rec in registration.values()}:
        job = jobs[key]
        attempt = next(item for item in job['attempts'] if item['raw'] == job['selected_raw'])
        attached = attempt['actual_submitted_inputs']
        assert attached[0]['role'] == 'untouched_native_complete_animation'
        assert attached[1]['role'] == 'matching_outline_only_geometry_no_shading'
        assert Path(attached[1]['path']).name == key + '_outline.png'
        assert len(attached) == 3 or attempt['bootstrap_exception']
        references = [asset(out, item['path']) for item in attached]
        assert all(left['sha256'] == right['sha256'] for left, right in zip(references, attached))
        batches[key] = dict(raw=asset(out, attempt['raw']), prompt=asset(out, attempt['prompt']),
                            references=references, actual_submitted_inputs=attached,
                            bootstrap_exception=attempt['bootstrap_exception'],
                            complete_native_frames=job['frames'], native_crop=job['native_crop'],
                            columns=job['columns'], rows=job['rows'])
    variants, names = {}, {}
    for descriptor, binding in source['bindings'].items():
        palette = str(binding['actions']['standing']['views']['0'][0]['palette'])
        variants.setdefault(palette, dict(actions={action: record['native_group_record']
                                                 for action, record in binding['actions'].items()}))
        names.setdefault(palette, []).append(binding['label'])
    assert set(variants) == set(source['palette_sources'])
    inventory = dict(logical_canvas=source['logical_canvas'], sources=source['sources'],
                     palette_paths={key: rec['path'] for key, rec in source['palette_sources'].items()},
                     pixel_aliases=source['pixel_aliases'], variants=variants)
    module_path = root / config['material_module']
    spec = importlib.util.spec_from_file_location('session_export_materials', module_path)
    materials = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(materials)
    material_review_path = root / 'material_review.json'
    if material_review_path.exists():
        material_review = read(material_review_path)
        assert material_review['status'] == 'reviewed_all_poses'
        assert material_review['selected_raw_sha256'] == {
            job['id']: hashlib.sha256((REPO / job['selected_raw']).read_bytes()).hexdigest()
            for job in run['jobs']}
        materials.CONFIG.update(regions=material_review['regions'], review_status=material_review['status'])
        materials.REGIONS = material_review['regions']
    config = dict(config, regions='; '.join(materials.REGIONS),
                  material_module=os.path.relpath(module_path, out),
                  variant_names={key: ', '.join(value) for key, value in names.items()})
    # Runtime-only function bindings reuse the existing packer; no shared files are edited.
    packer.load = lambda family, source_root: (root, config, inventory)
    packer.recolor = lambda image, mask, palette, config, vectors: materials.recolor(image, mask, palette)
    (out / 'palettes').mkdir(exist_ok=True)
    for key in source['palette_sources']:
        shutil.copy2(root / f'palettes/pal{key}.act', out / f'palettes/pal{key}.act')
    for name, record in registration.items():
        shutil.copy2(REPO / record['clean_path'], out / 'cleaned' / (name + '.png'))
    save(out / 'config.json', config)
    save(out / 'sources.json', source)
    save(out / 'generation.json', dict(method=run['method'], batches=batches))
    # This required legacy-packer field is unused by the supplied native-delta recolor function.
    save(out / 'recolor_vectors.json', {key: [0, 0, 0] for key in variants})
    packer.export(config['family'], source_root=root, output_root=out)
    manifest = read(out / 'manifest.json')
    manifest.update(creature=source['creature'], label=source['label'], installed=False,
                    merged_descriptor_ids=[int(key) for key in source['bindings']],
                    native_descriptor_bindings=source['bindings'],
                    native_group_bindings=variants, logical_pivot=source['logical_pivot'],
                    native_palettes={key: dict(source=rec, staged=asset(out, out / f'palettes/pal{key}.act'))
                                     for key, rec in source['palette_sources'].items()},
                    orphan_images=source['orphan_images'],
                    generation_method=run['method'], acceptance_status='pending_full_visual_acceptance')
    by_descriptor = {}
    for descriptor, binding in source['bindings'].items():
        actions = {}
        for action, record in binding['actions'].items():
            entry = copy.deepcopy(record)
            entry.update(playback='loop' if action in ['standing', 'walk'] else
                         'hold' if action == 'corpse' else 'once',
                         next_action='corpse' if action == 'death' else
                         'standing' if action in ['attack', 'attack2', 'hit', 'fidget'] else None,
                         no_image=record['native_group'].lower() == 'null')
            for steps in entry['views'].values():
                assert all(step['frame'] in manifest['frames'] for step in steps)
            actions[action] = entry
        by_descriptor[descriptor] = actions
    manifest['animations_by_descriptor'] = by_descriptor
    manifest['playback_authority'] = 'animations_by_descriptor; palette-only views use the first descriptor for that palette'
    manifest['recolor_model'] = materials.CONFIG['operation']
    manifest['recolor'] = materials.CONFIG
    for value in manifest['variants'].values():
        value.pop('luminance_vector', None)
    manifest['limitations'] = ['Fine detail is a faithful reviewed interpretation of native art.',
                              'Physical 2x masters do not imply 2x generated detail in every whole-cycle return.',
                              'The staged native-palette RGB lookup requires its documented recolor operation; gameplay installation is separate.']
    manifest['generated_sampling'] = read(root / 'redo_2x/calibration.json')
    policy = read(out / 'processing.json')['whole_animation_resolution_policy']
    manifest['generated_detail'] = dict(measured_minimum=min(min(row['effective_sampling_xy'])
        for row in registration.values()), below_target_frames=sorted(name for name, row in registration.items()
        if min(row['effective_sampling_xy']) < 2), whole_animation_resolution_policy=policy,
        retained_detail_exceptions={}, physical_export_scale=2)
    manifest['material_module_provenance'] = dict(path=str(module_path.relative_to(REPO)),
        sha256=hashlib.sha256(module_path.read_bytes()).hexdigest())
    if material_review_path.exists():
        manifest['material_review_provenance'] = dict(path=str(material_review_path.relative_to(REPO)),
            sha256=hashlib.sha256(material_review_path.read_bytes()).hexdigest())
    save(out / 'material_settings.json', materials.CONFIG)
    save(out / 'manifest.json', manifest)
    # The freezer compares native playback and placement with this authoritative family snapshot.
    save(root / 'manifest.json', manifest)
    validation = read(out / 'validation.json')
    validation.update(exact_descriptor_bindings_preserved=True,
                      unused_art_excluded_from_playback=True,
                      mandatory_outline_attachments_verified=True,
                      visual_review='Pending artifact-bound full-pose, independent-placement, material, edge and palette/mask review.')
    save(out / 'validation.json', validation)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family')
    export(parser.parse_args().family)
