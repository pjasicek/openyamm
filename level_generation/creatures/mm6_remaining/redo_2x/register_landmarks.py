"""Register any staged family from explicit, artifact-bound anatomical points.

Points are in native logical coordinates and cleaned-cell physical coordinates.
One calibration pair sets scale for a whole sheet; only point zero sets translation.
Remaining points are independent review evidence, never optimization targets.
"""
import argparse
import hashlib
import json
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw

from prepare_run import REPO, native as native_frame
from whole_animation_resolution import validate_policy

sys.path.insert(0, str(REPO/'level_generation/creatures/mm6_peasants'))
import process_family
sys.path.insert(0, str(REPO/'level_generation/creatures'))
from local_geometry import deform, transform_points


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def register(project, selected_frames=None):
    root = REPO/project
    out = root/'redo_2x'
    manifest = json.loads((root/'manifest.json').read_text())
    run = json.loads((out/'run.json').read_text())
    annotation = json.loads((out/'review/anatomy_points.json').read_text())
    policy = json.loads((out/'processing.json').read_text())
    resolution_policy = policy.get('whole_animation_resolution_policy')
    validate_policy(resolution_policy, run, manifest)
    config = json.loads((root/'config.json').read_text())
    materials = None
    if policy.get('material_module_override'):
        materials = process_family.module('annotated_materials', out/policy['material_module_override'])
    selected = set(selected_frames) if selected_frames else None
    records = json.loads((out/'registration.json').read_text()) if selected else {}
    calibration = json.loads((out/'calibration.json').read_text()) if selected else {}
    if selected:
        assert selected <= annotation['frames'].keys(), 'Selected frame lacks anatomical annotations'
    for folder in ['aligned_2x', 'masks_2x']:
        (out/folder).mkdir(exist_ok=True)
    for job in run['jobs']:
        chosen = {n: a for n, a in annotation['frames'].items() if a.get('job') == job['id']
                  and (selected is None or n in selected)}
        if not chosen:
            continue
        report = json.loads((out/'review'/(job['id']+'_extraction.json')).read_text())
        assert report['raw'] == job['selected_raw']
        assigned_in_report = set()
        for frame in report['frames']:
            name = frame['frame']
            if name not in chosen:
                continue
            if name in assigned_in_report:
                # A held native bitmap can occur twice in one submitted timeline.
                # Its annotation and runtime tile refer to the first selected occurrence.
                continue
            assigned_in_report.add(name)
            points = chosen[name]
            group = points.get('calibration_group', job['id'])
            specification = annotation['calibration'][group]
            first = specification if 'native' in specification else annotation['frames'][specification['frame']]
            if 'clean_path' in specification:
                assert digest(REPO/specification['clean_path']) == specification['clean_sha256']
            indices = specification['pair']
            native = np.array(first['native'], float)
            raw = np.array(first['raw'], float)
            axes = specification.get('axes', [0, 1])
            assert axes in ([0], [1], [0, 1]), 'Choose explicitly reviewed calibration dimensions'
            sampling = np.linalg.norm((raw[indices[1]]-raw[indices[0]])[axes]) / np.linalg.norm(
                (native[indices[1]]-native[indices[0]])[axes])
            assert sampling > 0 and (resolution_policy or sampling > 2), (group, sampling)
            factor = 2/sampling
            calibration[group] = dict(specification, generated_sampling=float(sampling),
                raw_sha256=report['raw_sha256'], method=annotation['scale_policy'])
            path = REPO/frame['clean_path']
            assert points['clean_sha256'] == digest(path), 'Changed art needs new annotations: '+name
            native, raw = np.array(points['native'], float), np.array(points['raw'], float)
            clean = Image.open(path).convert('RGBA')
            material_parameters = policy.get('material_parameters_by_frame', {}).get(name, {})
            if material_parameters:
                selected_materials = materials or process_family.module(
                    'annotated_family_materials', root/config['material_module'])
                mask = selected_materials.coverage(clean, **material_parameters)
            else:
                mask = materials.coverage(clean) if materials else process_family.mask(clean, config)
            if name in policy.get('protected_material_frames', []):
                mask = Image.new(mask.mode, mask.size)
            coverage = policy.get('material_coverage_polygons', {}).get(name)
            if coverage:
                assert mask.mode == 'L', 'Explicit coverage polygons require a single-region mask'
                assert coverage['clean_sha256'] == digest(path), name
                assert coverage['reason'], 'Explicit material coverage requires a visual-review reason'
                draw = ImageDraw.Draw(mask)
                for polygon in coverage['polygons']:
                    draw.polygon([tuple(point) for point in polygon], fill=255)
                weights = np.array(mask)
                weights[np.array(clean.getchannel('A')) == 0] = 0
                mask = Image.fromarray(weights)
            protected = policy.get('protected_material_polygons', {}).get(name)
            if protected:
                assert protected['clean_sha256'] == digest(path), name
                stencil = Image.new('L', clean.size)
                draw = ImageDraw.Draw(stencil)
                for polygon in protected['polygons']:
                    draw.polygon([tuple(point) for point in polygon], fill=255)
                weights = np.array(mask)
                weights[np.array(stencil) > 0] = 0
                mask = Image.fromarray(weights)
            geometry = None
            correction = policy.get('local_geometry_corrections', {}).get(name)
            geometry_controls = correction.get('control_landmarks', []) if correction else []
            if correction:
                assert correction['clean_sha256'] == digest(path), 'Changed art needs a new geometry edit: '+name
                before = raw.copy()
                clean, mask, geometry = deform(clean, mask, correction)
                raw = transform_points(raw, geometry)
                assert np.linalg.norm(raw[0]-before[0]) < 1e-6, 'Local edit must preserve the registration anchor'
                geometry['clean_sha256'] = correction['clean_sha256']
                geometry['control_landmarks'] = geometry_controls
                geometry['landmarks_before_raw'] = before.tolist()
            pixels = np.array(clean)
            gain = np.array(policy.get('rgb_gain', [1, 1, 1])) * np.array(
                policy.get('frame_rgb_gain', {}).get(name, [1, 1, 1]))
            pixels[:, :, :3] = np.round(np.clip(pixels[:, :, :3].astype(float)*gain,
                0, 255)).astype(np.uint8)
            size = [round(v*factor) for v in clean.size]
            scaled = Image.fromarray(pixels).convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA')
            effective = np.array(size)/clean.size
            generated_sampling = 2/effective
            if geometry:
                generated_sampling /= geometry['maximum_occupied_expansion']
                assert min(generated_sampling) > 0 and (resolution_policy or min(generated_sampling) > 2), (
                    'Local geometry falls below required generated detail', name, generated_sampling.tolist())
            transformed = raw*effective
            translation = np.round(native[0]*2-transformed[0]).astype(int)
            box = scaled.getbbox()
            origin = np.minimum([0, 0], translation+box[:2]-4)
            end = np.maximum(np.array(manifest['logical_canvas'])*2, translation+box[2:]+4)
            aligned = Image.new('RGBA', tuple(end-origin))
            aligned.paste(scaled, tuple(translation-origin))
            aligned.save(out/'aligned_2x'/(name+'.png'))
            # All channels of an RGBA material mask are coverage, including its fourth channel.
            resized_mask = Image.merge(mask.mode, [band.resize(size, Image.Resampling.LANCZOS)
                for band in mask.split()]) if len(mask.getbands()) > 1 else mask.resize(size, Image.Resampling.LANCZOS)
            if len(mask.getbands()) > 1:
                weights = np.array(resized_mask, dtype=float)
                weights *= np.minimum(1, 255/np.maximum(1, weights.sum(axis=2, keepdims=True)))
                resized_mask = Image.fromarray(np.floor(weights).astype(np.uint8))
            weights = np.array(resized_mask)
            weights[np.array(scaled.getchannel('A')) == 0] = 0
            resized_mask = Image.fromarray(weights, mode=mask.mode)
            canvas = Image.new(mask.mode, aligned.size)
            canvas.paste(resized_mask, tuple(translation-origin))
            canvas.save(out/'masks_2x'/(name+'.png'))
            residual = (transformed+translation)/2-native
            core = clean.getchannel('A').point(lambda a: 255 if a >= 32 else 0).getbbox()
            records[name] = dict(batch=job['id'], calibration_group=group, raw_path=report['raw'], raw_sha256=report['raw_sha256'],
                clean_path=frame['clean_path'], clean_sha256=digest(path),
                raw_size=report['raw_size'], raw_rect=frame['raw_rect'], native_crop=report['native_crop'],
                scale=float(factor), effective_sampling_xy=generated_sampling.tolist(), translate=translation.tolist(),
                canvas_origin_px=origin.tolist(), native_bounds=frame['native_bounds'], matte=frame['matte'],
                raw_clip=core[0] == 0 or core[1] == 0 or core[2] == clean.width or core[3] == clean.height,
                review_landmarks={label: dict(native=n.tolist(), restored_before_translation=r.tolist())
                    for label, n, r in zip(points['landmarks'], native, transformed)},
                independent_residual_logical={label: error.tolist()
                    for label, error in zip(points['landmarks'][1:], residual[1:])
                    if label not in points.get('diagnostic_landmarks', []) and label not in geometry_controls},
                diagnostic_residual_logical={label: error.tolist()
                    for label, error in zip(points['landmarks'][1:], residual[1:])
                    if label in points.get('diagnostic_landmarks', [])},
                diagnostic_landmarks=points.get('diagnostic_landmarks', []),
                review_status='candidate_requires_visual_review')
            if geometry:
                records[name]['local_geometry'] = geometry
                records[name]['pre_geometry_effective_sampling_xy'] = (2/effective).tolist()
    old = json.loads((root/'registration.json').read_text()) if annotation.get('retain') else {}
    for name in annotation.get('retain', []):
        if selected is not None and name not in selected:
            continue
        previous = old[name]
        exception = policy.get('retained_detail_exceptions', {}).get(name)
        if 2/previous['scale'] <= 2:
            assert exception and exception.get('user_authorization') and exception.get('reason'), name
        assets = {}
        for folder in ['aligned_2x', 'masks_2x', 'cleaned']:
            relative = f'{folder}/{name}.png'
            shutil.copy2(root/relative, out/relative)
            assets[relative] = digest(root/relative)
        records[name] = dict(previous, effective_sampling_xy=[2/previous['scale']]*2,
            retained_from=dict(project=str(root.relative_to(REPO)),
                registration_sha256=digest(root/'registration.json'), assets=assets))
        if name in policy.get('rebuild_retained_material_masks', []):
            clean = Image.open(out/'cleaned'/(name+'.png')).convert('RGBA')
            selected_materials = materials or process_family.module(
                'retained_family_materials', root/config['material_module'])
            mask = selected_materials.coverage(clean, **policy.get('material_parameters_by_frame', {}).get(name, {}))
            size = [round(v*previous['scale']) for v in clean.size]
            resized = Image.merge(mask.mode, [band.resize(size, Image.Resampling.LANCZOS)
                for band in mask.split()])
            weights = np.array(resized, dtype=float)
            if weights.ndim == 3:
                weights *= np.minimum(1, 255/np.maximum(1, weights.sum(axis=2, keepdims=True)))
            canvas = Image.new(mask.mode, Image.open(out/'aligned_2x'/(name+'.png')).size)
            canvas.paste(Image.fromarray(np.floor(weights).astype(np.uint8)),
                tuple(np.array(previous['translate'])-previous['canvas_origin_px']))
            canvas.save(out/'masks_2x'/(name+'.png'))
            records[name]['retained_mask_rebuild'] = dict(method='Current material coverage on retained cleaned art',
                mask_sha256=digest(out/'masks_2x'/(name+'.png')))
        if exception:
            records[name]['retained_detail_exception'] = exception
        saved = annotation.get('retained_landmarks', {}).get(name)
        if saved:
            assert saved['aligned_sha256'] == assets[f'aligned_2x/{name}.png']
            offset = np.array(previous['canvas_origin_px'])-previous['translate']
            records[name]['review_landmarks'] = {label: dict(native=n,
                restored_before_translation=(np.array(r)+offset).tolist())
                for label, n, r in zip(saved['landmarks'], saved['native'], saved['aligned'])}
    empty = policy.get('native_empty_endpoints', [])
    if empty:
        blank_raw = out/'raw/native_empty_endpoints.png'
        blank_prompt = out/'prompts/native_empty_endpoints.txt'
        blank_raw.parent.mkdir(exist_ok=True)
        blank_prompt.parent.mkdir(exist_ok=True)
        Image.new('RGBA', (1, 1)).save(blank_raw)
        blank_prompt.write_text('Preserve genuinely empty native endpoint frames as transparent pixels; '
                                'there is no visible artwork to generate or reuse.\n')
    for name in empty:
        if selected is not None and name not in selected:
            continue
        assert native_frame(root, name).getbbox() is None, name
        clean = Image.new('RGBA', tuple(manifest['logical_canvas']))
        folder = out/'cleaned/native_empty_endpoints'
        folder.mkdir(parents=True, exist_ok=True)
        clean.save(folder/(name+'.png'))
        canvas = Image.new('RGBA', tuple(np.array(manifest['logical_canvas'])*2))
        canvas.save(out/'aligned_2x'/(name+'.png'))
        mask = process_family.mask(canvas, config)
        mask.save(out/'masks_2x'/(name+'.png'))
        records[name] = dict(batch='native_empty_endpoints', raw_path=str(blank_raw.relative_to(REPO)),
            raw_sha256=digest(blank_raw), scale=1, effective_sampling_xy=[0, 0], translate=[0, 0],
            canvas_origin_px=[0, 0], native_bounds=None, raw_clip=False,
            matte=dict(method='Native source contains no visible pixels'), empty_native_endpoint=True,
            review_landmarks={}, independent_residual_logical={}, review_status='native_empty_endpoint')
    sources = json.loads((root/'sources.json').read_text())
    for name, canonical in sources.get('pixel_aliases', {}).items():
        if selected is not None and name not in selected and canonical not in selected:
            continue
        assert canonical not in sources['pixel_aliases'], 'Native aliases must resolve directly'
        records[name] = dict(records[canonical], generated_frame=canonical, native_pixel_alias=canonical)
        for folder in ['aligned_2x', 'masks_2x']:
            shutil.copy2(out/folder/(canonical+'.png'), out/folder/(name+'.png'))
        if 'retained_from' in records[canonical]:
            shutil.copy2(out/'cleaned'/(canonical+'.png'), out/'cleaned'/(name+'.png'))
    for filename, value in [('registration.json', records), ('calibration.json', calibration)]:
        (out/filename).write_text(json.dumps(value, indent=2)+'\n')
    print(json.dumps(dict(frames=len(records), missing=sorted(set(manifest['frames'])-records.keys()),
        minimum_sampling=min(min(r['effective_sampling_xy']) for r in records.values()
                             if not r.get('empty_native_endpoint')),
        clipped=[n for n, r in records.items() if r['raw_clip']], status='candidate_not_accepted')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project')
    parser.add_argument('--frames', nargs='+', help='Rebuild only these annotated frames and their aliases')
    args = parser.parse_args()
    register(args.project, args.frames)
