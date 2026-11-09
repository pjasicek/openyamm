"""Author enhanced-pixel material coverage and native-calibrated palette previews."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'mm7_m514'))
from process import apply_variant


def smooth(value, low, high):
    t = np.clip((value-low)/(high-low), 0, 1)
    return t*t*(3-2*t)


def coverage(rgb, region):
    r, g, b = np.moveaxis(rgb, -1, 0)
    if region['selector'] == 'green':
        value = (g-np.maximum(r, b))/np.maximum(g, 1)
    elif region['selector'] == 'blue':
        value = (b-np.maximum(r, g))/np.maximum(b, 1)
    elif region['selector'] == 'cyan':
        value = (np.minimum(g, b)-r)/np.maximum(np.maximum(g, b), 1)
    elif region['selector'] == 'burgundy':
        value = (r-np.maximum(g, b))/np.maximum(r, 1)
    elif region['selector'] == 'cream':
        value = ((g-b)-region.get('red_penalty', 1.4)*(r-g))/np.maximum(r, 1)
    elif region['selector'] == 'warm_body':
        value = (r-b)/np.maximum(r, 1)
    elif region['selector'] == 'neutral':
        value = 1-(rgb.max(axis=2)-rgb.min(axis=2))/np.maximum(rgb.max(axis=2), 1)
    elif region['selector'] == 'purple':
        value = (np.minimum(r, b)-g)/np.maximum(np.maximum(r, b), 1)
    else:
        raise ValueError(region['selector'])
    weight = smooth(value, *region['thresholds'])
    if 'brightness_floor' in region:
        weight *= smooth(rgb.max(axis=2), *region['brightness_floor'])
    if 'brightness_ceiling' in region:
        weight *= 1-smooth(rgb.max(axis=2), *region['brightness_ceiling'])
    if 'minimum_warm_chroma' in region:
        weight *= smooth((r-b)/np.maximum(r, 1), *region['minimum_warm_chroma'])
    if 'minimum_green_over_blue' in region:
        weight *= smooth((g-b)/np.maximum(g, 1), *region['minimum_green_over_blue'])
    if 'maximum_green_over_blue' in region:
        weight *= 1-smooth((g-b)/np.maximum(r, 1), *region['maximum_green_over_blue'])
    if 'maximum_red_over_green' in region:
        weight *= 1-smooth((r-g)/np.maximum(r, 1), *region['maximum_red_over_green'])
    weight *= region.get('weight_multiplier', 1)
    return weight


def run(root):
    source = json.loads((root/'sources.json').read_text())
    config = json.loads((root/'config.json').read_text())['materials']
    repo = Path(__file__).resolve().parents[3]
    palettes = {p: np.frombuffer((repo/source['palette_sources'][str(p)]['path']).read_bytes()[:768],
                                np.uint8).reshape(256, 3).astype(float) for p in source['palettes']}
    base = palettes[source['base_palette']]
    variants = []
    for palette, colors in palettes.items():
        regions = []
        for channel, spec in enumerate(config['regions']):
            indices = np.array(spec['palette_indices'])
            matrix = np.linalg.lstsq(base[indices], colors[indices], rcond=None)[0]
            if spec.get('fit') == 'diagonal':
                matrix = np.diag((base[indices]*colors[indices]).sum(axis=0) / np.maximum((base[indices]**2).sum(axis=0), 1))
            elif spec.get('fit') == 'luminance':
                luma = np.array([.2126, .7152, .0722])
                shade = base[indices] @ luma
                gain = (shade[:, None]*colors[indices]).sum(axis=0)/max((shade*shade).sum(), 1)
                matrix = np.outer(luma, gain)
            regions.append(dict(channel=channel, rgb_matrix=matrix.tolist(),
                native_fit_mean_channel_error=float(abs(base[indices]@matrix-colors[indices]).mean())))
        descriptors = [int(d) for d, bindings in source['descriptor_bindings'].items()
            if any(f.get('palette_id') == palette for group in bindings.values()
                   for f in source['groups'][group]['frames'])]
        variants.append(dict(id=f'mm7:palette{palette}', palette_id=palette,
            default=palette == source['base_palette'], exact_bypass=palette == source['base_palette'],
            descriptors=descriptors, regions=regions))
        if len(regions) == 1:
            variants[-1]['rgb_matrix'] = regions[0]['rgb_matrix']
            variants[-1]['native_fit_mean_channel_error'] = regions[0]['native_fit_mean_channel_error']
            del variants[-1]['regions']
    data = dict(variants=variants, regions=config['regions'], recolor=dict(operation='masked_rgb_regions',
        color_space='encoded sRGB', rule='base + sum(mask * (base @ region_matrix - base)); alpha unchanged',
        calibration='Native palette material ramps; coverage is evaluated on enhanced RGB, never resized native masks.',
        limitation=config.get('limitation', '')))
    (root/'variants.json').write_text(json.dumps(data, indent=2)+'\n')
    registration = json.loads((root/'registration.json').read_text())
    for name in registration:
        rgba = np.array(Image.open(root/f'aligned_2x/{name}.png').convert('RGBA'))
        mask = np.zeros(rgba.shape[:2]+(3,), dtype=float)
        for channel, region in enumerate(config['regions']):
            mask[:, :, channel] = coverage(rgba[:, :, :3].astype(float), region)
            if region.get('native_palette_spatial_support'):
                indices = np.array(Image.open(repo/source['sources'][name]['path']))
                support_pixels = np.isin(indices, region['native_palette_spatial_support'])
                if region.get('support_largest_component'):
                    support_pixels = ndimage.binary_opening(support_pixels)
                    labels, count = ndimage.label(ndimage.binary_closing(support_pixels, iterations=2))
                    sizes = np.bincount(labels.ravel())
                    sizes[0] = 0
                    support_pixels = labels == sizes.argmax() if count else support_pixels
                ys, xs = np.where(support_pixels)
                if len(xs):
                    origin = registration[name]['canvas_origin_px']
                    y, x = np.indices(rgba.shape[:2])
                    x, y = (x+origin[0])/2, (y+origin[1])/2
                    pad = region.get('support_padding', 8)
                    support = smooth(x, xs.min()-pad, xs.min()) * (1-smooth(x, xs.max(), xs.max()+pad))
                    support *= smooth(y, ys.min()-pad, ys.min()) * (1-smooth(y, ys.max(), ys.max()+pad))
                    if region.get('support_components_min_pixels'):
                        labels, count = ndimage.label(ndimage.binary_closing(support_pixels, iterations=2))
                        support = np.zeros_like(support)
                        for component in range(1, count+1):
                            cy, cx = np.where(labels == component)
                            if len(cx) < region['support_components_min_pixels']:
                                continue
                            box = smooth(x, cx.min()-pad, cx.min()) * (1-smooth(x, cx.max(), cx.max()+pad))
                            box *= smooth(y, cy.min()-pad, cy.min()) * (1-smooth(y, cy.max(), cy.max()+pad))
                            support = np.maximum(support, box)
                    if region.get('support_enhanced_component'):
                        # Native bounds locate the material; enhanced pixels define its full contour.
                        candidate = (mask[:, :, channel] > .6) & (rgba[:, :, 3] >= 128)
                        labels, count = ndimage.label(candidate)
                        scores = np.bincount(labels.ravel(), weights=support.ravel())
                        scores[0] = 0
                        if count and scores.max() > 0:
                            selected = labels == scores.argmax()
                            if region.get('support_enhanced_components_min_pixels'):
                                sizes = np.bincount(labels.ravel())
                                retained = (sizes >= region['support_enhanced_components_min_pixels']) & (scores > 0)
                                selected = np.isin(labels, np.flatnonzero(retained))
                            if selected.any():
                                distance = ndimage.distance_transform_edt(~selected)
                                support = 1-smooth(distance, 1, 4)
                            else:
                                support = np.zeros_like(support)
                        else:
                            support = np.zeros_like(support)
                    mask[:, :, channel] *= support
                else:
                    mask[:, :, channel] = 0
        for channel, region in enumerate(config['regions']):
            if region.get('mask_sigma'):
                alpha = rgba[:, :, 3].astype(float)/255
                sigma = region['mask_sigma']
                mask[:, :, channel] = ndimage.gaussian_filter(mask[:, :, channel]*alpha, sigma)/np.maximum(ndimage.gaussian_filter(alpha, sigma), 1e-6)
        for channel, region in enumerate(config['regions']):
            for protected in region.get('exclude_channels', []):
                mask[:, :, channel] *= 1-mask[:, :, protected]
            polygons = region.get('frame_exclude_polygons', {}).get(name, [])
            if polygons:
                protected = Image.new('L', (rgba.shape[1], rgba.shape[0]))
                draw = ImageDraw.Draw(protected)
                origin = registration[name]['canvas_origin_px']
                for polygon in polygons:
                    draw.polygon([(round(x*2-origin[0]), round(y*2-origin[1]))
                                  for x, y in polygon], fill=255)
                mask[:, :, channel] *= 1-np.asarray(protected)/255
        mask /= np.maximum(mask.sum(axis=2, keepdims=True), 1)
        mask[rgba[:, :, 3] == 0] = 0
        if len(config['regions']) <= 1:
            mask = mask[:, :, 0]
        Image.fromarray(np.round(mask*255).astype(np.uint8)).save(root/f'masks_2x/{name}.png')
    selected = json.loads((root/'config.json').read_text())['identity_frames']
    contact = Image.new('RGB', (len(selected)*270, (len(variants)+1)*285), (45, 45, 45))
    draw = ImageDraw.Draw(contact)
    for col, name in enumerate(selected):
        im = Image.open(root/f'aligned_2x/{name}.png').convert('RGBA')
        mask = Image.open(root/f'masks_2x/{name}.png')
        for row, variant in enumerate(variants):
            out = apply_variant(im, mask, variant)
            assert np.array_equal(np.array(out)[:, :, 3], np.array(im)[:, :, 3])
            out = out.convert('RGBa').resize((256, 256), Image.Resampling.LANCZOS).convert('RGBA')
            contact.paste(out, (col*270, row*285+22), out)
            draw.text((col*270+3, row*285+3), name+' '+str(variant['palette_id']), fill='white')
        channels = mask.split() if mask.mode == 'RGB' else (mask, Image.new('L', mask.size), Image.new('L', mask.size))
        overlay = Image.merge('RGBA', (*channels, im.getchannel('A')))
        overlay = overlay.resize((256, 256))
        contact.paste(overlay, (col*270, len(variants)*285+22), overlay)
    contact.save(root/'review/identity_variants.png')
    print(f'{root.name}: masks for {len(registration)} frames; {len(variants)} native palettes')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    run(parser.parse_args().project)
