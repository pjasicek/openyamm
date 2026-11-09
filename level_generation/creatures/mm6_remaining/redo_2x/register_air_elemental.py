"""Candidate Air Elemental placement from reviewed native vortex-core landmarks."""
import hashlib
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

from prepare_run import REPO, native

ROOT = REPO / 'level_generation/creatures/mm6_aie1'
OUT = ROOT / 'redo_2x'
sys.path.insert(0, str(ROOT.parent/'mm6_peasants'))
import process_family as processing

materials = processing.module('air_redo_materials', ROOT/'materials.py')


def points(layout, annotation, side):
    display = layout[side]
    extent = np.array(display['crop'][2:])-display['crop'][:2]
    return ((np.array(annotation[side])-display['display_offset'])*extent/display['display_size']
            + display['crop'][:2])


def main():
    manifest = json.loads((ROOT/'manifest.json').read_text())
    run = json.loads((OUT/'run.json').read_text())
    annotations = json.loads((OUT/'review/anatomy_points.json').read_text())
    layouts = json.loads((OUT/'review/anatomy_annotation_layout.json').read_text())['frames']
    overlaps = json.loads((OUT/'review/overlap_calibration.json').read_text())
    assert overlaps['calibration_policy'] == 'direct_native_core_landmarks'
    assert set(annotations['frames']) == set(manifest['frames'])
    records, calibrations, concerns = {}, {}, []
    warm_curve = np.array(json.loads((ROOT/'recolor_vectors.json').read_text())['198'][1])
    for folder in ['aligned_2x', 'masks_2x']:
        (OUT/folder).mkdir(exist_ok=True)
    for job in run['jobs']:
        report = json.loads((OUT/'review'/(job['id']+'_extraction.json')).read_text())
        assert report['raw'] == job['selected_raw']
        selected = [f for f in report['frames'] if layouts[f['frame']]['job'] == job['id']]
        if not selected:
            continue
        first = selected[0]['frame']
        first_native = points(layouts[first], annotations['frames'][first], 'native')
        first_raw = points(layouts[first], annotations['frames'][first], 'raw')
        sampling = np.linalg.norm(first_raw[2]-first_raw[1])/np.linalg.norm(first_native[2]-first_native[1])
        overlap = None  # Reviewed matching failed; use direct native wind-core calibration.
        calibrations[job['id']] = dict(frame=first, native_points=first_native.tolist(),
            raw_points=first_raw.tolist(), generated_sampling=float(sampling), raw_sha256=report['raw_sha256'],
            method='Manually matched native vortex core extent; one uniform scale for every phase in a sheet',
            status='candidate_requires_sequence_review')
        if overlap:
            calibrations[job['id']]['method'] = 'Uniform scale from visually reviewed shared-pose feature matches'
            calibrations[job['id']]['overlap_evidence'] = overlap
        previews = []
        for frame in selected:
            name = frame['frame']
            annotation, layout = annotations['frames'][name], layouts[name]
            assert annotation['clean_sha256'] == layout['clean_sha256'], 'Re-annotate changed art: '+name
            assert layout['clean_sha256'] == hashlib.sha256((REPO/frame['clean_path']).read_bytes()).hexdigest()
            npnt = points(layout, annotation, 'native')
            rpnt = points(layout, annotation, 'raw')
            measured = np.linalg.norm(rpnt[2]-rpnt[1])/np.linalg.norm(npnt[2]-npnt[1])
            static = False  # All six standing images are animated wind phases, not independent views.
            scale_sampling = measured if static else sampling
            assert scale_sampling > 2, (name, scale_sampling)
            factor = 2/scale_sampling
            clean = Image.open(REPO/frame['clean_path']).convert('RGBA')
            assert frame['matte']['method'] == 'Preserved delivered alpha; no second matte extraction'
            weights = np.array(materials.coverage(clean)).astype(float)/255
            pixels = np.array(clean)
            rgb = pixels[:, :, :3].astype(float)
            warm = weights[:, :, 1, None]
            levels = np.clip(np.round(rgb @ np.array([.2126, .7152, .0722])), 0, 255).astype(int)
            rgb = .84*(rgb*(1-warm)+warm_curve[levels]*255*warm)
            if name.startswith('aie1at'):
                # Native electrical strokes remain pale and legible; the general wind grade dulled them.
                lightning = np.clip((levels.astype(float)-150)/70, 0, 1)*(1-warm[:, :, 0])
                rgb *= 1+lightning[:, :, None]*(1/.84-1)
                pixels[:, :, 3] = np.round(np.minimum(255,
                    pixels[:, :, 3].astype(float)*(1+.35*lightning))).astype(np.uint8)
            pixels[:, :, :3] = np.round(np.clip(rgb, 0, 255)).astype(np.uint8)
            toned = Image.fromarray(pixels)
            size = [round(clean.width*factor), round(clean.height*factor)]
            resized = toned.convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA')
            opacity_gain = 1.0
            if name.startswith(('aie1wi', 'aie1de')):
                native_area = np.array(native(ROOT, name))[:, :, 3].sum(dtype=float)
                restored_area = np.array(resized)[:, :, 3].sum(dtype=float)
                opacity_gain = min(1.0, native_area*4/restored_area)
                alpha = np.array(resized.getchannel('A'), dtype=float)
                resized.putalpha(Image.fromarray(np.round(alpha*opacity_gain).astype(np.uint8)))
            effective_scale = np.array(size)/clean.size
            transformed = rpnt*effective_scale
            translate = np.round(npnt[0]*2-transformed[0]).astype(int)
            box = resized.getbbox()
            origin = np.minimum([0, 0], translate+box[:2]-4)
            end = np.maximum(np.array(manifest['logical_canvas'])*2, translate+box[2:]+4)
            aligned = Image.new('RGBA', tuple(end-origin))
            aligned.paste(resized, tuple(translate-origin))
            aligned.save(OUT/'aligned_2x'/(name+'.png'))
            # Preserve enhanced-art ownership independently of the fixed native tonal grade.
            ungraded = clean.convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA')
            ungraded.putalpha(resized.getchannel('A'))
            material_canvas = Image.new('RGBA', aligned.size)
            material_canvas.paste(ungraded, tuple(translate-origin))
            assert material_canvas.getchannel('A').tobytes() == aligned.getchannel('A').tobytes()
            materials.coverage(material_canvas).save(OUT/'masks_2x'/(name+'.png'))
            core = clean.getchannel('A').point(lambda x: 255 if x >= 32 else 0).getbbox()
            residual = transformed+translate-npnt*2
            discrepancy = float(measured/scale_sampling-1)
            if abs(discrepancy) > .08:
                concerns.append(dict(frame=name, anatomy_scale_difference=discrepancy,
                                     concern='Anatomy scale differs within batch; inspect native motion and overlap'))
            records[name] = dict(batch=job['id'], raw_path=report['raw'], raw_sha256=report['raw_sha256'],
                raw_size=report['raw_size'], raw_rect=frame['raw_rect'], native_crop=report['native_crop'],
                scale=float(factor), effective_sampling_xy=(2/effective_scale).tolist(),
                translate=translate.tolist(), canvas_origin_px=origin.tolist(), native_bounds=frame['native_bounds'],
                placement_landmarks=dict(names=annotation['landmarks'], native=npnt.tolist(), raw=rpnt.tolist(),
                    anchor_index=0, physical_residual=residual[0].tolist(),
                    other_landmark_residual=residual[1:].tolist(),
                    annotation_uncertainty=annotations['uncertainty'], static_view_calibration=static),
                raw_clip=core[0] == 0 or core[1] == 0 or core[2] == clean.width or core[3] == clean.height,
                opacity_gain=opacity_gain, matte=frame['matte'], review_status='pending_sequence_material_and_variant_review')
            previews.append((name, native(ROOT, name), aligned, origin))
        crop = report['native_crop']
        width, height = crop[2]-crop[0], crop[3]-crop[1]
        sheet = Image.new('RGB', (width*len(previews), height*2+44), (42, 44, 43))
        draw = ImageDraw.Draw(sheet)
        for index, (name, source, aligned, origin) in enumerate(previews):
            src = source.crop(crop)
            dst = aligned.crop((crop[0]*2-origin[0], crop[1]*2-origin[1],
                                crop[2]*2-origin[0], crop[3]*2-origin[1]))
            dst = dst.convert('RGBa').resize((width, height), Image.Resampling.LANCZOS).convert('RGBA')
            sheet.paste(src, (index*width, 20), src)
            sheet.paste(dst, (index*width, height+40), dst)
            draw.text((index*width+2, 3), name, fill='white')
        sheet.save(OUT/'review'/(job['id']+'_registered_contact.png'))
    for name, value in [('registration.json', records), ('calibration.json', calibrations),
                         ('review/registration_concerns.json', concerns)]:
        (OUT/name).write_text(json.dumps(value, indent=2)+'\n')
    print(json.dumps(dict(frames=len(records), minimum_sampling=min(min(r['effective_sampling_xy'])
        for r in records.values()), concerns=concerns, status='candidate_not_accepted')))


if __name__ == '__main__':
    main()
