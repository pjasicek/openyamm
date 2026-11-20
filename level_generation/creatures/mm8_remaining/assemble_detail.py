"""Assemble reviewed replacement frames using an existing family's material and atlas exporters.

This creates review candidates only. Driver placement review and final acceptance are separate.
"""
import argparse
import importlib
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw

from prepare_detail import REPO, read, save, sampling, sha
from process_detail import composite, edge_candidates


def assemble(args):
    root = REPO / args.project
    out = root / 'redo_2x'
    run = read(out / 'run.json')
    assert sha(root / 'sources.json') == run['source_manifest_sha256']
    previous = root / args.previous_registration
    initial = run.get('initial_restoration', False)
    if not initial:
        assert sha(previous) == run['previous_registration_sha256']
    registration = read(out / 'registration.json')
    old = {} if initial else read(previous)
    assert not initial or not run['retained_frames']
    for filename in ['sources.json', 'batches.json']:
        shutil.copy2(root / filename, out / filename)
    if initial:
        source = read(out / 'sources.json')
        template = (REPO / 'level_generation/creatures/mm8_remaining/viewer_template.html').read_text()
        template = template.replace('__LABEL__', source['label']).replace('__BASE_PALETTE__', str(source['base_palette']))
        template = template.replace('__PALETTE_OPTIONS__', ''.join(
            f'<option value="{palette}">Palette {palette}</option>' for palette in source['palette_sources']))
        (out / 'viewer_template.html').write_text(template)
    else:
        shutil.copy2(root / 'viewer_template.html', out / 'viewer_template.html')
    for folder in [args.master_folder, 'masks_2x', 'cleaned', 'review']:
        (out / folder).mkdir(exist_ok=True)
    if args.package_cleaned_folder:
        (out / args.package_cleaned_folder).mkdir(exist_ok=True)
    for name in run['retained_frames']:
        record = dict(old[name])
        record.update(path=f'{args.master_folder}/{name}.png', cleaned_path=f'cleaned/{name}.png',
                      sampling=sampling(record), retained_from=str(previous.relative_to(REPO)))
        raw = root / 'raw' / record['raw']
        assert raw.is_file(), raw
        record.update(raw=str(raw.relative_to(REPO)), raw_sha256=sha(raw))
        registration[name] = record
        with Image.open(root / args.master_folder / (name + '.png')) as retained:
            assert list(retained.size) == record['aligned_size_px'], 'Retained master needs its active registration'
        shutil.copy2(root / args.master_folder / (name + '.png'), out / record['path'])
        shutil.copy2(root / 'cleaned' / (name + '.png'), out / record['cleaned_path'])
    sources = read(out / 'sources.json')
    assert set(registration) == set(sources['sources']) - set(sources.get('pixel_aliases', {}))
    assert min(sampling(record) for record in registration.values()) >= 2
    for job in run['jobs']:
        assert job.get('selected_raw'), job['id']
        assert sha(REPO / job['references'][0]) == job['reference_sha256']
        if len(job['references']) > 1:
            assert sha(REPO / job['references'][1]) == job['identity_sha256']
        else:
            assert initial and job['scope'] == 'identity', 'Animation sheets require the selected identity'
    for name, record in registration.items():
        target = out / args.master_folder / (name + '.png')
        if target != out / record['path']:
            shutil.copy2(out / record['path'], target)
        clean = out / 'cleaned' / (name + '.png')
        if clean != out / record['cleaned_path']:
            shutil.copy2(out / record['cleaned_path'], clean)
        if args.package_cleaned_folder:
            shutil.copy2(clean, out / args.package_cleaned_folder / (name + '.png'))
    save(out / 'registration.json', registration)
    if args.export_registration != 'registration.json':
        save(out / args.export_registration, registration)
    sys.path.insert(0, str(root))
    package = importlib.import_module('native_package' if initial else 'package')
    package.ROOT = out
    if args.mask_arguments != 'exporter':
        materials = importlib.import_module('native_materials' if initial else 'materials')
        materials.ROOT = out
        if initial:
            materials.PALETTES = [int(palette) for palette in sources['palette_sources']]
        config = getattr(materials, args.config_function)()
        save(out / 'material_settings.json', config)
        if args.mask_arguments in ('image_config', 'image_config_name'):
            (out / 'previews').mkdir(exist_ok=True)
            (out / 'native_variants').mkdir(exist_ok=True)
        if args.material_support:
            support = importlib.import_module('material_support')
            support.ROOT = out
            policy = read(out / 'processing.json').get('material_support', {})
            support_options = {key: policy[key] for key in ('seed_green', 'minimum_area') if key in policy}
            (out / 'material_support_2x').mkdir(exist_ok=True)
        for name in registration:
            im = Image.open(out / args.master_folder / (name + '.png')).convert('RGBA')
            if args.material_support:
                coverage = np.round(support.support(im, name, **support_options) * 255).astype(np.uint8)
                Image.fromarray(coverage).save(out / 'material_support_2x' / (name + '.png'))
            if args.mask_arguments == 'image':
                mask = materials.masks(im)
            elif args.mask_arguments == 'image_config_name':
                mask = materials.masks(im, config, name)
            else:
                mask = materials.masks(im, config)
            assert not mask[np.asarray(im)[:, :, 3] == 0].any(), name
            Image.fromarray(mask).save(out / 'masks_2x' / (name + '.png'))
            if args.mask_arguments in ('image_config', 'image_config_name'):
                for palette in materials.PALETTES:
                    variant = materials.recolor(im, mask, palette, config)
                    assert np.array_equal(np.asarray(im)[:, :, 3], np.asarray(variant)[:, :, 3]), name
                    if int(palette) == int(config['base_palette']):
                        assert np.array_equal(np.asarray(im), np.asarray(variant)), name
                    variant.save(out / 'previews' / f'{name}_{palette}.png')
                    materials.queue.native(out, name, palette).save(out / 'native_variants' / f'{name}_{palette}.png')
    package.run()
    manifest = read(out / 'draft_manifest.json')
    from exact_placement import export_placement, native_offset, validate_manifest
    canvases = {tuple(record['logical_size']) for record in registration.values()}
    assert len(canvases) == 1, 'Different logical canvases need an explicit export contract'
    canvas = list(canvases.pop())
    manifest.update(logical_canvas=canvas, logical_pivot=[canvas[0] / 2, canvas[1]], anchor='bottom-center')
    expanded_registration = {}
    for name, frame in manifest['frames'].items():
        canonical = frame.get('canonical_frame', frame.get('pixel_alias_of', name))
        record = registration[canonical]
        expanded_registration[name] = record
        reference = record.get('native_offset')
        if reference is None:
            assert frame['source_canvas'] == canvas, 'Retained nontrivial placement needs its reference offset'
            reference = native_offset(canvas, frame['source_canvas'])
        exact, origin, correction = export_placement(canvas, frame['source_canvas'], reference,
                                                    record['canvas_origin_px'])
        frame.update(native_offset=exact, registration_native_offset=reference,
                     aligned_canvas_origin_px=origin,
                     crop_origin_px=[origin[k] + frame['crop_in_aligned_px'][k] for k in (0, 1)])
    assert not validate_manifest(manifest, expanded_registration)
    manifest.update(placement_registration=args.export_registration, status='preproduction_review_pending',
                    driver_acceptance=False, installed=False)
    save(out / 'draft_manifest.json', manifest)
    audit = {}
    patches = []
    pages = {i: Image.open(out / page['base']).convert('RGBA') for i, page in enumerate(manifest['pages'])}
    for name, frame in manifest['frames'].items():
        canonical = frame.get('canonical_frame', frame.get('pixel_alias_of', name))
        x, y, width, height = frame['atlas_xywh']
        images = {'cleaned': Image.open(out / 'cleaned' / (canonical + '.png')).convert('RGBA'),
                  'atlas_extracted': pages[frame['page']].crop((x, y, x + width, y + height))}
        audit[name] = {}
        for stage, im in images.items():
            score, _ = edge_candidates(im)
            py, px = np.unravel_index(np.argmax(score), score.shape)
            value = float(score.max())
            audit[name][stage] = dict(maximum=value, position=[int(px), int(py)])
            patches.append((value, name, stage, im.crop((px - 20, py - 20, px + 20, py + 20))))
    save(out / 'review/local_chroma_scan.json', audit)
    patches.sort(key=lambda item: item[0], reverse=True)
    worst = patches[:12]
    contact = Image.new('RGB', (480, len(worst) * 144), (42, 42, 42))
    draw = ImageDraw.Draw(contact)
    for row, (value, name, stage, patch) in enumerate(worst):
        draw.text((4, row * 144 + 4), f'{name} {stage}: {value:.1f}', fill='white')
        for col, bg in enumerate([(20, 20, 20), (235, 235, 235)]):
            contact.paste(composite(patch, bg).resize((120, 120), Image.Resampling.NEAREST),
                          (col * 240, row * 144 + 24))
    contact.save(out / 'review/worst_final_edges.png')
    print('Candidate assembled; inspect variants, all poses and edge contact before preproduction handoff.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project')
    parser.add_argument('--master-folder', required=True)
    parser.add_argument('--previous-registration', default='registration.json')
    parser.add_argument('--export-registration', default='registration.json')
    parser.add_argument('--config-function', choices=['fit', 'settings'], default='settings')
    parser.add_argument('--mask-arguments', choices=['image', 'image_config', 'image_config_name', 'exporter'],
                        default='image_config')
    parser.add_argument('--material-support', action='store_true', help='Use the existing enhanced material support module')
    parser.add_argument('--package-cleaned-folder', help='Existing exporter input folder for cleaned pixels')
    assemble(parser.parse_args())
