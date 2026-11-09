"""Extract native skeleton restorations and normalize bone color consistently."""
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'mm6_peasants'))
import process_family
import materials


def build_guides():
    inventory = json.loads((ROOT / 'inventory.json').read_text())['ske']
    records = json.loads((ROOT / 'registration.json').read_text())
    guides = {}
    for name, source in inventory['sources'].items():
        index = np.array(Image.open(process_family.REPO / source['path']))
        canvas = inventory['logical_canvas']
        offset = [(canvas[0] - index.shape[1]) // 2, canvas[1] - index.shape[0]]
        origin = records[name]['canvas_origin_px']
        guides[name] = {}
        for key, selection, pad in [('blade', (index >= 143) & (index <= 198), 22),
                                    ('eyes', (index >= 199) & (index <= 209), 10)]:
            if key == 'blade':
                labels, count = ndimage.label(selection, structure=np.ones((3, 3)))
                if count:
                    sizes = np.bincount(labels.ravel())
                    sizes[0] = 0
                    selection = labels == sizes.argmax()
            y, x = np.where(selection)
            boxes = []
            if len(x):
                boxes = [[int(2 * (x.min() + offset[0]) - origin[0] - pad),
                          int(2 * (y.min() + offset[1]) - origin[1] - pad),
                          int(2 * (x.max() + offset[0] + 1) - origin[0] + pad),
                          int(2 * (y.max() + offset[1] + 1) - origin[1] + pad)]]
            guides[name][key] = boxes
    (ROOT / 'material_guides.json').write_text(json.dumps(guides, indent=2) + '\n')


def finish():
    build_guides()
    for folder in ('cleaned', 'aligned_2x'):
        for path in (ROOT / folder).glob('*.png'):
            image = Image.open(path)
            a = np.array(image)
            rgb = a[:, :, :3].astype(float) / 255
            mask = np.array(materials.coverage(image, path.stem if folder == 'aligned_2x' else None)).astype(float) / 255
            bone = mask[:, :, 0, None]
            luminance = rgb @ materials.LUMA
            target = luminance[:, :, None] * np.array([1.035, 1.002, .93]) * .96
            a[:, :, :3] = np.round(np.clip(rgb * (1 - bone) + target * bone, 0, 1) * 255).astype(np.uint8)
            process_family.fix_contour(Image.fromarray(a), 'magenta').save(path)
            if folder == 'aligned_2x':
                # Retain masks derived before the tonal correction changes hues.
                Image.fromarray(np.round(mask * 255).astype(np.uint8), 'RGBA').save(ROOT / 'masks_2x' / path.name)
    (ROOT / 'tone.json').write_text(json.dumps({
        'bone_luminance_gain': .96, 'bone_rgb_per_luminance': [1.035, 1.002, .93],
        'protected': 'rusty blade and red eye points',
        'scope': 'fixed enhanced-art mask correction across every native frame',
        'variant_fit': 'Native material luminance curves, preserving nonlinear dark clamp and highlight ceiling'
    }, indent=2) + '\n')



def skull(image, name):
    """Broad ivory skull cap; rust and thin raised hands cannot define the crown."""
    pixels = np.array(image)
    r, g, b = pixels[:, :, :3].astype(float).transpose(2, 0, 1)
    box = process_family.bounds(image)
    height = box[3] - box[1]
    yy, xx = np.indices(pixels.shape[:2])
    bone = (pixels[:, :, 3] >= 128) & (g > 65) & (r < g * 1.25)
    if name == 'skedyf0':
        # The corpse skull lies beside the ribs, below the raised knee.
        bone &= (xx < box[0] + (box[2]-box[0]) * .38) & (xx > box[0] + (box[2]-box[0]) * .16)
        bone &= yy > box[1] + height * .45
    else:
        bone &= yy < box[1] + height * .36
    width = max(3, round(height * .04))
    broad = ndimage.binary_opening(bone, structure=np.ones((1, width), bool))
    ys, xs = np.where(broad)
    assert len(xs), ('No skull cap', name)
    top = int(ys.min())
    cap = broad & (yy < top + max(2, round(height * .025)))
    return [float(np.median(np.where(cap)[1])), float(top)]


def foot(image, side):
    solid = np.array(image)[:, :, 3] >= 128
    box = process_family.bounds(image)
    height = box[3] - box[1]
    ys, xs = np.where(solid & (np.arange(image.height)[:, None] >= box[3] - height * .045))
    split = (xs.min() + xs.max()) / 2
    chosen = xs >= split if side == 'right' else xs < split
    if not chosen.any():
        chosen = np.ones(xs.shape, bool)
    return [float(np.median(xs[chosen])), float(box[3])]


def pelvis(image, crown, name):
    """Independent pelvis-tip check, never used to solve an upright transform."""
    pixels = np.array(image)
    box = process_family.bounds(image)
    height = box[3] - crown[1]
    yy, xx = np.indices(pixels.shape[:2])
    r, g, b = pixels[:, :, :3].astype(float).transpose(2, 0, 1)
    bone = (pixels[:, :, 3] >= 128) & (g > 55) & (r < g * 1.48)
    bone &= (yy > crown[1] + height * .39) & (yy < crown[1] + height * .57)
    bone &= abs(xx - crown[0]) < height * .06
    # Find the dense pelvic mass, not thin femurs below it.
    counts = bone.sum(axis=1).astype(float)
    counts = ndimage.gaussian_filter1d(counts, max(1, height * .008))
    row = int(counts.argmax())
    band = bone & (abs(yy-row) < max(1, height*.012))
    ys, xs = np.where(band)
    assert len(xs), ('No pelvis', name)
    return [float(np.median(xs)), float(np.median(ys))]


def run_redo():
    import hashlib
    import shutil
    sys.path.insert(0, str(ROOT.parent / 'mm6_remaining/redo_2x'))
    from prepare_run import REPO, native
    out = ROOT / 'redo_2x'
    config = json.loads((ROOT / 'config.json').read_text())
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    inventory = json.loads((ROOT / 'inventory.json').read_text())['ske']
    run = json.loads((out / 'run.json').read_text())
    records, calibrations, guides = {}, {}, {}
    policy = json.loads((out/'processing.json').read_text())
    reviewed = policy.get('reviewed_landmarks', {})
    for directory in ['aligned_2x', 'masks_2x']:
        (out / directory).mkdir(exist_ok=True)
    for job in run['jobs']:
        report = json.loads((out / 'review' / (job['id'] + '_extraction.json')).read_text())
        first = report['frames'][0]
        source = native(ROOT, first['frame'])
        clean = Image.open(REPO / first['clean_path']).convert('RGBA')
        nb, gb = process_family.bounds(source), process_family.bounds(clean)
        nc, gc = skull(source, first['frame']), skull(clean, first['frame'])
        sampling = (gb[3] - gc[1]) / (nb[3] - nc[1])
        method = 'First-pose ivory skull-to-sole anatomical scale; one uniform scale across the sheet'
        if job['id'] == 'death_corpse_redo_02':
            previous = records[first['frame']]
            old = Image.open(out / 'cleaned' / previous['batch'] / (first['frame'] + '.png'))
            ob = process_family.bounds(old)
            sampling = previous['calibrated_sampling'] * (gb[2]-gb[0]) / (ob[2]-ob[0])
            method = 'Shared seated overlap width transfers preceding anatomical scale; no per-pose fitting'
        assert sampling > 2, (job['id'], sampling)
        factor = 2 / sampling
        calibrations[job['id']] = dict(frame=first['frame'], native_skull=nc, raw_skull=gc,
            generated_sampling=sampling, method=method, raw_sha256=report['raw_sha256'])
        for frame in report['frames']:
            name = frame['frame']
            if name in records:
                continue
            clean = Image.open(REPO / frame['clean_path']).convert('RGBA')
            source = native(ROOT, name)
            im = process_family.resize_base(clean, (round(clean.width*factor), round(clean.height*factor)), config)
            nb, rb = process_family.bounds(source), process_family.bounds(im)
            nc, rc = skull(source, name), skull(im, name)
            nf, rf = foot(source, 'right'), foot(im, 'right')
            nx, rx = nc[0], rc[0]
            contact = 'Skull X, per-native-pose sole Y; independent pelvis and foot checks'
            if name.startswith('skeat'):
                nl, rl = foot(source, 'left'), foot(im, 'left')
                nx, rx = (nf[0]+nl[0])/2, (rf[0]+rl[0])/2
                contact = 'Planted foot-pair midpoint X and sole Y; independent skull and pelvis checks'
            tx, ty = round(nx*2-rx), nb[3]*2-rb[3]
            points = {'skull': dict(native=nc, restored_before_translation=rc),
                      'foot': dict(native=nf, restored_before_translation=rf)}
            if not name.startswith('skedy'):
                points['pelvis'] = dict(native=pelvis(source, nc, name),
                    restored_before_translation=pelvis(im, rc, name))
            if name in reviewed:
                saved = reviewed[name]
                assert saved['raw_sha256'] == report['raw_sha256'], ('Stale reviewed landmark', name)
                point = saved['pelvis']
                points['pelvis'] = dict(native=point['native'], restored_before_translation=[
                    point['raw_cell'][0]*im.width/clean.width, point['raw_cell'][1]*im.height/clean.height])
            residuals = {key: [round((point['restored_before_translation'][i]+[tx, ty][i])/2-point['native'][i], 2)
                for i in range(2)] for key, point in points.items()}
            box = im.getbbox()
            origin = [min(0, tx+box[0]-4), min(0, ty+box[1]-4)]
            end = [max(manifest['logical_canvas'][0]*2, tx+box[2]+4),
                   max(manifest['logical_canvas'][1]*2, ty+box[3]+4)]
            aligned = Image.new('RGBA', (end[0]-origin[0], end[1]-origin[1]))
            aligned.paste(im, (tx-origin[0], ty-origin[1]))
            # Native material bounds are broad guides; masks still classify enhanced pixels.
            index = np.array(Image.open(REPO / inventory['sources'][name]['path']))
            offset = [(manifest['logical_canvas'][0]-index.shape[1])//2,
                      manifest['logical_canvas'][1]-index.shape[0]]
            guide = {}
            for key, selection, pad in [('blade', (index>=143)&(index<=198), 24),
                                        ('eyes', (index>=199)&(index<=209), 14)]:
                if key == 'blade':
                    labels, count = ndimage.label(selection, structure=np.ones((3, 3)))
                    if count:
                        sizes = np.bincount(labels.ravel())
                        sizes[0] = 0
                        selection = labels == sizes.argmax()
                ys, xs = np.where(selection)
                guide[key] = [] if not len(xs) else [[int(2*(xs.min()+offset[0])-origin[0]-pad),
                    int(2*(ys.min()+offset[1])-origin[1]-pad), int(2*(xs.max()+offset[0]+1)-origin[0]+pad),
                    int(2*(ys.max()+offset[1]+1)-origin[1]+pad)]]
                if key == 'blade' and len(xs) > 1:
                    samples = np.column_stack((xs, ys)).astype(float)
                    center = samples.mean(axis=0)
                    _, axes = np.linalg.eigh(np.cov(samples.T))
                    axis = axes[:, -1]
                    along = (samples-center) @ axis
                    across = (samples-center) @ np.array([-axis[1], axis[0]])
                    axis_points = [center+axis*along.min(), center+axis*along.max()]
                    guide['blade_axis'] = dict(points=[(2*(point+offset)-origin).tolist() for point in axis_points],
                        radius=float(2*max(abs(across))+12))
            if name in policy.get('reviewed_weapon_regions', {}):
                region = policy['reviewed_weapon_regions'][name]
                assert region['raw_sha256'] == report['raw_sha256']
                guide['blade_polygon'] = [[point[0]*im.width/clean.width+tx-origin[0],
                    point[1]*im.height/clean.height+ty-origin[1]] for point in region['polygon_raw_cell']]
            guides[name] = guide
            mask = materials.coverage(aligned, guides=guide)
            pixels = np.array(aligned)
            rgb = pixels[:, :, :3].astype(float)/255
            bone = np.array(mask)[:, :, 0, None].astype(float)/255
            target = (rgb @ materials.LUMA)[:, :, None] * np.array([1.035, 1.002, .93]) * .96
            pixels[:, :, :3] = np.round(np.clip(rgb*(1-bone)+target*bone, 0, 1)*255).astype(np.uint8)
            process_family.fix_contour(Image.fromarray(pixels), 'magenta').save(out/'aligned_2x'/(name+'.png'))
            mask.save(out/'masks_2x'/(name+'.png'))
            effective = [2*clean.width/im.width, 2*clean.height/im.height]
            actual = clean.getbbox()
            records[name] = dict(batch=job['id'], raw_path=report['raw'], raw_sha256=report['raw_sha256'],
                raw_size=report['raw_size'], raw_rect=frame['raw_rect'], native_crop=report['native_crop'],
                scale=factor, calibrated_sampling=sampling, effective_sampling_xy=effective,
                translate=[tx, ty], canvas_origin_px=origin, native_bounds=frame['native_bounds'],
                review_landmarks=points, independent_residual_logical=residuals, contact_method=contact,
                tone_grade='Fixed native ivory bone grade; preserve blade and eyes',
                raw_clip=actual[0]<=0 or actual[1]<=0 or actual[2]>=clean.width or actual[3]>=clean.height,
                matte=frame['matte'], review_status='pending_static_sequence_and_variant_review')
    name = 'skefib0'
    previous = json.loads((ROOT/'registration.json').read_text())[name]
    assets = {}
    for folder in ['aligned_2x', 'masks_2x', 'cleaned']:
        relative = f'{folder}/{name}.png'
        shutil.copy2(ROOT/relative, out/relative)
        assets[relative] = hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
    records[name] = dict(previous, effective_sampling_xy=[2/previous['scale']]*2,
        retained_from=dict(project=str(ROOT.relative_to(REPO)),
            registration_sha256=hashlib.sha256((ROOT/'registration.json').read_bytes()).hexdigest(), assets=assets))
    source = native(ROOT, name)
    aligned = Image.open(out/'aligned_2x'/(name+'.png')).convert('RGBA')
    nc, rc = skull(source, name), skull(aligned, name)
    retained_points = {'skull': (nc, rc), 'pelvis': (pelvis(source, nc, name), pelvis(aligned, rc, name))}
    records[name]['review_landmarks'] = {key: dict(native=n, restored_before_translation=[
        r[i]+previous['canvas_origin_px'][i]-previous['translate'][i] for i in range(2)])
        for key, (n, r) in retained_points.items()}
    # These are anatomical differences, separate from primary-anchor rounding.
    for frame_name, record in records.items():
        for key, error in record.get('independent_residual_logical', {}).items():
            if key in ('skull', 'pelvis'):
                assert max(abs(v) for v in error) <= 12, (frame_name, key, error)
    guides[name] = json.loads((ROOT/'material_guides.json').read_text())[name]
    assert set(records) == set(manifest['frames'])
    for filename, value in [('registration.json', records), ('calibration.json', calibrations), ('material_guides.json', guides)]:
        (out/filename).write_text(json.dumps(value, indent=2)+'\n')
    shutil.copy2(ROOT/'tone.json', out/'tone.json')
    print(json.dumps(dict(frames=len(records), minimum_sampling=min(min(r['effective_sampling_xy']) for r in records.values()),
        clipped=[n for n, r in records.items() if r['raw_clip']], status='Registered; visual review pending')))


if __name__ == '__main__':
    if '--redo' in sys.argv:
        run_redo()
    else:
        process_family.run('ske')
        finish()
