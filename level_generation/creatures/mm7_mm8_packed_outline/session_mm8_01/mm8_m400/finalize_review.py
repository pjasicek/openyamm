"""Prepare MM8 exports for the existing reviewer; freeze only hash-matched visual evidence."""
import argparse
import copy
from datetime import datetime, timezone
import importlib.util
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from session import REPO, SESSION, CREATURES, CONTEXT, ROLES, native_2x, read, save, sha, rel


def viewer_module():
    path = CREATURES / 'mm6_remaining/acceptance_viewer/serve.py'
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location('session_existing_reviewer', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def prepare(stem):
    root = SESSION / ('mm8_' + stem)
    out = root / 'redo_2x'
    manifest = read(out / 'draft_manifest.json')
    assert not manifest['missing_frames']
    sources = read(root / 'sources.json')
    settings = read(out / 'material_settings.json')
    if stem == 'm400':
        # Describe the existing m400 two-region colour fit exactly. This is
        # export metadata for already-reviewed pixels, not a new recolour.
        assert settings['base_palette'] == 401
        assert settings['regions'] == ['green garment panels', 'warm trim, belt and apron bands']
        assert all(len(coefficients) == 2 for coefficients in settings['palettes'].values())
        settings['operation'] = 'two_region_luminance_rgb_affine'
        settings['luminance_rgb_weights'] = [0.2126, 0.7152, 0.0722]
        settings['mask_channels'] = dict(mask_r=settings['regions'][0], mask_g=settings['regions'][1],
                                         mask_b='unused; zero')
        settings['equation'] = ('Base palette 401 bypasses exactly. Otherwise normalized sRGB c and '
            'linear mask coverages w_r,w_g produce c*(1-w_r-w_g) + '
            'sum_k(w_k*clip((c dot luminance_rgb_weights)*slope_k+intercept_k,0,1)); '
            'round clipped RGB to uint8 and preserve alpha exactly.')
        save(out / 'material_settings.json', settings)
    records = read(out / 'registration.json')
    palettes = sorted(map(int, sources['palette_sources']))
    (out / 'native_variants').mkdir(exist_ok=True)
    manifest['material_settings'] = 'material_settings.json'
    manifest['material_settings_sha256'] = sha(out / 'material_settings.json')
    manifest['variants'] = {str(p): dict(name=f'Native palette {p}', palette_id=p,
        exact_base_bypass=p == sources['base_palette'], operation=settings['operation'],
        settings='material_settings.json') for p in palettes}
    manifest['regions'] = (settings['mask_channels'] if stem == 'm400'
                           else {'mask_r': ', '.join(settings['regions'])})
    manifest['animations_by_palette'] = {}
    manifest['review_descriptor_by_palette'] = {}
    # The complete descriptor-indexed animations remain authoritative. The viewer
    # uses one representative descriptor for each palette and omits no-image steps.
    for descriptor, actor in sources['bindings'].items():
        steps = actor['actions']['walk']['views']['0']
        palette = str(steps[0]['palette'])
        if palette in manifest['animations_by_palette']:
            continue
        actions = copy.deepcopy(actor['actions'])
        for action in actions.values():
            for view, sequence in action['views'].items():
                action['views'][view] = [dict(step, native_scale=step['scale']) for step in sequence
                                        if step['frame'] is not None]
        manifest['animations_by_palette'][palette] = actions
        manifest['review_descriptor_by_palette'][palette] = descriptor
    assert set(manifest['animations_by_palette']) == set(manifest['variants'])
    for name in manifest['frames']:
        for palette in palettes:
            native, _ = native_2x(sources['sources'][name], sources, palette)
            native.save(out / 'native_variants' / f'{name}_{palette}.png')
    for page_index, page in enumerate(manifest['pages']):
        page['variant_previews'] = {}
        for palette in palettes:
            image = Image.open(out / page['base']).convert('RGBA')
            if palette != sources['base_palette']:
                for name, frame in manifest['frames'].items():
                    if frame['page'] != page_index or 'pixel_alias_of' in frame:
                        continue
                    tile = Image.open(out / 'previews' / f'{name}_{palette}.png').convert('RGBA')
                    tile = tile.crop(frame['crop_in_aligned_px'])
                    image.paste(tile, frame['atlas_xywh'][:2])
            path = out / 'atlas' / f'preview_{page_index}_{palette}.png'
            image.save(path)
            page['variant_previews'][str(palette)] = str(path.relative_to(out))
    values = [min(record['effective_sampling_xy']) for record in records.values()]
    manifest['generated_detail'] = dict(measured_minimum=min(values), measured_maximum=max(values),
        physical_export_tier=2, sampling_method='actual raw-to-export anatomical registration including rounding',
        below_2x_frames=sorted(name for name, r in records.items() if min(r['effective_sampling_xy']) < 2),
        whole_cycle_priority=True, interpolation_is_not_new_detail=True)
    manifest['review_label'] = sources['label']
    if stem == 'm400':
        manifest['unbound_native_palette_archive'] = read(
            out / 'review/unused_quadruped_native_data.json')['archived_unbound_palette']
    manifest['quality_status'] = 'visual review pending'
    save(out / 'manifest.json', manifest)
    sys.path.insert(0, str(CREATURES / 'mm6_peasants'))
    from package_family import edge_stats
    ranked = []
    boundaries = []
    run = read(out / 'run.json')
    for job in run['jobs']:
        raw = Image.open(REPO / job['selected_raw']).convert('RGBA')
        alpha = np.asarray(raw.getchannel('A'))
        border = np.concatenate([alpha[0], alpha[-1], alpha[:, 0], alpha[:, -1]])
        boundaries.append(dict(job=job['id'], raw=job['selected_raw'], sha256=sha(REPO / job['selected_raw']),
            maximum_alpha=int(border.max()), pixels_alpha_at_least_128=int((border >= 128).sum())))
    for name, frame in manifest['frames'].items():
        page = manifest['pages'][frame['page']]
        x, y, w, h = frame['atlas_xywh']
        image = Image.open(out / page['base']).crop((x, y, x + w, y + h)).convert('RGBA')
        stats = edge_stats(image, read(root / 'config.json')['matte'])
        ranked.append((stats['max_score'], name, image, stats))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    panel = Image.new('RGB', (1280, 1600), '#262a28')
    draw = ImageDraw.Draw(panel)
    samples = []
    for index, (_, name, image, stats) in enumerate(ranked[:20]):
        cx, cy = map(round, stats['position'])
        box = [cx - 64, cy - 64, cx + 64, cy + 64]
        patch = image.crop(box)
        bx, by = (index % 5) * 256, (index // 5) * 400
        for side, background in enumerate(['#262a28', '#eee9df']):
            composite = Image.new('RGBA', (128, 128), background)
            composite.alpha_composite(patch)
            panel.paste(composite, (bx + side * 128, by + 20))
        draw.text((bx, by), name + ' final atlas edge 100%', fill='white')
        samples.append(dict(frame=name, atlas=manifest['pages'][manifest['frames'][name]['page']]['base'],
            stats=stats, crop=box, pixel_scale=1))
    edge_path = out / 'review' / 'final_atlas_edges_100pct.png'
    panel.save(edge_path)
    save(out / 'review' / 'final_atlas_edges.json', dict(samples=samples, page=rel(edge_path),
        sha256=sha(edge_path), boundaries=boundaries, reviewed=False))
    print(dict(family=stem, viewer_manifest=rel(out / 'manifest.json'), minimum_sampling=min(values),
        solid_boundary_contacts=[b['job'] for b in boundaries if b['pixels_alpha_at_least_128']]))


def freeze(stem, note):
    root = SESSION / ('mm8_' + stem)
    out = root / 'redo_2x'
    observed = read(out / 'review' / 'manual_observations.json')['artifacts']
    categories = {'all_pose_detail_100pct_*.png': 'delivered_detail_alpha_100_percent',
        'final_atlas_edges_100pct.png': 'final_atlas_edges_100_percent'}
    required = []
    placement_report = read(out / 'review' / 'complete_placement.json')
    required += [(out / p, 'native_1x_independent_placement') for p in placement_report['pages']]
    for pattern, category in categories.items():
        for path in sorted((out / 'review').glob(pattern)):
            required.append((path, category))
    palette_report = read(out / 'review' / 'all_palette_mask_poses.json')
    required += [(REPO / p['path'], 'all_native_palettes_and_masks') for p in palette_report['pages']]
    for path, category in required:
        assert any(a['sha256'] == sha(path) and a['category'] == category and a['reviewed']
                   for a in observed), f'Unreviewed current artifact: {path}'
    manifest = read(out / 'manifest.json')
    checks = read(out / 'review' / 'export_checks.json')
    assert checks['full_coverage'] and not manifest['missing_frames']
    run = read(out / 'run.json')
    protocol = []
    for job in run['jobs']:
        attempt = next(a for a in reversed(job['attempts']) if a.get('raw') == job['selected_raw'])
        args = attempt['actual_tool_arguments']
        inputs = attempt['actual_submitted_inputs']
        assert args['prompt'].startswith(CONTEXT)
        assert len(inputs) == 3 and [i['role'] for i in inputs] == ROLES
        assert args['referenced_image_paths'] == [i['path'] for i in inputs]
        assert all(sha(Path(i['path'])) == i['sha256'] for i in inputs)
        assert sha(REPO / attempt['raw']) == attempt['sha256']
        assert not attempt.get('visual_review', {}).get('status') == 'rejected'
        protocol.append(dict(job=job['id'], raw=attempt['raw'], sha256=attempt['sha256'], inputs=inputs))
        attempt['status'] = 'accepted'
        job['status'] = 'accepted'
    run['status'] = 'complete_local_accepted'
    save(out / 'run.json', run)
    settings = read(out / 'material_settings.json')
    settings['visual_acceptance'] = True
    save(out / 'material_settings.json', settings)
    manifest['material_settings_sha256'] = sha(out / 'material_settings.json')
    manifest.update(status='accepted', quality_status='accepted', visual_acceptance=True, installed=False)
    save(out / 'manifest.json', manifest)
    checks['visual_review_complete'] = True
    save(out / 'validation.json', checks)
    reviewer = viewer_module()
    family = reviewer.load_family(manifest['label'], out / 'manifest.json', 'MM8 packed outline session', 'accepted')
    state = root / 'acceptance_state'
    state.mkdir(exist_ok=True)
    checkpoint = reviewer.Checkpoints(state / 'frame_fixups.json').get(family)
    decision = dict(decision='accepted', note=note, updated_at=datetime.now(timezone.utc).isoformat(),
        viewer_revision=reviewer.VIEWER_REVISION, manifest_sha256=family.manifest_sha256,
        artifact_sha256=family.artifact_sha256, fixups_revision=checkpoint['revision'],
        fixups_snapshot=checkpoint['frames'], guides_snapshot=checkpoint.get('guides'),
        colors_snapshot=checkpoint.get('colors', {}), preview_fixups=False, preview_scale=False)
    reviewer.save_decisions(dict(schema_version=1, decisions={family.id: {family.artifact_sha256: decision}}),
                            state / 'decisions.json')
    paths = [out / name for name in ['manifest.json', 'run.json', 'registration.json', 'processing.json',
        'material_settings.json', 'validation.json', 'review/manual_observations.json']] + [root / 'sources.json']
    paths += [out / folder / f'{name}.png' for folder in ['aligned_2x', 'masks_2x', 'runtime_aligned_2x',
        'runtime_masks_2x', 'trimmed_2x', 'trimmed_masks_2x'] for name in manifest['frames']
        if (out / folder / f'{name}.png').exists()]
    if stem == 'm400':
        paths += [out / 'review/unused_quadruped_native_data.json', out / 'native_palette_archive/pal400.act']
    save(out / 'review' / 'acceptance.json', dict(status='accepted', reviewed_utc=decision['updated_at'],
        review_mode='static_contacts', method=run['method'], reviewed_frames=sorted(manifest['frames']),
        coverage=dict(native_frames=len(manifest['frames']), complete_animation_view_jobs=len(protocol),
            palettes=run['palette_ids'], descriptor_ids=run['descriptor_ids'], retained_frames=0),
        checks=dict(faithful_detail=True, poses_and_placement=True, edges_and_alpha=True,
            masks_and_variants=True, attached_outline_every_selected_call=True, watched_playback=False),
        placement_notes=note, limitations='Static sequence review; timed playback not watched. Offline export; not installed.',
        generated_detail=manifest['generated_detail'], submitted_protocol=protocol,
        artifact_hashes={rel(p): sha(p) for p in paths}, reviewer_decision=rel(state / 'decisions.json'),
        reviewer_artifact_sha256=family.artifact_sha256,
        visually_viewed_artifacts=[dict(path=rel(p), sha256=sha(p), category=c) for p, c in required]))
    print(dict(family=stem, accepted_frames=len(manifest['frames']), jobs=len(protocol),
        palettes=run['palette_ids'], minimum_sampling=family.minimum_sampling, installed=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'freeze'])
    parser.add_argument('--family', required=True)
    parser.add_argument('--note', default='')
    args = parser.parse_args()
    prepare(args.family) if args.operation == 'prepare' else freeze(args.family, args.note)
