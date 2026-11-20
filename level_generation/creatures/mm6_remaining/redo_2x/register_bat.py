"""Candidate Bat registration from explicit anatomical annotations, never silhouette fitting."""
import hashlib
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

from prepare_run import REPO, native

ROOT = REPO / 'level_generation/creatures/mm6_bat'
OUT = ROOT / 'redo_2x'
sys.path.insert(0, str(ROOT.parent / 'mm6_peasants'))
import process_family as processing

materials = processing.module('bat_redo_materials', ROOT / 'materials.py')
purple = processing.module('bat_redo_contour', ROOT.parent / 'mm6_sor1/process.py')


def anatomical_points(layout, annotation, side):
    display = layout[side]
    extent = np.array(display['crop'][2:]) - display['crop'][:2]
    return ((np.array(annotation[side]) - display['display_offset']) * extent / display['display_size']
            + display['crop'][:2])


def wing_gains(name):
    if name.startswith('batwa'):
        pose, view = name[5], int(name[-1])
        if view == 0:
            return dict(a=(.32, 1), b=(.4, 1), c=(.4, 1), d=(1, .3), e=(.65, .9), f=(.6, .85))[pose]
        if view == 3:
            return .48, .48
        if view == 4:
            return dict(a=(.28, .35), b=(.32, .4), c=(.3, .6), d=(.3, 1), e=(.7, .7), f=(.65, .65))[pose]
    if name.startswith('batat'):
        return .38, .95
    if name.startswith('batwi'):
        return dict(a=(.32, 1), b=(1, .55), c=(1.05, .75), d=(.4, 1), e=(1, .45), f=(.55, .35))[name[5]]
    return 1, 1


def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    run = json.loads((OUT / 'run.json').read_text())
    annotations = json.loads((OUT / 'review/anatomy_points.json').read_text())
    layouts = json.loads((OUT / 'review/anatomy_annotation_layout.json').read_text())['frames']
    overlap_review = json.loads((OUT / 'review/attack_overlap_calibration.json').read_text())
    assert overlap_review['status'] == 'correspondences_visually_reviewed'
    assert set(annotations['frames']) == set(manifest['frames'])
    records, calibrations, concerns = {}, {}, []
    for folder in ['aligned_2x', 'masks_2x']:
        (OUT / folder).mkdir(exist_ok=True)
    for job in run['jobs']:
        report = json.loads((OUT / 'review' / (job['id'] + '_extraction.json')).read_text())
        assert report['raw'] == job['selected_raw']
        selected = [f for f in report['frames'] if layouts[f['frame']]['job'] == job['id']]
        if not selected:
            continue
        first = selected[0]['frame']
        calibration_annotation = annotations['frames'][first].get('calibration_override', annotations['frames'][first])
        first_native = anatomical_points(layouts[first], calibration_annotation, 'native')
        first_raw = anatomical_points(layouts[first], calibration_annotation, 'raw')
        sampling = np.linalg.norm(first_raw[1] - first_raw[0]) / np.linalg.norm(first_native[1] - first_native[0])
        overlap = overlap_review['records'].get(job['id'])
        if overlap:
            for path, digest in zip(overlap['paths'], overlap['cleaned_sha256']):
                assert hashlib.sha256((REPO / path).read_bytes()).hexdigest() == digest
            sampling = calibrations[overlap['previous_job']]['generated_sampling'] * overlap['scale_ratio']
        calibrations[job['id']] = dict(frame=first, native_points=first_native.tolist(),
            raw_points=first_raw.tolist(), generated_sampling=float(sampling), raw_sha256=report['raw_sha256'],
            method=calibration_annotation.get('method',
                'Matched head/torso to feet or pelvis; common scale for animated batch, translation per native pose'),
            status='candidate_requires_motion_review')
        if overlap:
            calibrations[job['id']]['method'] = 'Uniform scale propagated through visually checked native overlap poses'
            calibrations[job['id']]['overlap_evidence'] = overlap
        previews = []
        for frame in selected:
            name = frame['frame']
            annotation, layout = annotations['frames'][name], layouts[name]
            assert annotation['clean_sha256'] == layout['clean_sha256'], 'Re-annotate changed artwork: ' + name
            assert layout['clean_sha256'] == hashlib.sha256((REPO / frame['clean_path']).read_bytes()).hexdigest()
            npnt = anatomical_points(layout, annotation, 'native')
            rpnt = anatomical_points(layout, annotation, 'raw')
            measured = np.linalg.norm(rpnt[1] - rpnt[0]) / np.linalg.norm(npnt[1] - npnt[0])
            # These are independent stored camera poses with no native animation binding for the drafts.
            static = job['id'].startswith(('standing_', 'unused_native_'))
            scale_sampling = measured if static else sampling
            assert scale_sampling > 2, (name, scale_sampling)
            factor = 2 / scale_sampling
            clean = Image.open(REPO / frame['clean_path']).convert('RGBA')
            # Preserve actual supplied alpha; contour recovery only applies to historical keyed inputs.
            supplied = frame['matte'].get('method') == 'Preserved delivered alpha; no second matte extraction'
            if not supplied:
                clean = purple.contour(clean, 'magenta')
            weights = np.array(materials.coverage(clean)).astype(float) / 255
            left, right = wing_gains(name)
            middle = rpnt[0, 0]
            blend = np.clip((np.arange(clean.width) - middle) / (8 * scale_sampling) + .5, 0, 1)
            gain = .82 * (1 - weights + weights * (left * (1 - blend) + right * blend)[None, :])
            a = np.array(clean)
            a[:, :, :3] = np.round(np.clip(a[:, :, :3].astype(float) * gain[:, :, None], 0, 255)).astype(np.uint8)
            toned = Image.fromarray(a)
            size = [round(clean.width * factor), round(clean.height * factor)]
            resized = toned.convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA')
            effective_scale = np.array(size) / clean.size
            transformed = rpnt * effective_scale
            anchor_index = annotation.get('anchor_index', 0)
            translate = np.round(npnt[anchor_index] * 2 - transformed[anchor_index]).astype(int)
            box = resized.getbbox()
            origin = np.minimum([0, 0], translate + box[:2] - 4)
            end = np.maximum(np.array(manifest['logical_canvas']) * 2, translate + box[2:] + 4)
            aligned = Image.new('RGBA', tuple(end - origin))
            aligned.paste(resized, tuple(translate - origin))
            aligned.save(OUT / 'aligned_2x' / (name + '.png'))
            materials.coverage(aligned).save(OUT / 'masks_2x' / (name + '.png'))
            core_box = clean.getchannel('A').point(lambda x: 255 if x >= 32 else 0).getbbox()
            residual = transformed + translate - npnt * 2
            discrepancy = float(measured / scale_sampling - 1)
            if abs(discrepancy) > .15 or annotation.get('review_concern'):
                concerns.append(dict(frame=name, anatomy_scale_difference=discrepancy,
                                     concern=annotation.get('review_concern', 'Body length differs within batch')))
            effective = (2 / effective_scale).tolist()
            records[name] = dict(batch=job['id'], raw_path=report['raw'], raw_sha256=report['raw_sha256'],
                raw_size=report['raw_size'], raw_rect=frame['raw_rect'], native_crop=report['native_crop'],
                scale=float(factor), effective_sampling_xy=effective, translate=translate.tolist(),
                canvas_origin_px=origin.tolist(), native_bounds=frame['native_bounds'],
                placement_landmarks=dict(names=annotation['landmarks'], native=npnt.tolist(), raw=rpnt.tolist(),
                    anchor_index=anchor_index, physical_residual=residual[anchor_index].tolist(),
                    other_landmark_residual=residual[1-anchor_index].tolist(),
                    annotation_uncertainty=annotations['uncertainty'], static_view_calibration=static),
                raw_clip=core_box[0] == 0 or core_box[1] == 0 or core_box[2] == clean.width
                         or core_box[3] == clean.height,
                matte=frame['matte'], review_status='pending_animation_landmark_and_material_review')
            previews.append((name, native(ROOT, name), aligned, origin))
        crop = report['native_crop']
        w, h = crop[2] - crop[0], crop[3] - crop[1]
        sheet = Image.new('RGB', (w * len(previews), h * 2 + 44), (42, 44, 43))
        draw = ImageDraw.Draw(sheet)
        for index, (name, source, aligned, origin) in enumerate(previews):
            src = source.crop(crop)
            dst = aligned.crop((crop[0]*2-origin[0], crop[1]*2-origin[1],
                                crop[2]*2-origin[0], crop[3]*2-origin[1]))
            dst = dst.convert('RGBa').resize((w, h), Image.Resampling.LANCZOS).convert('RGBA')
            sheet.paste(src, (index*w, 20), src)
            sheet.paste(dst, (index*w, h+40), dst)
            draw.text((index*w+2, 3), name, fill='white')
        sheet.save(OUT / 'review' / (job['id'] + '_registered_contact.png'))
    for filename, value in [('registration.json', records), ('calibration.json', calibrations),
                            ('review/registration_concerns.json', concerns)]:
        (OUT / filename).write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(dict(frames=len(records), minimum_sampling=min(min(r['effective_sampling_xy'])
        for r in records.values()), concerns=concerns, status='candidate_only_not_accepted')))


if __name__ == '__main__':
    main()
