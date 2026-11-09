"""Create a reversible darker RGB-only variant. No AI, geometry edits, or alpha changes."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

import build_review
from package import composite

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'toned_v1'
CURVE_IN = [0, .08, .20, .40, .65, 1]
CURVE_OUT = [0, .08, .181, .348, .552, .90]


def grade(image):
    """Fixed sRGB luma curve and subtle cool balance; alpha is copied verbatim."""
    original = np.array(image.convert('RGBA'))
    rgb = original[:, :, :3].astype(np.float64) / 255
    luma = rgb @ np.array([.2126, .7152, .0722])
    target = np.interp(luma, CURVE_IN, CURVE_OUT)
    gain = np.divide(target, luma, out=np.ones_like(luma), where=luma > 0)
    rgb = np.clip(rgb * gain[:, :, None] * np.array([.98, 1, 1.02]), 0, 1)
    result = original.copy()
    result[:, :, :3] = np.round(rgb * 255).astype(np.uint8)
    # Do not alter fully transparent stored pixels, either.
    result[original[:, :, 3] == 0] = original[original[:, :, 3] == 0]
    assert np.array_equal(result[:, :, 3], original[:, :, 3])
    return Image.fromarray(result)


def comparison():
    OUT.mkdir(exist_ok=True)
    image = Image.open(ROOT / 'aligned_2x/gobata0.png')
    native = Image.open(ROOT / 'previews/native/gobata0.png').resize((710, 578), Image.Resampling.NEAREST)
    pictures = [native, image, grade(image)]
    # Same logical crop for all columns: readable close view without changing relative scale or placement.
    crop = (185, 30, 565, 578)
    result = Image.new('RGB', (3 * 380, 2 * 580), (42, 45, 44))
    draw = ImageDraw.Draw(result)
    for row, bg in enumerate([(229, 230, 223), (37, 41, 38)]):
        for col, (title, im) in enumerate(zip(['Original', 'Restored master', 'Darker variant'], pictures)):
            result.paste(composite(im.crop(crop), bg), (col * 380, row * 580 + 30))
            draw.text((col * 380 + 12, row * 580 + 8), title, fill='white')
    result.save(OUT / 'comparison.png')


def build():
    comparison()
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    for folder in ['aligned_1x', 'aligned_2x', 'trimmed_1x', 'trimmed_2x', 'action_sheets_2x', 'previews/native']:
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    source_hashes = {}
    for name, frame in manifest['frames'].items():
        for tier in ['1x', '2x']:
            record = frame['exports'][tier]
            source = ROOT / record['aligned']
            source_hashes[str(source.relative_to(ROOT))] = hashlib.sha256(source.read_bytes()).hexdigest()
            im = grade(Image.open(source))
            im.save(OUT / record['aligned'])
            x, y, w, h = record['crop_xywh']
            trimmed = im.crop((x, y, x + w, y + h))
            trimmed.save(OUT / record['trimmed'])
            restored = Image.new('RGBA', im.size)
            restored.paste(trimmed, (x, y))
            assert np.array_equal(np.array(im), np.array(restored))
            assert np.array_equal(np.array(trimmed)[:, :, 3],
                                  np.array(Image.open(ROOT / record['trimmed']))[:, :, 3])
        native_path = Path('previews/native') / (name + '.png')
        (OUT / native_path).write_bytes((ROOT / native_path).read_bytes())
    for tier in [1, 2]:
        atlas = Image.new('RGBA', tuple(manifest['memory'][f'{tier}x']['atlas_size']))
        sheet = Image.new('RGBA', (6 * 355 * tier, 7 * 289 * tier))
        for frame in manifest['frames'].values():
            ex = frame['exports'][f'{tier}x']
            atlas.paste(Image.open(OUT / ex['trimmed']), tuple(ex['atlas_xywh'][:2]))
        atlas.save(OUT / f'packed_front_{tier}x.png')
        assert np.array_equal(np.array(atlas)[:, :, 3],
                              np.array(Image.open(ROOT / f'packed_front_{tier}x.png'))[:, :, 3])
        for row, action in enumerate(manifest['actions']):
            images = []
            strip = Image.new('RGBA', (len(action['frames']) * 355 * tier, 289 * tier))
            for col, frame in enumerate(action['frames']):
                name = Path(frame['source']).stem
                im = Image.open(OUT / f'aligned_{tier}x/{name}.png')
                strip.paste(im, (col * 355 * tier, 0))
                sheet.paste(im, (col * 355 * tier, row * 289 * tier))
                images.append(im)
            if tier == 2:
                label = action['name'].lower()
                strip.save(OUT / f'action_sheets_2x/{label}.png')
                playback = [composite(im, (37, 41, 38)) for im in images]
                playback[0].save(OUT / f'previews/{label}.png', save_all=True, append_images=playback[1:],
                                 duration=125 if len(images) > 1 else 500, loop=0)
        sheet.save(OUT / f'front_all_actions_{tier}x.png')
        if tier == 1:
            for label, bg in [('light', (229, 230, 223)), ('dark', (37, 41, 38))]:
                composite(sheet, bg).save(OUT / f'previews/all_actions_{label}.png')
    manifest['tone_variant'] = {'source': '../manifest.json', 'method': 'Fixed RGB-only sRGB luma curve and balance',
                                'curve_input': CURVE_IN, 'curve_output': CURVE_OUT,
                                'rgb_balance': [.98, 1, 1.02], 'ai_calls': 0,
                                'alpha_identical_to_master': True, 'all_placement_and_timing_metadata_unchanged': True,
                                'master_sha256': source_hashes}
    for path, digest in source_hashes.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    build_review.ROOT = OUT
    build_review.build()
    print('Graded 31 frames in both tiers; alpha, crops, atlas layout, timing and master hashes preserved.')


if __name__ == '__main__':
    comparison() if '--preview' in sys.argv else build()
