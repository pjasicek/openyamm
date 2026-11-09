"""Barbarian head/sole calibration; enhanced-art blade masks; all outputs require visual review."""
import importlib.util
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from prepare_run import REPO, native
from register_archer import contact
sys.path.insert(0, str(REPO / 'level_generation/creatures/mm6_peasants'))
import process_family as processing

ROOT = REPO / 'level_generation/creatures/mm6_bar1'
OUT = ROOT / 'redo_2x'
spec = importlib.util.spec_from_file_location('barbarian_materials', ROOT / 'materials.py')
materials = importlib.util.module_from_spec(spec)
spec.loader.exec_module(materials)
purple = processing.module('purple_matte', ROOT.parent / 'mm6_sor1/process.py')


def crown(image, scale=1):
    a = np.array(image); r, g, b = a[:, :, :3].astype(float).transpose(2, 0, 1)
    # Red hair is above skin, leather and scabbard. Silver sword is excluded by hue.
    hair = (r > g * 1.65) & (r > b * 1.7) & (r > 20) & (a[:, :, 3] >= 128)
    labels, _ = ndimage.label(hair)
    sizes = np.bincount(labels.ravel()); sizes[0] = 0
    viable = sizes >= max(5, 5 * scale * scale)
    viable[0] = False
    yy, xx = np.where(viable[labels])
    assert len(xx), 'Missing Barbarian hair landmark'
    top = int(yy.min())
    cap = hair & (np.arange(image.height)[:, None] < top + max(3, round(8 * scale)))
    labels, _ = ndimage.label(cap); sizes = np.bincount(labels.ravel()); sizes[0] = 0
    yy, xx = np.where(labels == sizes.argmax())
    return [(int(xx.min()) + int(xx.max()) + 1) / 2, top]


def blade_mask(image, name):
    reviewed = json.loads((OUT / 'blade_axes_reviewed.json').read_text())
    a = np.array(image); a[a[:, :, 3] == 0] = 0
    assert hashlib.sha256(a[:, :, 3].tobytes()).hexdigest() == reviewed['alpha_sha256'][name], name
    line = np.array(reviewed['axes'][name])
    start, end = line.reshape(2, 2).astype(float)
    direction = end - start; length = np.linalg.norm(direction); direction /= length
    yy, xx = np.indices((image.height, image.width)); delta = np.stack([xx-start[0], yy-start[1]], axis=2)
    along = delta @ direction
    distance = abs(delta[:, :, 0] * direction[1] - delta[:, :, 1] * direction[0])
    footprint = (along >= -15) & (along <= length + 15) & (distance <= 9)
    weights = np.array(materials.coverage(image))
    weights[footprint, 0] = 0
    return Image.fromarray(weights), line.tolist()


def main():
    config = json.loads((ROOT / 'config.json').read_text())
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    records, calibrations, axes = {}, {}, {}
    for folder in ['aligned_2x', 'masks_2x']:
        (OUT / folder).mkdir(exist_ok=True)
    for path in sorted((OUT / 'review').glob('*_extraction.json')):
        report = json.loads(path.read_text()); first = report['frames'][0]
        first_native = native(ROOT, first['frame'])
        first_raw = Image.open(REPO / first['clean_path']).convert('RGBA')
        nc, gc = crown(first_native), crown(first_raw, 2.5)
        nf, gf = contact(first_native, 6), contact(first_raw, 15)
        sampling = (gf[1] - gc[1]) / (nf[1] - nc[1]); factor = 2 / sampling
        assert sampling > 2, (report['job'], sampling)
        calibrations[report['job']] = dict(frame=first['frame'], native_crown=nc, raw_crown=gc,
            native_contact=nf, raw_contact=gf, generated_sampling=sampling, raw_sha256=report['raw_sha256'],
            method='First-pose red-hair crown to sole; exclude blade; one uniform scale for the entire batch')
        previews = []
        for f in report['frames']:
            name = f['frame']
            if name in records:
                continue
            clean = Image.open(REPO / f['clean_path']).convert('RGBA')
            source = native(ROOT, name)
            # Standing consists of independent static stored views, not a time sequence.
            # Calibrate each camera's anatomy explicitly; never normalize animated poses this way.
            if report['job'].startswith('standing_'):
                nh, rh = crown(source), crown(clean, 2.5)
                nf, rf = contact(source, 6), contact(clean, 15)
                sampling = (rf[1] - rh[1]) / (nf[1] - nh[1])
                factor = 2 / sampling
                assert sampling > 2, name
                calibrations[report['job']].setdefault('static_view_calibrations', {})[name] = dict(
                    native_crown=nh, raw_crown=rh, native_contact=nf, raw_contact=rf,
                    generated_sampling=sampling)
            # Local matte recovery already preserved intended purple leather; a global chroma clamp destroys it.
            im = clean.convert('RGBa').resize((round(clean.width * factor), round(clean.height * factor)),
                                             Image.Resampling.LANCZOS).convert('RGBA')
            nc, rc = contact(source, 6), contact(im, 12)
            nh, rh = crown(source), crown(im, 2)
            tx, ty = round(nh[0] * 2 - rh[0]), round(nc[1] * 2 - rc[1])
            box = im.getbbox()
            origin = [min(0, tx+box[0]-4), min(0, ty+box[1]-4)]
            end = [max(manifest['logical_canvas'][0]*2, tx+box[2]+4),
                   max(manifest['logical_canvas'][1]*2, ty+box[3]+4)]
            aligned = Image.new('RGBA', (end[0]-origin[0], end[1]-origin[1]))
            aligned.paste(im, (tx-origin[0], ty-origin[1]))
            aligned = purple.contour(aligned, 'magenta')
            aligned.save(OUT/'aligned_2x'/(name+'.png'))
            mask, axis = blade_mask(aligned, name); mask.save(OUT/'masks_2x'/(name+'.png')); axes[name] = axis
            effective = [2*clean.width/im.width, 2*clean.height/im.height]
            assert min(effective) > 2
            records[name] = dict(batch=report['job'], raw_path=report['raw'], raw_sha256=report['raw_sha256'],
                raw_size=report['raw_size'], raw_rect=f['raw_rect'], native_crop=report['native_crop'],
                scale=factor, effective_sampling_xy=effective, translate=[tx, ty], canvas_origin_px=origin,
                native_bounds=f['native_bounds'],
                placement_landmarks=dict(native_contact=nc, restored_contact_before_translation=rc,
                    native_crown=nh, restored_crown_before_translation=rh,
                    physical_residual=[rh[0]+tx-nh[0]*2, rc[1]+ty-nc[1]*2],
                    crown_y_residual=rh[1]+ty-nh[1]*2, stance_center_x_residual=rc[0]+tx-nc[0]*2),
                raw_clip=f['clean_bounds'][0] <= 0 or f['clean_bounds'][1] <= 0
                    or f['clean_bounds'][2] >= clean.width or f['clean_bounds'][3] >= clean.height,
                matte=f['matte'], review_status='pending_animation_landmark_and_material_review')
            previews.append((name, source, aligned, origin))
        crop = report['native_crop']; w, h = crop[2]-crop[0], crop[3]-crop[1]
        if previews:
            sheet = Image.new('RGB', (w*len(previews), h*2+44), (42,44,43)); draw = ImageDraw.Draw(sheet)
            for i, (name, source, aligned, origin) in enumerate(previews):
                src = source.crop(crop)
                dst = aligned.crop((crop[0]*2-origin[0], crop[1]*2-origin[1],
                                    crop[2]*2-origin[0], crop[3]*2-origin[1]))
                dst = dst.convert('RGBa').resize((w,h), Image.Resampling.LANCZOS).convert('RGBA')
                sheet.paste(src,(i*w,20),src); sheet.paste(dst,(i*w,h+40),dst)
                draw.text((i*w+2,3),name,fill='white')
            sheet.save(OUT/'review'/(report['job']+'_registered_contact.png'))
    assert set(records) == set(manifest['frames'])
    for name, data in [('registration.json',records), ('calibration.json',calibrations), ('blade_axes_candidates.json',axes)]:
        (OUT/name).write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(dict(frames=len(records), minimum_sampling=min(min(r['effective_sampling_xy']) for r in records.values()),
                         status='candidate registration; review required')))


if __name__ == '__main__':
    main()
