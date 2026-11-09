"""Clean reviewed AI outputs, register native canvases, and stage 2x decoration PNGs."""
from pathlib import Path
import hashlib
import importlib.util
import json

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location('sprite_matte',
    REPO / 'level_generation/creatures/mm6_goblin/direct_ai_attack/clean_edges.py')
matting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(matting)


def contour_cleanup(image, matte):
    a = np.array(image)
    order = [0, 1, 2] if matte[0] else [1, 0, 2]
    color = a[:, :, order].astype(np.int16)
    edge = (a[:, :, 3] > 0) & ((ndimage.distance_transform_edt(a[:, :, 3] >= 128) <= 4)
                              | (a[:, :, 3] < 255))
    excess = np.where(edge, np.maximum(0, np.minimum(color[:, :, 0], color[:, :, 2]) - color[:, :, 1] - 10), 0)
    color[:, :, 0] -= excess
    color[:, :, 2] -= excess
    a[:, :, :3] = color[:, :, order].astype(np.uint8)
    return Image.fromarray(a)


def clean(image, matte):
    # A delivered alpha channel takes precedence; opaque returned sheets need chroma extraction.
    if image.mode == 'RGBA' and image.getchannel('A').getextrema()[0] < 255:
        return image.copy(), {'method': 'delivered_alpha'}
    order = [0, 1, 2] if matte[0] else [1, 0, 2]
    rgb = np.array(image.convert('RGB'))[:, :, order]
    extracted, stats = matting.extract(Image.fromarray(rgb))
    a = np.array(extracted)
    a[:, :, :3] = a[:, :, order]
    return contour_cleanup(Image.fromarray(a), matte), dict(stats, method='local_matte_unmixing')


def alpha_bounds(image):
    return Image.fromarray((np.array(image)[:, :, 3] > 16).astype(np.uint8) * 255).getbbox()


def register(image, source, matte):
    bbox = alpha_bounds(image)
    assert bbox
    native_bbox = source['visible_bounds']
    target = tuple(v * 2 for v in native_bbox)
    size = (target[2] - target[0], target[3] - target[1])
    crop = image.crop(bbox).convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA')
    out = Image.new('RGBA', tuple(v * 2 for v in source['size']))
    out.paste(crop, target[:2])
    return contour_cleanup(out, matte), {'generated_bounds': bbox, 'target_bounds': target,
                                       'scale_xy': [size[0] / (bbox[2] - bbox[0]), size[1] / (bbox[3] - bbox[1])]}


def luma_samples(image):
    a = np.array(image)
    return a[:, :, :3][a[:, :, 3] >= 240] @ np.array([.2126, .7152, .0722])


def grade(image, gain):
    a = np.array(image)
    a[:, :, :3] = np.clip(np.round(a[:, :, :3].astype(float) * gain), 0, 255).astype(np.uint8)
    return Image.fromarray(a)


def foliage_ratios(image):
    a = np.array(image)
    r, g, b = a[:, :, :3].astype(float).transpose(2, 0, 1)
    selected = (a[:, :, 3] >= 240) & (g > r * 1.12) & (g > b * 1.12) & (g > 12)
    return np.array([np.median(r[selected] / g[selected]), np.median(b[selected] / g[selected])])


def match_foliage(image, gains):
    a = np.array(image)
    rgb = a[:, :, :3].astype(float)
    r, g, b = rgb.transpose(2, 0, 1)
    weight = np.clip((g - np.maximum(r, b)) / np.maximum(g, 1) / .15, 0, 1)
    rgb[:, :, 0] *= 1 + weight * (gains[0] - 1)
    rgb[:, :, 2] *= 1 + weight * (gains[1] - 1)
    a[:, :, :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    return Image.fromarray(a)


def composite(image, background):
    canvas = Image.new('RGBA', image.size, (*background, 255))
    canvas.alpha_composite(image)
    return canvas.convert('RGB')


def lock_states(images):
    if 'tree06a' in images:
        # Reuse the exact foliage/trunk/alpha; retain only reviewed red/orange fruit from the second state.
        base = np.array(images['6tree06'])
        fruit = np.array(images['tree06a'])
        r, g, b = fruit[:, :, :3].astype(float).transpose(2, 0, 1)
        selected = (r > g * 1.25 + 6) & (r > b * 1.6 + 8) & (fruit[:, :, 3] > 200)
        selected[round(selected.shape[0] * .82):] = False
        labels, _ = ndimage.label(selected)
        sizes = np.bincount(labels.ravel())
        keep = sizes >= 6
        keep[0] = False
        weight = ndimage.gaussian_filter(ndimage.binary_dilation(keep[labels], iterations=1).astype(float), .55)
        weight *= (base[:, :, 3] > 200)
        out = base.copy()
        out[:, :, :3] = np.round(base[:, :, :3] * (1 - weight[:, :, None])
                                + fruit[:, :, :3] * weight[:, :, None]).astype(np.uint8)
        images['tree06a'] = Image.fromarray(out)
    if 'swrdstx' in images:
        # Use one boulder for both states, at the native bottom alignment.
        rock = images['swrdstx']
        sword = images['swrdstn'].copy()
        top = sword.height - rock.height
        sword.paste(Image.new('RGBA', (sword.width, rock.height)), (0, top))
        sword.alpha_composite(rock, (0, top))
        images['swrdstn'] = sword


def run():
    inv = json.loads((HERE / 'inventory.json').read_text())
    batches = json.loads((HERE / 'batches.json').read_text())
    images, registrations, generations, matte_by_frame = {}, {}, {}, {}
    (HERE / 'cleaned').mkdir(exist_ok=True)
    for key, batch in batches.items():
        raw_path = HERE / 'raw' / (key + '.png')
        if not raw_path.exists():
            print('Pending generation:', key)
            continue
        raw = Image.open(raw_path)
        cols, rows = batch['columns'], batch['rows']
        clean_sheet, stats = clean(raw, batch['matte'])
        clean_sheet.save(HERE / 'cleaned' / (key + '.png'))
        restored = {}
        for i, name in enumerate(batch['frames']):
            rect = (round(i % cols * raw.width / cols), round(i // cols * raw.height / rows),
                    round((i % cols + 1) * raw.width / cols), round((i // cols + 1) * raw.height / rows))
            cell = clean_sheet.crop(rect)
            image, alignment = register(cell, inv['sources'][name], batch['matte'])
            alignment['sheet_extraction'] = rect
            registrations[name] = alignment
            restored[name] = image
            matte_by_frame[name] = batch['matte']
        foliage_gain = None
        if key in ('6tree01', '6tree02', '6tree05', '6tree19', 'food_tree'):
            anchor = batch['frames'][0]
            foliage_gain = np.clip(foliage_ratios(Image.open(HERE / 'native' / (anchor + '.png')))
                                   / foliage_ratios(restored[anchor]), .3, 1.8)
            restored = {name: match_foliage(im, foliage_gain) for name, im in restored.items()}
        native_luma = np.concatenate([luma_samples(Image.open(HERE / 'native' / (n + '.png')))
                                      for n in restored])
        enhanced_luma = np.concatenate([luma_samples(im) for im in restored.values()])
        gain = float(np.clip(np.percentile(native_luma, 60) / np.percentile(enhanced_luma, 60), .65, 1.08))
        for name, image in restored.items():
            images[name] = contour_cleanup(grade(image, gain), batch['matte'])
        generations[key] = {'raw': str(raw_path.relative_to(HERE)), 'raw_size': list(raw.size),
                            'raw_sha256': hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                            'reference': 'references/' + key + '.png', 'prompt': 'prompts/' + key + '.txt',
                            'mode': 'built-in imagegen', 'tonal_gain': gain, 'cleanup': stats,
                            'foliage_red_blue_gain': foliage_gain.tolist() if foliage_gain is not None else None}
    lock_states(images)
    frames = {}
    audits = {}
    for name, im in images.items():
        im.save(HERE / 'enhanced' / (name + '.png'))
        a = np.array(im)
        order = [0, 1, 2] if matte_by_frame[name][0] else [1, 0, 2]
        rgb = a[:, :, order].astype(np.int16)
        edge = (a[:, :, 3] > 0) & ((ndimage.distance_transform_edt(a[:, :, 3] >= 128) <= 4)
                                  | (a[:, :, 3] < 255))
        excess = np.maximum(0, np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1])
        audits[name] = {'visible_pixels': int((a[:, :, 3] > 0).sum()),
                        'contour_spill_candidates_over_16': int((edge & (excess > 16)).sum()),
                        'alpha_bounds': im.getbbox(), 'expected_size': [2 * v for v in inv['sources'][name]['size']],
                        'size': list(im.size)}
        assert list(im.size) == audits[name]['expected_size']
        assert audits[name]['contour_spill_candidates_over_16'] == 0, (name, audits[name])
        source = inv['sources'][name]
        frames[name] = {'file': 'enhanced/' + name + '.png', 'native_size': source['size'], 'physical_size': list(im.size),
                        'logical_pivot': [source['size'][0] / 2, source['size'][1]],
                        'palette_baked': source['palette_id'], 'sha256': hashlib.sha256((HERE / 'enhanced' / (name + '.png')).read_bytes()).hexdigest()}
    records = inv['records']
    manifest = {'schema_version': 1, 'status': 'ready for map-scoped installation; see playtest_snapshot.json for installed state', 'scope': {'world': 'mm6', 'map': 'oute3.odm'},
                'pixels_per_logical_pixel': 2, 'format': 'RGBA8 PNG, straight alpha',
                'alignment': 'Full native canvas doubled; retain original frame scale and flags',
                'frames': frames, 'decorations': records,
                'native_animation_policy': 'Reuse all six native animated groups and original timings at 1x; do not freeze them',
                'installation': 'Requires explicit map-scoped decoration image override; do not replace global sprite files'}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (HERE / 'generation.json').write_text(json.dumps(generations, indent=2) + '\n')
    (HERE / 'registration.json').write_text(json.dumps(registrations, indent=2) + '\n')
    (HERE / 'validation.json').write_text(json.dumps(audits, indent=2) + '\n')
    for label, bg in [('dark', (38, 42, 39)), ('light', (224, 226, 221))]:
        sheet = Image.new('RGB', (4 * 640, ((len(images) + 3) // 4) * 360), bg)
        draw = ImageDraw.Draw(sheet)
        for i, (name, im) in enumerate(images.items()):
            native = Image.open(HERE / 'native' / (name + '.png'))
            size = (min(292, native.width), min(310, native.height))
            # Match both illustrations to one common logical display size.
            scale = min(292 / native.width, 310 / native.height)
            size = (round(native.width * scale), round(native.height * scale))
            x, y = i % 4 * 640, i // 4 * 360
            draw.text((x + 8, y + 8), name + ' : native | enhanced', fill=(180, 180, 180) if label == 'dark' else (30, 30, 30))
            for j, pic in enumerate([native, im]):
                pic = pic.convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA')
                sheet.paste(composite(pic, bg), (x + j * 320 + (320 - size[0]) // 2, y + 338 - size[1]))
        sheet.save(HERE / 'review' / ('comparison_' + label + '.png'))
    for key, batch in batches.items():
        if not all(n in images for n in batch['frames']):
            continue
        w = max(images[n].width for n in batch['frames'])
        h = max(images[n].height for n in batch['frames'])
        sheet = Image.new('RGBA', (w * batch['columns'], h * batch['rows']))
        for i, name in enumerate(batch['frames']):
            im = images[name]
            sheet.paste(im, (i % batch['columns'] * w + (w - im.width) // 2,
                            i // batch['columns'] * h + h - im.height))
        sheet.save(HERE / 'sheets' / (key + '.png'))
    print('Exported', len(images), 'enhanced images; matte edge checks passed.')


if __name__ == '__main__':
    run()
