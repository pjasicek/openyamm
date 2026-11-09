"""Prepare review-only replacements from retained masters; never change staged approvals."""
import json
import sys
from pathlib import Path
from urllib.parse import unquote

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from prepare import HERE, OUT, PREVIOUS, digest, read, write

sys.path.insert(0, str(HERE.parent))
import matte


def resize(image, size):
    return image.convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA')


def meaningful_box(image):
    return Image.fromarray((np.asarray(image)[:, :, 3] > 32).astype('uint8') * 255).getbbox()


def fit(image, native):
    box = meaningful_box(image)
    x, y, right, bottom = [v * 2 for v in native.getbbox()]
    output = Image.new('RGBA', (native.width * 2, native.height * 2))
    output.alpha_composite(resize(image.crop(box), (right-x, bottom-y)), (x, y))
    return output


def isolate(image):
    pixels = np.asarray(image).copy()
    # The tool stores colorful RGB under almost invisible alpha. Do not key those RGB values.
    # Preserve resolved antialiasing; only discard the non-subject floating residue.
    labels, _ = ndimage.label(pixels[:, :, 3] > 32)
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    # Keep detached ornaments as well as the central weapon, if materially visible.
    keep = np.isin(labels, np.flatnonzero(sizes >= max(10, sizes.max() * .0002)))
    keep = ndimage.binary_dilation(keep, iterations=3)
    pixels[~keep | (pixels[:, :, 3] <= 8)] = 0
    return Image.fromarray(pixels)


def main():
    catalog = json.loads((HERE/'catalog.js').read_text().split('=', 1)[1].strip().rstrip(';'))
    assets = {a['id']: a for a in catalog['assets'].values()}
    latest = read(OUT/'review.original.json')
    flags = read(OUT/'new_flags.json')
    staged = read(OUT/'stage_manifest.json')['records']
    previous = read(PREVIOUS/'repairs.json')['results']
    generated = read(OUT/'generated/batches.json')
    results = {}
    (OUT/'repaired').mkdir(exist_ok=True)

    def native(target):
        return Image.open(HERE/unquote(assets[target]['native'])).convert('RGBA')

    def save(target, image, operations, donor=None):
        a = assets[target]
        old = staged.get(target, {})
        old_path = old.get('reviewed_path', previous.get(target, {}).get('path', a['candidate']))
        old_hash = digest(HERE/unquote(old_path))
        path = OUT/'repaired'/(target+'.png') if not donor else HERE/results[donor]['path']
        if not donor:
            image.save(path)
        results[target] = {
            'target': target, 'name': a['name'], 'source_hash': a['sourceHash'],
            'path': str(path.relative_to(HERE)), 'sha256': digest(path),
            'old_path': old_path, 'old_sha256': old_hash,
            'note': flags.get(target, {}).get('note', ''), 'operations': operations,
            'unresolved': [], 'status': 'repair_candidate_needs_review',
            'changed': digest(path) != old_hash,
            'previously_approved': latest['decisions'].get(target, {}).get('decision') == 'approve',
            'pass_id': '20260926_round2', 'review_baseline_at': latest['exported_at'],
        }
        if donor:
            results[target]['exact_native_donor'] = donor

    for batch in generated['batches']:
        path = OUT/'generated'/batch['name']/'raw.png'
        raw = Image.open(path).convert('RGBA')
        sx, sy = raw.width/batch['size'][0], raw.height/batch['size'][1]
        for cell in batch['cells']:
            x, y, w, h = cell['slot']
            box = [round(x*sx), round(y*sy), round((x+w)*sx), round((y+h)*sy)]
            if batch['name'] == 'weapons_04':
                # The returned top-row pommels extend past the mathematical half-height.
                # The inspected empty inter-row band is y=920..945 in the 887x1774 master.
                divider = round(raw.height * 930 / 1774)
                box[3 if y == 0 else 1] = divider
            subject = isolate(raw.crop(box))
            bounds = meaningful_box(subject)
            guide = native(cell['target'])
            nb = guide.getbbox()
            sampling = [(bounds[2]-bounds[0])/(nb[2]-nb[0]), (bounds[3]-bounds[1])/(nb[3]-nb[1])]
            assert min(sampling) >= 2, (cell['name'], sampling)
            assert bounds[0] > 0 and bounds[1] > 0 and bounds[2] < subject.width and bounds[3] < subject.height, (cell['name'], bounds)
            save(cell['target'], fit(subject, guide), [{
                'method': 'imagegen_native_reference_reconstruction',
                'master': str(path.relative_to(HERE)), 'master_sha256': digest(path),
                'prompt': str((path.parent/'prompt.txt').relative_to(HERE)),
                'raw_crop': box, 'subject_bounds': bounds, 'native_sampling': sampling,
                'output_size': [guide.width*2, guide.height*2],
                'resampling': 'premultiplied_alpha_lanczos', 'native_mask_applied': False,
            }])

    for target, donor in generated['exact_native_aliases'].items():
        assert assets[target]['sourceHash'] == assets[donor]['sourceHash']
        save(target, None, [{'method': 'shared_exact_native_sprite', 'donor': donor}], donor)

    target = 'engine--icons--sshield1.bmp'
    raw_path = HERE/'../chat_bundles/dense64_20260916/dense64_inventory_002/outputs/raw/S001.png'
    raw = Image.open(raw_path).convert('RGBA')
    # Inspected complete shield, including the curved top clipped by the old y=466 cell boundary.
    box = [40, 440, 378, 785]
    clean, parameters = matte.extract(raw.crop(box))
    clean = isolate(clean)
    bounds = meaningful_box(clean)
    assert bounds[0] > 0 and bounds[1] > 0 and bounds[2] < clean.width and bounds[3] < clean.height
    save(target, fit(clean, native(target)), [{
        'method': 'complete_shield_reextraction', 'master': str(raw_path.relative_to(HERE)),
        'master_sha256': digest(raw_path), 'old_raw_crop': [57, 466, 365, 775],
        'raw_crop': box, 'subject_bounds': bounds, 'matte': parameters,
    }])

    target = 'engine--icons--7item074v1a.bmp'
    prior = previous[target]
    image = Image.open(HERE/prior['path']).convert('RGBA')
    operation = prior['operations'][0]
    raw_path = operation['raw']
    raw = Image.open(raw_path).convert('RGBA')
    rb = operation['component']['box']
    subject = raw.crop((rb[0]-4, rb[1]-4, rb[2]+4, rb[3]+4))
    subject, neck_matte = matte.extract(subject)
    # Restore only the neckline's dark V strip, removed too broadly in round 1.
    # Other fitted contours and sleeve openings stay as reviewed.
    original = fit(isolate(subject), native(target))
    patch_box = [87, 12, 112, 64]
    image.paste(original.crop(patch_box), tuple(patch_box))
    save(target, image, [{'method': 'restore_neckline_dark_v_from_same_master',
                         'master': raw_path, 'master_sha256': digest(Path(raw_path)),
                         'patch_box_2x': patch_box, 'matte': neck_matte}])

    target = 'engine--icons--item110v1.bmp'
    image = Image.open(HERE/previous[target]['path']).convert('RGBA')
    pixels = np.asarray(image).copy()
    rgb = pixels[:, :, :3].astype(float)
    r, g, b = rgb.transpose(2, 0, 1)
    alpha = pixels[:, :, 3]
    edge = (alpha > 0) & (ndimage.distance_transform_edt(np.pad(alpha > 8, 1))[1:-1, 1:-1] <= 4)
    green = edge & (g - np.maximum(r, b) > 4) & (g - np.minimum(r, b) > 12)
    pink = edge & (np.minimum(r, b) - g > 16)
    rgb[:, :, 1][green] = (r[green] + b[green]) / 2
    excess = np.minimum(r, b) - g - 8
    rgb[:, :, 0][pink] -= excess[pink]
    rgb[:, :, 2][pink] -= excess[pink]
    pixels[:, :, :3] = np.clip(np.rint(rgb), 0, 255).astype('uint8')
    pixels[alpha == 0] = 0
    save(target, Image.fromarray(pixels), [{'method': 'localized_helmet_contour_despill',
         'green_pixels': int(green.sum()), 'magenta_pixels': int(pink.sum()), 'alpha_unchanged': True}])
    for a in assets.values():
        if a['sourceHash'] == assets[target]['sourceHash'] and a['id'] != target:
            save(a['id'], None, [{'method': 'shared_exact_native_sprite', 'donor': target}], target)

    target = 'engine--icons--7item026.bmp'
    prior = previous[target]
    save(target, Image.open(HERE/prior['path']).convert('RGBA'), [{
        'method': 'retain_existing_inspected_repair', 'prior_path': prior['path'],
        'reason': 'New flag has no note and refers to the original extraction; the existing slimmer-handle and contour repair remains available.',
    }])
    # Confirmed during the additional audit of approved files: pommels, shield top, bowstrings.
    audit = read(OUT/'staged_crop_audit.json')['targets']
    crop_names = ['item022', 'item023', 'lshield2', 'item058', 'item059', '7item042', 'bow1', 'bow2', 'bow3']
    for name in crop_names:
        target = catalog['assets'][name]['id']
        info = audit[target]
        raw_path = Path(info['raw'])
        raw = Image.open(raw_path).convert('RGBA')
        x, y, right, bottom = info['subject_bounds']
        box = [max(0, x-12), max(0, y-12), min(raw.width, right+12), min(raw.height, bottom+12)]
        subject = raw.crop(box)
        pixels = np.asarray(subject)
        if np.median(pixels[[0, 0, -1, -1], [0, -1, 0, -1], 3]) > 128:
            subject, params = matte.extract(subject, preserve_thin_lines=True)
        else:
            params = {'method': 'retained_alpha'}
        image = fit(isolate(subject), native(target))
        save(target, image, [{'method': 'staged_crop_audit_complete_subject',
             'master': str(raw_path.relative_to(HERE.parent)), 'master_sha256': digest(raw_path),
             'old_crop': info['raw_crop'], 'raw_crop': box, 'matte': params,
             'reason': 'Complete pommel, shield rim or bowstring extends outside the original extraction.'}])
        for a in assets.values():
            if a['sourceHash'] == assets[target]['sourceHash'] and a['id'] != target:
                save(a['id'], None, [{'method': 'shared_exact_native_sprite', 'donor': target}], target)
    assert set(flags) <= set(results), set(flags)-set(results)
    write(OUT/'repairs.json', {'schema': 'paperdoll-repairs-v2', 'results': results,
          'summary': {'targets': len(results), 'new_flags_covered': len(flags),
                      'unique_generated_masters': sum(len(b['cells']) for b in generated['batches']),
                      'shared_aliases': sum('exact_native_donor' in r for r in results.values()),
                      'staged_crop_repairs': sum(any(op['method'] == 'staged_crop_audit_complete_subject' for op in r['operations']) for r in results.values())}})

    (OUT/'after_contacts').mkdir(exist_ok=True)
    unique = [r for r in results.values() if 'exact_native_donor' not in r]
    for start in range(0, len(unique), 8):
        sheet = Image.new('RGB', (1600, 1240), '#56646b')
        draw = ImageDraw.Draw(sheet)
        for i, result in enumerate(unique[start:start+8]):
            a = assets[result['target']]
            x, y = i % 4 * 400, i // 4 * 620
            draw.text((x+4, y+5), a['name']+'   Native / Reviewed / New', fill='white')
            ims = [native(a['id']).resize((a['size'][0]*2, a['size'][1]*2), Image.Resampling.NEAREST),
                   Image.open(HERE/unquote(result['old_path'])).convert('RGBA'),
                   Image.open(HERE/result['path']).convert('RGBA')]
            for j, im in enumerate(ims):
                scale = min(1.8, 128/im.width, 570/im.height)
                im = resize(im, (round(im.width*scale), round(im.height*scale))) if j else im.resize(
                    (round(im.width*scale), round(im.height*scale)), Image.Resampling.NEAREST)
                sheet.paste(im, (x+j*133+(128-im.width)//2, y+35), im)
        sheet.save(OUT/'after_contacts'/f'{start//8+1:02}.png')
    print(read(OUT/'repairs.json')['summary'])


if __name__ == '__main__':
    main()
