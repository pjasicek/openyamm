"""Offline cleanup/registration and visual proofs. Does not generate or artistically accept images."""
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from placement import CHECKS_VERSION, inspect_placement, inspect_motion
from weather import preserve_field

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location('sorpigal_cleanup',
                                             HERE.parents[1] / 'decorations/mm6_new_sorpigal/process.py')
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


def read(path):
    return json.loads(path.read_text())


def color_order(matte):
    return [1, 0, 2] if matte[0] == 0 else [0, 2, 1] if matte[2] == 0 else [0, 1, 2]


def clean_solid(image, matte):
    if image.mode == 'RGBA' and image.getchannel('A').getextrema()[0] < 255:
        return image.copy(), {'method': 'delivered_alpha'}
    order = color_order(matte)
    rgb = np.array(image.convert('RGB'))[:, :, order]
    output, stats = cleanup.clean(Image.fromarray(rgb), (255, 0, 255))
    pixels = np.array(output)
    pixels[:, :, :3] = pixels[:, :, order]
    return Image.fromarray(pixels), stats


def clean_soft(image, matte):
    """Estimated chroma unmixing without the opaque-object erosion radius or fringe color clamp.

    A single RGB composite cannot uniquely recover foreground/alpha. Keep the raw master; visually
    compare soft tails and smoke. This is NOT an additive-blending conversion.
    """
    if image.mode == 'RGBA' and image.getchannel('A').getextrema()[0] < 255:
        return image.copy(), {'method': 'delivered_alpha'}
    order = color_order(matte)
    rgb = np.array(image.convert('RGB'), dtype=float)[:, :, order] / 255
    dominance = np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1]
    core = dominance <= 8 / 255
    if not np.any(core):
        raise ValueError('No reliable foreground in cell; inspect wrong/empty output')
    _, nearest = ndimage.distance_transform_edt(~core, return_indices=True)
    foreground = rgb[nearest[0], nearest[1]]
    # Built-in image generation may return a slightly varied magenta field rather than a
    # mathematically flat key. Estimate that field from the four corners, while retaining
    # the requested key as the intended color reference.
    corners = np.concatenate([rgb[:8, :8].reshape(-1, 3), rgb[:8, -8:].reshape(-1, 3),
                              rgb[-8:, :8].reshape(-1, 3), rgb[-8:, -8:].reshape(-1, 3)])
    background = np.median(corners, axis=0)
    vector = foreground - background
    alpha = np.clip(np.sum((rgb - background) * vector, axis=2) /
                    np.maximum(np.sum(vector * vector, axis=2), 1e-8), 0, 1)
    alpha[core] = 1
    pure_background = np.linalg.norm(rgb - background, axis=2) < 0.10
    alpha[pure_background] = 0
    recovered = np.clip((rgb - (1 - alpha[:, :, None]) * background) /
                        np.maximum(alpha[:, :, None], 1 / 255), 0, 1)
    recovered[core] = rgb[core]
    recovered[alpha == 0] = 0
    pixels = np.dstack([np.round(recovered[:, :, order] * 255), np.round(alpha * 255)]).astype('uint8')
    # Remove a narrow matte fringe that can survive chroma
    # unmixing on opaque props. Restrict this to a few pixels next to the
    # transparent boundary so genuinely purple interior material/effects stay.
    # Work in the same canonical magenta channel order as the unmixing above.
    # Otherwise cyan/yellow jobs erase genuine purple foreground edges.
    final_rgb = pixels[:, :, :3][:, :, order].astype(float)
    final_alpha = pixels[:, :, 3]
    red, green, blue = final_rgb.transpose(2, 0, 1)
    edge = ndimage.distance_transform_edt(final_alpha > 0) <= 3.0
    magenta_fringe = (edge & (blue >= red * 0.72) &
                      (green <= red * 0.70) & (blue > 24) & (final_alpha > 0))
    pixels[magenta_fringe, 3] = 0
    return Image.fromarray(pixels), {'method': 'soft_chroma_estimate_no_erosion',
                                   'limitation': 'Single-matte estimate with narrow matte-fringe cleanup; visual review required'}


def register_cell(image, job, cell, sheet_size, adjust=(1., 0., 0.)):
    """Invert the prepared native rectangle, never the generated foreground bounds.

    SCALE expands art about the reference cell center, then DX/DY translate it in reference
    pixels. The same correction applies to every cell. Premultiplied sampling avoids matte bleed.
    """
    scale, dx, dy = adjust
    if not np.isfinite(adjust).all() or scale <= 0:
        raise ValueError('Registration needs a positive finite scale and finite translation')
    if not cleanup.alpha_bounds(image):
        raise ValueError('Generated cell has no visible foreground')
    bounds = cell['cell']
    rectangle = cell['native_rectangle']
    sx = sheet_size[0] / job['sheet_size'][0]
    sy = sheet_size[1] / job['sheet_size'][1]
    origin = [round(bounds[0] * sx), round(bounds[1] * sy)]
    output_size = tuple(n * 2 for n in cell['native_size'])
    # A source-native pixel's position is defined by the prepared rectangle, including its
    # rounding at preparation time. Invert an optional COMMON correction about the cell center.
    centers = [(bounds[i] + bounds[i + 2]) / 2 for i in range(2)]
    shifts = [dx, dy]
    starts = [centers[i] + (rectangle[i] - centers[i] - shifts[i]) / scale for i in range(2)]
    steps = [(rectangle[i + 2] - rectangle[i]) / output_size[i] / scale for i in range(2)]
    box = (starts[0] * sx - origin[0], starts[1] * sy - origin[1],
           (starts[0] + steps[0] * output_size[0]) * sx - origin[0],
           (starts[1] + steps[1] * output_size[1]) * sy - origin[1])
    # EXTENT transform samples a small interpolation kernel even for large reductions,
    # aliasing fine leaf/material detail. Resize filters over the reduction footprint.
    # Pad explicitly so fractional/outside crop bounds retain their original placement.
    left, top = min(0, int(np.floor(box[0]))), min(0, int(np.floor(box[1])))
    right = max(image.width, int(np.ceil(box[2])))
    bottom = max(image.height, int(np.ceil(box[3])))
    padded = Image.new('RGBA', (right - left, bottom - top))
    padded.paste(image, (-left, -top))
    sample_box = (box[0] - left, box[1] - top, box[2] - left, box[3] - top)
    output = padded.convert('RGBa').resize(output_size, Image.Resampling.LANCZOS,
                                          box=sample_box).convert('RGBA')
    # Inspect clipping before extraction; fitting a truncated silhouette afterward would hide it.
    alpha = np.array(image)[:, :, 3]
    yy, xx = np.nonzero(alpha >= 192)
    outside = (xx + .5 < box[0]) | (xx + .5 >= box[2]) | (yy + .5 < box[1]) | (yy + .5 >= box[3])
    return output, {'method': 'native_rectangle_inverse_v2',
                    'resampling': 'premultiplied_lanczos_resize',
                    'source_pixels_per_output_pixel': [steps[0] * sx, steps[1] * sy],
                    'job_adjust': list(adjust), 'sample_box': list(box),
                    'solid_pixels_outside_canvas_fraction': float(outside.mean()) if len(outside) else 0.}


def decontaminate_campfire_smoke(image):
    """Remove clearly magenta-biased smoke hallucination while retaining flame/wood colors.

    Campfire's native smoke is neutral gray. This narrow correction only touches the upper
    smoke region when both red and blue dominate green; orange flame and brown logs remain.
    """
    pixels = np.array(image)
    rgb = pixels[:, :, :3].astype(np.int16)
    r, g, b = rgb.transpose(2, 0, 1)
    upper = np.indices(r.shape)[0] < round(r.shape[0] * .70)
    purple = upper & (np.minimum(r, b) - g > 12) & (b > r * .70) & (r > 70) & (pixels[:, :, 3] > 8)
    if np.any(purple):
        luminance = np.clip(.2126 * r + .7152 * g + .0722 * b, 0, 255)
        rgb[purple, 0] = np.clip(luminance[purple] * .92, 0, 255)
        rgb[purple, 1] = np.clip(luminance[purple] * .96, 0, 255)
        rgb[purple, 2] = np.clip(luminance[purple], 0, 255)
        pixels[:, :, :3] = rgb.astype(np.uint8)
    return Image.fromarray(pixels), int(purple.sum())


def has_checkerboard_backdrop(image):
    """Return true when an opaque RGB sheet has a baked gray checker preview."""
    if image.mode == 'RGBA' and image.getchannel('A').getextrema()[0] < 255:
        return False
    sample = np.array(image.convert('RGB'))
    border = np.concatenate((sample[:8].reshape(-1, 3), sample[-8:].reshape(-1, 3),
                             sample[:, :8].reshape(-1, 3), sample[:, -8:].reshape(-1, 3)))
    gray = border[(border.max(axis=1) - border.min(axis=1)) < 8]
    # Gray material reaching a magenta sheet edge is not a checkerboard. Require a predominantly
    # neutral border with two substantial, well-separated flat levels rather than arbitrary texture.
    if len(gray) < max(32, len(border) * .70):
        return False
    histogram = np.bincount(np.round(gray.mean(axis=1)).astype(np.uint8), minlength=256)
    windows = np.convolve(histogram, np.ones(7, dtype=int), mode='same')
    first = int(windows.argmax())
    first_count = int(windows[first])
    windows[max(0, first - 19):min(256, first + 20)] = 0
    second_count = int(windows.max())
    return min(first_count, second_count) >= len(gray) * .20 and first_count + second_count >= len(gray) * .70


def process(job, sources, raw, directory, adjust=(1., 0., 0.), mask_path=None, landmarks=None):
    directory.mkdir(parents=True, exist_ok=True)
    sheet = Image.open(raw)
    # Image generators sometimes return a checkerboard preview baked into the RGB
    # pixels.  It is never a valid backdrop for this pipeline: require the
    # declared flat matte (or delivered alpha) instead of silently accepting it.
    if has_checkerboard_backdrop(sheet):
        raise ValueError('Opaque checkerboard backdrop detected; regenerate with flat pure magenta RGB(255,0,255)')
    expected = job['sheet_size'][0] / job['sheet_size'][1]
    if abs(sheet.width / sheet.height / expected - 1) > .04:
        raise ValueError('Returned sheet aspect differs by >4%; repair layout before slicing')
    soft = job['profile'] in ('soft_fx', 'animated_prop', 'water_prop', 'weather')
    has_alpha = sheet.mode == 'RGBA' and sheet.getchannel('A').getextrema()[0] < 255
    mask = None
    if mask_path:
        delivered_mask = Image.open(mask_path).convert('RGBA')
        mask = Image.alpha_composite(Image.new('RGBA', delivered_mask.size, (0, 0, 0, 255)),
                                     delivered_mask).convert('L')
    opaque_weather = job.get('layout_override', {}).get('opaque_weather_field', False)
    if opaque_weather and (job['profile'] != 'weather' or len(job['cells']) != 1 or mask is not None):
        raise ValueError('Opaque weather layout requires one weather field and no companion mask')
    if mask:
        if abs(mask.width / mask.height / (sheet.width / sheet.height) - 1) > .04:
            raise ValueError('Mask aspect ratio differs from RGB; repair mask registration')
        mask = mask.resize(sheet.size, Image.Resampling.BILINEAR)
    if job['matte_collision_fraction'] > .015 and not has_alpha and mask is None:
        raise ValueError('Key overlaps material colors: use payload --repair alpha_mask, record-mask, then process')
    report = {'checks_version': CHECKS_VERSION, 'raw': str(raw), 'raw_size': list(sheet.size),
              'landmarks': landmarks, 'frames': {}, 'warnings': []}
    if job.get('layout_override'):
        report['layout_override'] = job['layout_override']
    sx = sheet.width / job['sheet_size'][0]
    sy = sheet.height / job['sheet_size'][1]
    for cell in job['cells']:
        key = cell['asset']
        # Older frozen jobs predate the explicit cell field; recover it from the immutable source ledger.
        cell.setdefault('native_bounds', sources[key]['native_bounds'])
        bounds = cell['cell']
        raw_box = (round(bounds[0] * sx), round(bounds[1] * sy), round(bounds[2] * sx), round(bounds[3] * sy))
        crop = sheet.crop(raw_box)
        if opaque_weather:
            if bounds != [0, 0, *job['sheet_size']] or cell['native_rectangle'] != bounds:
                raise ValueError('Opaque weather layout must map the complete field without padding')
            clean, stats = preserve_field(crop, Image.open(HERE / sources[key]['native']))
        elif mask is not None and has_alpha:
            clean = crop.convert('RGBA')
            alpha = np.minimum(np.array(clean.getchannel('A')), np.array(mask.crop(raw_box)))
            clean.putalpha(Image.fromarray(alpha))
            stats = {'method': 'reviewed_mask_refines_delivered_alpha', 'mask': str(mask_path)}
        elif mask is not None:
            alpha = np.array(mask.crop(raw_box), dtype=float) / 255
            color = np.array(crop.convert('RGB'), dtype=float)
            recovered = (color - (1 - alpha[:, :, None]) * np.array(job['matte_rgb'])) / np.maximum(
                alpha[:, :, None], 1 / 255)
            recovered[alpha == 0] = 0
            clean = Image.fromarray(np.dstack([np.clip(np.round(recovered), 0, 255),
                                               np.round(alpha * 255)]).astype('uint8'))
            stats = {'method': 'reviewed_mask_with_color_unmixing', 'mask': str(mask_path)}
        else:
            clean, stats = clean_soft(crop, job['matte_rgb']) if soft else clean_solid(crop, job['matte_rgb'])
        clean.save(directory / (key + '.master.png'))
        output, registration = register_cell(clean, job, cell, sheet.size, adjust)
        if job['group'] == 'dec04':
            output, corrected_pixels = decontaminate_campfire_smoke(output)
            stats['campfire_smoke_decontamination_pixels'] = corrected_pixels
        output.save(directory / (key + '.png'))
        expected_bounds = sources[key]['native_bounds']
        actual_bounds = cleanup.alpha_bounds(output)
        placement, warnings = inspect_placement(Image.open(HERE / sources[key]['native']), output,
                                                 (landmarks or {}).get('regions', {}).get(key, []))
        if registration['solid_pixels_outside_canvas_fraction'] > .005:
            warnings.append('solid_art_outside_native_canvas')
        if not actual_bounds:
            warnings.append('empty_generated_frame')
        elif expected_bounds:
            delta = [actual_bounds[i] / 2 - expected_bounds[i] for i in range(4)]
            if max(abs(v) for v in delta) > max(3, max(cell['native_size']) * .04):
                warnings.append('visible_bounds_drift_review_alignment_or_shape')
        if min(registration['source_pixels_per_output_pixel']) < 1.0:
            warnings.append('generated_detail_below_2x_target_split_or_request_larger_sheet')
        pixels = np.array(output)
        visible = pixels[:, :, 3] > 0
        native_pixels = np.array(Image.open(HERE / sources[key]['native']))
        native_visible = native_pixels[:, :, 3] > 0
        coverage_ratio = float(visible.sum() / max(1, native_visible.sum() * 4))
        if coverage_ratio < .70 or coverage_ratio > 1.45:
            warnings.append('large_alpha_coverage_change_review_holes_or_halo')
        for warning in warnings:
            report['warnings'].append(key + ': ' + warning)
        report['frames'][key] = dict(cleanup=stats, registration=registration,
                                      placement=placement, native_size=cell['native_size'], physical_size=list(output.size),
                                      logical_pivot=[cell['native_size'][0] / 2,
                                                     cell['native_size'][1] / (2 if job['alignment'] == 'center' else 1)],
                                      native_bounds=expected_bounds, enhanced_bounds=actual_bounds,
                                      alpha_coverage_ratio=coverage_ratio, warnings=warnings)
    report['warnings'].extend(inspect_motion(report['frames']))
    (directory / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    review(job, sources, directory)
    return report


def check_existing(job, sources, directory, landmarks=None):
    """Review a previously exported full canvas without resampling or changing its pixels."""
    previous = read(directory / 'checks.json') if (directory / 'checks.json').exists() else {}
    report = dict(checks_version=CHECKS_VERSION, existing_canvas_review=True,
                  landmarks=landmarks, frames={}, warnings=[])
    # Draft-specific art defects remain unresolved until explicitly addressed by the reviewer.
    if previous.get('imported_benchmark_draft'):
        report['warnings'].extend(previous.get('warnings', []))
    for key in job['assets']:
        native = Image.open(HERE / sources[key]['native']).convert('RGBA')
        image = Image.open(directory / (key + '.png'))
        if image.mode != 'RGBA' or image.size != (native.width * 2, native.height * 2):
            raise ValueError('Existing export must already have its full native x2 RGBA canvas')
        placement, warnings = inspect_placement(native, image, (landmarks or {}).get('regions', {}).get(key, []))
        coverage = np.count_nonzero(np.array(image)[:, :, 3]) / max(1, 4 * np.count_nonzero(np.array(native)[:, :, 3]))
        if not .70 <= coverage <= 1.45:
            warnings.append('large_alpha_coverage_change_review_holes_or_halo')
        # Preserve extraction provenance when rechecking existing canvases. Rechecking alpha cannot
        # establish a master's resolution, and must not erase evidence of undersized sampling.
        registration = previous.get('frames', {}).get(key, {}).get('registration')
        report['frames'][key] = dict(placement=placement, warnings=warnings)
        if registration:
            report['frames'][key]['registration'] = registration
        report['warnings'].extend(key + ': ' + warning for warning in warnings)
    report['warnings'].extend(inspect_motion(report['frames']))
    (directory / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    review(job, sources, directory)
    return report


def review(job, sources, directory):
    keys = job['assets']
    for label, background in [('dark', (34, 39, 36)), ('light', (225, 227, 222))]:
        sheet = Image.new('RGB', (1000, 330 * len(keys)), background)
        draw = ImageDraw.Draw(sheet)
        for row, key in enumerate(keys):
            native = Image.open(HERE / sources[key]['native'])
            enhanced = Image.open(directory / (key + '.png'))
            factor = min(460 / native.width, 280 / native.height)
            size = max(1, round(native.width * factor)), max(1, round(native.height * factor))
            draw.text((10, row * 330 + 5), sources[key]['aliases'][0]['name'] + '  native / enhanced',
                      fill=(140, 145, 142))
            for column, im in enumerate((native, enhanced)):
                pic = im.convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA')
                sheet.paste(cleanup.composite(pic, background),
                            (column * 500 + (500 - size[0]) // 2, row * 330 + 320 - size[1]))
        sheet.save(directory / ('review_' + label + '.png'))
    # Native-size playback side by side, using table order and repeated frames, when present in this chunk.
    groups = read(HERE / 'groups.json')
    group = next(g for g in groups if g['sprite_id'] == job['sprite_id'])
    track = max(group['tracks'], key=lambda t: sum(f['asset'] in keys for f in t['timeline']))
    timeline = [f for f in track['timeline'] if f['asset'] in keys]
    if len(timeline) > 1:
        images = []
        w = max(sources[k]['native_size'][0] for k in keys) * 2
        h = max(sources[k]['native_size'][1] for k in keys) * 2
        for frame in timeline:
            key = frame['asset']
            canvas = Image.new('RGBA', (w * 2 + 12, h), (44, 48, 45, 255))
            for column, path in enumerate((HERE / sources[key]['native'], directory / (key + '.png'))):
                im = Image.open(path)
                if column == 0:
                    im = im.resize((im.width * 2, im.height * 2), Image.Resampling.NEAREST)
                y = (h - im.height) // 2 if job['alignment'] == 'center' else h - im.height
                canvas.alpha_composite(im, (column * (w + 12) + (w - im.width) // 2, y))
            images.append(canvas.convert('RGB'))
        # GIF is a review aid with rounded milliseconds, never the authoritative timing manifest.
        images[0].save(directory / 'motion.gif', save_all=True, append_images=images[1:], loop=0,
                       duration=[max(20, round(f['duration_ms'])) for f in timeline])
