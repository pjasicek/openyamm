"""Reviewed enhanced-blade masks: native colour statistics, preserved generated detail."""
import json
import numpy as np
from PIL import Image, ImageDraw
from process import ROOT, queue, save


def apply(image, name):
    path = ROOT / 'blade_color_settings.json'
    if not path.exists():
        return image
    item = json.loads(path.read_text())['frames'].get(name)
    if not item:
        return image
    assert queue.sha(ROOT / 'registered_2x' / (name + '.png')) == item['registered_sha256']
    assert queue.sha(ROOT / item['mask']) == item['mask_sha256']
    a = np.array(image)
    coverage = np.asarray(Image.open(ROOT / item['mask'])) / 255
    corrected = a[:, :, :3].astype(float) * np.array(item['rgb_gain'])
    rgb = a[:, :, :3] * (1 - coverage[:, :, None]) + corrected * coverage[:, :, None]
    a[:, :, :3] = np.rint(rgb).clip(0, 255).astype(np.uint8)
    assert np.array_equal(a[:, :, 3], np.asarray(image)[:, :, 3])
    assert np.array_equal(a[coverage == 0], np.asarray(image)[coverage == 0])
    return Image.fromarray(a)


def prepare():
    # These starts were placed on exposed enhanced steel after inspecting the
    # native/enhanced 1:1 contacts. No native silhouette is resized into a mask.
    starts = {'sa1': 370, 'sa2': 329, 'wb1': 350, 'wa2': 344, 'wb2': 363,
              'wd2': 344, 'we2': 344, 'wf2': 359, 'wg2': 348}
    folder = ROOT / 'blade_color_masks'
    folder.mkdir(exist_ok=True)
    tone = json.loads((ROOT / 'tone_settings.json').read_text())['multiplier']
    settings = {'method': 'Per-channel native/enhanced opaque blade median ratio, frozen; enhanced steel axis and reviewed hilt starts define masks. Two-pixel fade at exposed hilt; alpha and all unmasked pixels unchanged.', 'frames': {}}
    sheet = Image.new('RGB', (1152, len(starts) * 220), 'white')
    draw = ImageDraw.Draw(sheet)
    for row, (suffix, start) in enumerate(starts.items()):
        name = 'm456' + suffix
        im = Image.open(ROOT / 'registered_2x' / (name + '.png')).convert('RGBA')
        a = np.array(im)
        a[:, :, :3] = np.rint(a[:, :, :3].astype(float) * tone).clip(0, 255).astype(np.uint8)
        native = Image.new('RGBA', im.size)
        native.paste(queue.native(ROOT, name).resize((512, 512), Image.Resampling.NEAREST), (32, 32))
        n = np.asarray(native)
        yy, xx = np.indices(a.shape[:2])
        sample = (xx > 400) & (a[:, :, 3] >= 240)
        slope, intercept = np.polyfit(xx[sample], yy[sample], 1)
        half = max(abs(yy[sample] - (xx[sample] * slope + intercept))) + 5
        coverage = np.clip((xx - start) / 2, 0, 1) * (abs(yy - (xx * slope + intercept)) <= half)
        coverage *= a[:, :, 3] > 0
        m = Image.fromarray(np.rint(coverage * 255).astype(np.uint8))
        mp = folder / (name + '.png')
        m.save(mp)
        target = np.median(n[(xx > 400) & (n[:, :, 3] >= 240), :3], axis=0)
        current = np.median(a[sample, :3], axis=0)
        gain = target / current
        settings['frames'][name] = {'mask': str(mp.relative_to(ROOT)), 'mask_sha256': queue.sha(mp),
            'registered_sha256': queue.sha(ROOT / 'registered_2x' / (name + '.png')),
            'native_rgb_median': target.tolist(), 'generated_rgb_median': current.tolist(),
            'rgb_gain': gain.tolist(), 'enhanced_axis': [float(slope), float(intercept)],
            'enhanced_half_width': float(half), 'enhanced_start_x': start}
        overlay = a.copy()
        overlay[:, :, :3] = np.rint(a[:, :, :3] * (1 - .65 * coverage[:, :, None]) + np.array([255, 70, 30]) * .65 * coverage[:, :, None])
        for col, pic in enumerate([native, Image.fromarray(overlay)]):
            crop = pic.crop((290, 240, 570, 515))
            bg = Image.new('RGBA', crop.size, 'white'); bg.alpha_composite(crop)
            bg.thumbnail((540, 195))
            sheet.paste(bg.convert('RGB'), (col * 576, row * 220 + 22))
            draw.text((col * 576, row * 220), name + (' native' if col == 0 else ' enhanced mask'), fill='black')
    save(ROOT / 'blade_color_settings.json', settings)
    sheet.save(ROOT / 'review/blade_color_masks.png')
    print(len(starts), 'local blade masks prepared for review')


if __name__ == '__main__':
    prepare()
