"""Derive held armor from frozen approved bases, with an explicit local edit mask.

This prepares review candidates only. It never writes accepted art, review decisions,
manual placements, the acceptance ledger, or runtime assets.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage, spatial

OUT = Path(__file__).resolve().parent
HERE = OUT.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools/mm9_import_discovery'))
sys.path.insert(0, str(HERE / 'review_pass_20260926'))
from audit_mm9_armor_pose_pairs import derive_validated_pose_change_mask
from repair_assets import clean_spill, extract_piece, fit_native


def read(path):
    return json.loads(path.read_text())


def js(path):
    return json.loads(path.read_text().split('=', 1)[1].strip().rstrip(';'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def solid_mask(mask):
    """Fill the arm region's internal islands before joining two independent renders."""
    yy, xx = np.where(mask)
    if not len(xx):
        return mask
    points = np.column_stack([xx, yy])
    hull = spatial.ConvexHull(points)
    image = Image.new('L', (mask.shape[1], mask.shape[0]))
    ImageDraw.Draw(image).polygon([tuple(p) for p in points[hull.vertices]], fill=255)
    # Cover the restored sleeve tips, which can extend beyond the native silhouette.
    result = ndimage.binary_dilation(np.asarray(image) > 0, iterations=10)
    return result


def arm_transfer(base, donor, allowed, feather_top=None):
    p = np.asarray(base).copy()
    q = np.asarray(donor)
    distance = ndimage.distance_transform_edt(np.pad(allowed, 1))[1:-1, 1:-1]
    weight = np.clip(distance / 7, 0, 1)
    weight = weight * weight * (3 - 2 * weight)
    # Premultiplied blending prevents dark outlines and retains soft transparency.
    a = np.asarray(base.convert('RGBa')).astype(float)
    b = np.asarray(donor.convert('RGBa')).astype(float)
    mixed = np.rint(a * (1 - weight[:, :, None]) + b * weight[:, :, None]).astype('uint8')
    result = np.asarray(Image.fromarray(mixed, 'RGBa').convert('RGBA')).copy()
    # A fading copy of the old sleeve leaves detached fragments at the mask boundary.
    # Geometry uses the donor; only the opaque attachment's color is feathered.
    edge = allowed & ((p[:, :, 3] < 240) | (q[:, :, 3] < 240))
    if feather_top is not None:
        edge[:feather_top] = False
    result[edge] = q[edge]
    result[~allowed] = p[~allowed]
    return Image.fromarray(result)


def trim_hidden_sleeve(base, native_held, allowed):
    """For a disappearing sleeve, retain the accepted material without a donor render."""
    pixels = np.asarray(base).copy()
    guide = np.asarray(native_held.resize(base.size, Image.Resampling.NEAREST))[:, :, 3] / 255
    guide = np.clip((ndimage.gaussian_filter(guide, 1.1) - .25) / .5, 0, 1)
    limited = np.minimum(pixels[:, :, 3], np.rint(guide * 255))
    pixels[:, :, 3][allowed] = limited[allowed]
    pixels[allowed & (pixels[:, :, 3] == 0)] = 0
    return Image.fromarray(pixels)


def trim_chain_sleeve(base, allowed):
    # The accepted blue/gold shoulder is wider than the legacy raster. Follow the
    # restored torso's edge at the sleeve attachment instead of cutting the blue yoke.
    cut = Image.new('L', (base.width*4, base.height*4))
    polygon = [(0, 67), (60, 67), (70, 80), (73, 99), (70, 121), (0, 121)]
    ImageDraw.Draw(cut).polygon([(x*4, y*4) for x, y in polygon], fill=255)
    coverage = np.asarray(cut.resize(base.size, Image.Resampling.LANCZOS)) / 255
    pixels = np.asarray(base).copy()
    pixels[:, :, 3][allowed] = np.rint(pixels[:, :, 3] * (1-coverage))[allowed]
    pixels[allowed & (pixels[:, :, 3] == 0)] = 0
    return Image.fromarray(pixels)


def rotate_troll_forearm(donor):
    # The retained 6plate1v4 return repeated the lowered forearm. Rotate that local
    # segment 17 degrees around its elbow to match the native raised-arm reference.
    yy, xx = np.indices((donor.height, donor.width), dtype=float)
    strength = np.clip((yy-129)/12, 0, 1) * np.clip((122-xx)/14, 0, 1)
    angle = -.30 * strength
    x, y = xx-110, yy-146
    sx = 110 + np.cos(angle)*x - np.sin(angle)*y
    sy = 146 + np.sin(angle)*x + np.cos(angle)*y
    pixels = np.asarray(donor.convert('RGBa')).astype(float)
    result = np.stack([ndimage.map_coordinates(pixels[:, :, c], [sy, sx], order=1, mode='constant')
                       for c in range(4)], axis=2)
    return Image.fromarray(np.clip(np.rint(result), 0, 255).astype('uint8'), 'RGBa').convert('RGBA')


def make_pages(records):
    edited = [r for r in records if r['method'] != 'exact_approved_base_copy']
    for page in range((len(edited) + 7) // 8):
        sheet = Image.new('RGB', (1200, 8 * 245), (42, 46, 52))
        draw = ImageDraw.Draw(sheet)
        for row, r in enumerate(edited[page * 8:page * 8 + 8]):
            y = row * 245
            draw.text((6, y + 4), r['held'] + ' | accepted base / donor / result / native empty+held / edit area', fill='white')
            paths = [HERE / r['base_path'], OUT / 'donors' / (r['held'] + '.png'), HERE / r['path']]
            images = [Image.open(p).convert('RGBA') for p in paths]
            allowed = np.asarray(Image.open(OUT / 'masks' / (r['held'] + '.png'))) > 0
            box = Image.fromarray(allowed.astype('uint8') * 255).getbbox()
            box = (max(0, box[0]-8), max(0, box[1]-10), min(images[0].width, box[2]+16),
                   min(images[0].height, box[3]+14))
            natives = [Image.open(HERE / 'native' / ('engine--icons--' + n + '.bmp.png')).convert('RGBA')
                       .resize(images[0].size, Image.Resampling.NEAREST) for n in [r['empty'], r['held']]]
            marked = np.asarray(images[0]).copy()
            marked[allowed] = (250, 130, 45, 255)
            images += natives + [Image.fromarray(marked)]
            for col, im in enumerate(images):
                im = im.crop(box)
                scale = min(190 / im.width, 211 / im.height, 2)
                im = im.resize((round(im.width * scale), round(im.height * scale)), Image.Resampling.LANCZOS)
                sheet.paste(im, (col*200+5, y+26), im)
        sheet.save(OUT / 'contact' / f'arms-{page+1:02d}.png')


def main():
    for folder in ['candidates', 'masks', 'donors', 'contact']:
        (OUT / folder).mkdir(exist_ok=True)
    pairs = read(HERE / 'armor_pose_study_20260926/audit.json')['pairs']
    catalog = js(HERE / 'catalog.js')
    crop_maps = read(HERE / 'review_pass_20260926/crop_audit.json')['sheets']
    checkpoint_before = digest(HERE.parent / 'checkpoint/state.json')
    records = []
    for pair in pairs:
        base_path = HERE / pair['base_path']
        assert digest(base_path) == pair['base_sha256'], pair['empty']
        base = Image.open(base_path).convert('RGBA')
        held = pair['held']
        asset = catalog['assets'][held]
        destination = OUT / 'candidates' / (held + '.png')
        record = {**pair, 'target': asset['id'], 'source_hash': asset['sourceHash'],
                  'path': str(destination.relative_to(HERE))}
        allowed = np.zeros((base.height, base.width), dtype=bool)
        if pair['native_pair_identical']:
            shutil.copyfile(base_path, destination)
            record['method'] = 'exact_approved_base_copy'
        else:
            native_empty = Image.open(HERE / catalog['assets'][pair['empty']]['native']).convert('RGBA')
            native_held = Image.open(HERE / asset['native']).convert('RGBA')
            mask = derive_validated_pose_change_mask(native_held, native_empty, native_held, native_empty)
            allowed = solid_mask(np.repeat(np.repeat(mask, 2, axis=0), 2, axis=1))
            if held == '7item299v2':
                # The generated held torso is taller; keep the accepted shoulder and
                # breast contour, joining only below the armpit.
                allowed[:250] = False
            donor = Image.open(HERE / pair['held_candidate_path']).convert('RGBA')
            record['donor_method'] = 'existing_canvas'
            alternative = next((a for a in asset.get('preparedAlternatives', [])
                                if a['sha256'] == pair['held_candidate_sha256']), None)
            if alternative and alternative.get('raw'):
                raw_path = (HERE / alternative['raw']).resolve()
                component = crop_maps.get(str(raw_path), {}).get(asset['id'])
                if component:
                    raw = Image.open(raw_path).convert('RGBA')
                    donor = fit_native(extract_piece(raw, component), native_held)
                    record.update(donor_method='complete_raw_component', raw_path=str(raw_path.relative_to(ROOT)),
                                  raw_sha256=digest(raw_path), raw_component=component)
            donor, spill = clean_spill(donor, native_held)
            record['donor_cleanup'] = spill
            if held == '6plate1v4':
                donor = rotate_troll_forearm(donor)
                record['local_rotation_radians'] = .30
            donor.save(OUT / 'donors' / (held + '.png'))
            native_a = np.asarray(native_empty)[:, :, 3] > 128
            native_b = np.asarray(native_held)[:, :, 3] > 128
            added = int((native_b & ~native_a).sum())
            if (added <= 9 or held == 'item088v2') and held not in {'item087v1', 'item087v2'}:
                result = trim_chain_sleeve(base, allowed) if held == '6chain4v1' else \
                    trim_hidden_sleeve(base, native_held, allowed)
                record['method'] = 'accepted_sleeve_trim'
                if held == '6chain4v1':
                    record['trim_guide'] = 'visually_aligned_restored_blue_yoke'
            else:
                result = arm_transfer(base, donor, allowed, 264 if held == '7item299v2' else None)
                record['method'] = 'bounded_arm_transfer'
            result.save(destination)
        Image.fromarray(allowed.astype('uint8') * 255).save(OUT / 'masks' / (held + '.png'))
        output = np.asarray(Image.open(destination).convert('RGBA'))
        original = np.asarray(base)
        assert output.shape == original.shape
        differences = np.any(output != original, axis=2)
        assert not differences[~allowed].any(), held
        assert digest(base_path) == pair['base_sha256'], held
        record.update(sha256=digest(destination), allowed_pixels=int(allowed.sum()),
                      changed_pixels=int(differences.sum()), outside_rgba_differences=0,
                      outside_alpha_differences=0,
                      mask_path=str((OUT / 'masks' / (held + '.png')).relative_to(HERE)))
        records.append(record)
    assert digest(HERE.parent / 'checkpoint/state.json') == checkpoint_before
    write(OUT / 'manifest.json', {'staging_only': True, 'ledger_sha256': checkpoint_before,
          'approval_snapshot': 'acceptance_snapshot_20260926_1322', 'imagegen_calls': 0, 'pairs': records})
    make_pages(records)
    print(json.dumps({'pairs': len(records), 'exact_copies': sum(r['method'] == 'exact_approved_base_copy' for r in records),
                      'arm_edits': sum(r['method'] != 'exact_approved_base_copy' for r in records),
                      'outside_changes': 0}))


if __name__ == '__main__':
    main()
