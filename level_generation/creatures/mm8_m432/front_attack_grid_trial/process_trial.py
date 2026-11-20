"""Register compact sequence grids with a shared scale and row translations; export a review trial."""
from pathlib import Path
import json
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.optimize import minimize

T = Path(__file__).resolve().parent
sys.path.insert(0, str(T.parent))
import process, calibrate, tone


def contact(images, labels, path, columns=4, size=288):
    rows = (len(images) + columns - 1) // columns
    out = Image.new('RGB', (columns*size, rows*(size+24)), (35, 35, 35))
    draw = ImageDraw.Draw(out)
    for i, (im, label) in enumerate(zip(images, labels)):
        bg = Image.new('RGBA', im.size, (35, 35, 35, 255))
        bg.alpha_composite(im.convert('RGBA'))
        x, y = i % columns*size, i // columns*(size+24)
        out.paste(bg.resize((size, size), Image.Resampling.LANCZOS).convert('RGB'), (x, y+24))
        draw.text((x+4, y+5), label, fill='white')
    out.save(path)


def grade(im, native, name):
    a, n = np.array(im), np.array(native)
    rgb, alpha = a[:, :, :3].astype(float), a[:, :, 3]/255
    c = tone.field(n[:, :, :3].astype(float), n[:, :, 3]/255) + .7*(rgb-tone.field(rgb, alpha))
    a[:, :, :3] = np.round(c).clip(0, 255).astype(np.uint8)
    return process.fix(Image.fromarray(a), name)


def run():
    data = json.loads((T/'sequence_jobs.json').read_text())
    records, arts, natives = [], [], []
    for j, (key, job) in enumerate(data['jobs'].items()):
        raw_path = T/job.get('selected_raw', 'raw/'+key+'_v1.png')
        raw = Image.open(raw_path)
        cw, ch = raw.width/3, raw.height/2
        assert abs(cw/ch-1) < .003
        job['actual_size'] = list(raw.size)
        job['generated_pixels_per_native_pixel_before_registration'] = cw/232
        job['selected_raw'] = str(raw_path.relative_to(T))
        job['raw_sha256'] = process.queue.sha(raw_path)
        job['prompt_sha256'] = process.queue.sha(T/job['prompt'])
        job['reference_sha256'] = process.queue.sha(T/job['reference'])
        for folder in ['cleaned', 'registered_2x', 'toned_2x']:
            (T/folder/key).mkdir(parents=True, exist_ok=True)
        for i, name in enumerate(job['frames']):
            rect = [round(i%3*cw), round(i//3*ch), round((i%3+1)*cw), round((i//3+1)*ch)]
            nominal_origin = rect[:2]
            # Raw inspection: top-row start soles extend into the empty row gap;
            # end af0 tip crosses a column line, ah0 tip crosses the row line.
            # Move extraction cuts through empty space, preserving raw coordinates.
            if key.endswith('start') and i < 3:
                rect[3] += 8
            if key.endswith('end') and name == 'm432af0':
                rect[2] += 8
            if key.endswith('end') and name == 'm432ah0':
                rect[1] -= 8
            clean = process.extract(raw.crop(rect), name)
            bb = clean.getchannel('A').getbbox()
            assert bb and bb[0]>0 and bb[1]>0 and bb[2]<clean.width and bb[3]<clean.height, (key, name, bb)
            clean.save(T/'cleaned'/key/(name+'.png'))
            canvas = Image.new('RGBA', (576, 576))
            ratio = 464/cw
            size = (round(clean.width*ratio), round(clean.height*ratio))
            offset = (88+round((rect[0]-nominal_origin[0])*ratio),
                      92+round((rect[1]-nominal_origin[1])*ratio))
            canvas.paste(clean.convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA'), offset)
            native = Image.new('RGBA', (576, 576))
            native.paste(process.queue.native(process.ROOT, name).resize((512, 512), Image.Resampling.NEAREST), (32, 32))
            arts.append(canvas)
            natives.append(native)
            records.append({'frame': name, 'job': key, 'row_group': j*2+i//3, 'raw_cell': rect,
                            'raw_visible_bbox': bb, 'sampling_before_registration': cw/232})
    masks, targets = [calibrate.body(a) for a in arts], [calibrate.body(n) for n in natives]

    def objective(v):
        num = den = 0
        for rec, a, b in zip(records, masks, targets):
            g = rec['row_group']
            w = calibrate.warp(a, [v[0], v[1+2*g], v[2+2*g]])
            num += 2*(w*b).sum()
            den += (w*w+b*b).sum()
        return 1-num/den + .02*(v[0]-1)**2

    settings_path = T/'processing_settings.json'
    previous = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    values = previous.get('frozen_calibration')
    if values is None:
        values = minimize(objective, [1, 0, 0, 0, 12, 0, 0, 0, 0], method='Powell',
                          bounds=[(.8, 1.08)]+[(-20, 20)]*8,
                          options={'maxiter': 60, 'xtol': .0001}).x.tolist()
    settings = {'runtime_scale': 2, 'canvas_size': [576, 576], 'canvas_origin_px': [-32, -32],
                'native_logical_size': [256, 256], 'native_pivot': [128, 256],
                'shared_crop_xyxy': [28, 30, 260, 262], 'calibration': values,
                'registration': 'One isotropic scale for BOTH sheets; one shared XY translation per row of three poses. No per-frame fits.',
                'row_drift_reason': 'Start sheet top feet at raw y510, lower feet at local y446 despite common native y226. Correct sheet row placement.',
                'objective_before': objective([1]+[0]*8), 'objective_after': objective(values),
                'tone': 'native coarse RGB + 0.7*(generated RGB - generated coarse RGB), alpha-normalized Gaussian sigma7 at 2x',
                'matte': 'Native-aware local magenta unmix and RGB-only edge repair from ../process.py',
                'state': 'processed_unreviewed'}
    if 'frozen_calibration' in previous:
        settings['frozen_calibration'] = values
    process.save(settings_path, settings)
    pictures, labels, selected = [], [], {}
    for rec, art, native, target, mask in zip(records, arts, natives, targets, masks):
        name, key, g = rec['frame'], rec['job'], rec['row_group']
        scale, dx, dy = values[0], values[1+2*g], values[2+2*g]
        out = process.fix(art.convert('RGBa').transform((576, 576), Image.Transform.AFFINE,
            (1/scale, 0, 288-(288+4.5*dx)/scale, 0, 1/scale, 288-(288+4.5*dy)/scale),
            Image.Resampling.BICUBIC).convert('RGBA'), name)
        out.save(T/'registered_2x'/key/(name+'.png'))
        final = grade(out, native, name)
        final.save(T/'toned_2x'/key/(name+'.png'))
        rec['calibration'] = [scale, dx, dy]
        rec['generated_pixels_per_native_pixel'] = rec['sampling_before_registration']/scale
        assert rec['generated_pixels_per_native_pixel'] >= 2, (name, rec['generated_pixels_per_native_pixel'])
        rec['edge'] = process.spill(final, name)
        bb = final.getchannel('A').getbbox()
        assert bb[0]>3 and bb[1]>3 and bb[2]<573 and bb[3]<573, (name, bb)
        assert rec['edge']['max_score'] == 0
        assert np.array_equal(np.asarray(out)[:, :, 3], np.asarray(final)[:, :, 3])
        overlay = np.zeros((128, 128, 3), np.uint8)
        overlay[:, :, 0] = np.round(target*255).clip(0, 255).astype(np.uint8)
        overlay[:, :, 1] = np.round(calibrate.warp(mask, [scale, dx, dy])*255).clip(0, 255).astype(np.uint8)
        pictures.extend([native, final, Image.fromarray(overlay).convert('RGBA')])
        labels.extend([name+' native', key.split('_')[-1]+' 2x', 'native red / new green'])
        if key.endswith('start') or name in ['m432ag0', 'm432ah0']:
            selected[name] = {**rec, 'image': str((T/'toned_2x'/key/(name+'.png')).relative_to(T))}
    contact(pictures[:18], labels[:18], T/'review/start_registration.png', columns=3)
    contact(pictures[18:], labels[18:], T/'review/end_registration.png', columns=3)
    process.save(T/'registration.json', {'all_candidates': records, 'selected': selected})
    for job in data['jobs'].values():
        job['status'] = 'processed_unreviewed'
    process.save(T/'sequence_jobs.json', data)
    print('Scale', values[0], 'sampling', records[0]['generated_pixels_per_native_pixel'])
    print('Row translations 2x', [round(v*4.5, 2) for v in values[1:]])


if __name__ == '__main__':
    run()
