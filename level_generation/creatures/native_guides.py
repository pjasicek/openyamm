"""Stage one base palette of geometry-preserving guides; never generate or replace masters.

Requires an existing sources.json and exported family manifest. Outputs are native-resolution
generation references, not restored art or a runtime atlas. No existing package is modified.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from exact_placement import native_offset, validate_animation_bindings


REPO = Path(__file__).resolve().parents[2]
SETTINGS = {
    'fine_sigma_px': 1.5,
    'coarse_sigma_px': 4.0,
    'contrast_threshold': 0.012,
    'contrast_range': 0.08,
    'outline_width_px': 1.45,
    'outline_darkening': 0.36,
    'crease_darkening': 0.48,
    'ridge_brightening': 0.13,
}


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def guide_channels(image):
    """R: inward silhouette, G: native dark creases, B: native bright ridges.

    Alpha-normalized smoothing excludes transparent RGB. Smoothing is used only to
    locate existing contrast: output color is always scaled original RGB, never blurred.
    This is contrast detection, not anatomical segmentation or a reconstructed skeleton.
    """
    rgba = np.asarray(image)
    inside = rgba[:, :, 3] > 0
    luma = rgba[:, :, :3].astype(float) @ np.array([.2126, .7152, .0722]) / 255

    def smooth(sigma):
        weight = ndimage.gaussian_filter(inside.astype(float), sigma)
        return ndimage.gaussian_filter(luma * inside, sigma) / np.maximum(weight, 1e-8)

    fine = smooth(SETTINGS['fine_sigma_px'])
    coarse = smooth(SETTINGS['coarse_sigma_px'])
    distance = ndimage.distance_transform_edt(inside)
    interior = np.clip((distance - 1) / 2, 0, 1)
    threshold = SETTINGS['contrast_threshold']
    span = SETTINGS['contrast_range']
    crease = np.clip((coarse - fine - threshold) / span, 0, 1) * interior
    ridge = np.clip((fine - coarse - threshold) / span, 0, 1) * interior
    # Suppress outline darkening on isolated one-pixel tips without eroding their alpha.
    thickness = np.clip((ndimage.maximum_filter(distance, size=5) - 1) / 2, 0, 1)
    outline = (distance <= SETTINGS['outline_width_px']) * inside * thickness
    return Image.fromarray(np.round(np.stack([outline, crease, ridge], axis=2) * 255).astype(np.uint8))


def apply_guides(image, guides):
    rgba = np.array(image)
    coverage = np.asarray(guides).astype(float) / 255
    outline, crease, ridge = coverage.transpose(2, 0, 1)
    dark = np.maximum(outline * SETTINGS['outline_darkening'], crease * SETTINGS['crease_darkening'])
    gain = 1 - dark + ridge * SETTINGS['ridge_brightening']
    rgb = rgba[:, :, :3].astype(float)
    # One scalar per pixel preserves each palette's hue, including pale protected details.
    # Cap the scalar before rounding so channel clipping cannot introduce a new hue.
    gain = np.minimum(gain, 255 / np.maximum(rgb.max(axis=2), 1))
    rgba[:, :, :3] = np.round(rgb * gain[:, :, None]).astype(np.uint8)
    rgba[np.asarray(image)[:, :, 3] == 0] = np.asarray(image)[np.asarray(image)[:, :, 3] == 0]
    return Image.fromarray(rgba)


def native_image(source, palette, canvas, anchor):
    with Image.open(REPO / source['path']) as bmp:
        if bmp.mode != 'P' or list(bmp.size) != source['size']:
            raise ValueError('Expected the recorded indexed native BMP: ' + source['path'])
        index = np.array(bmp)
    image = Image.fromarray(np.dstack([palette[index], (index != 0).astype(np.uint8) * 255]))
    offset = native_offset(canvas, image.size, anchor)
    if any(value != int(value) for value in offset):
        raise ValueError('Native 1x canvas cannot represent this half-pixel offset; use a separate 2x workflow')
    result = Image.new('RGBA', canvas)
    result.paste(image, tuple(int(value) for value in offset))
    return result, offset


def contact(path, rows, canvas):
    """Each row is (label, [(image, label), ...]); native-scale full-frame comparisons."""
    width, height = canvas
    columns = max(len(pictures) for _, pictures in rows)
    result = Image.new('RGB', (columns * width, len(rows) * (height + 24)), (39, 44, 51))
    draw = ImageDraw.Draw(result)
    for row, (name, pictures) in enumerate(rows):
        for column, (picture, title) in enumerate(pictures):
            x, y = column * width, row * (height + 24)
            draw.text((x + 6, y + 5), name + ' / ' + title, fill='white')
            result.paste(picture, (x, y + 24), picture if picture.mode == 'RGBA' else None)
    result.save(path)


def prepare(project, manifest_path, output, preserve_actions):
    sources_path = project / 'sources.json'
    sources = read(sources_path)
    original = read(manifest_path)
    if output.exists():
        raise ValueError('Choose a new output directory; existing work is never overwritten')
    if set(sources['sources']) != set(original['frames']):
        raise ValueError('Native and manifest frame sets differ')
    errors = validate_animation_bindings(original)
    if errors:
        raise ValueError(errors)
    base = str(sources['base_palette'])
    if base not in original['variants']:
        raise ValueError('Native base palette is absent from the manifest')
    palette_ids = [base]
    preserved = set()
    for action in preserve_actions:
        animations = original['animations_by_palette'][base]
        if action not in animations:
            raise ValueError('Unknown preserved action: ' + action)
        preserved.update(step['frame'] for steps in animations[action]['views'].values() for step in steps)
    # Snapshot all existing project files so guides cannot silently modify accepted work.
    protected = {path: digest(path) for path in project.rglob('*') if path.is_file()}
    for record in [*sources['sources'].values(), sources['palette_sources'][base]]:
        path = REPO / record['path']
        if digest(path) != record['sha256']:
            raise ValueError('Source hash mismatch: ' + str(path))
        protected[path] = record['sha256']
    palettes = {key: np.frombuffer((REPO / sources['palette_sources'][key]['path']).read_bytes()[:768],
                                  np.uint8).reshape(256, 3) for key in palette_ids}
    for folder in ['native_variants', 'guides', 'review']:
        (output / folder).mkdir(parents=True)
    canvas = original['logical_canvas']
    anchor = original['anchor']
    frames, artifacts, originals, guided = {}, {}, {}, {}
    edge_candidates = []
    changed_pixels = 0
    for name, frame in original['frames'].items():
        source = sources['sources'][name]
        if 'fixed_palette' in source:
            raise ValueError('Fixed-palette effect frames require a separately scoped guide pass')
        native, offset = native_image(source, palettes[base], canvas, anchor)
        if offset != frame['native_offset'][:2]:
            raise ValueError('Existing package needs explicit anchor repair: ' + name)
        guides = Image.new('RGB', native.size) if name in preserved else guide_channels(native)
        guide_path = Path('guides') / (name + '.png')
        guides.save(output / guide_path)
        artifacts[guide_path.as_posix()] = digest(output / guide_path)
        images = {}
        for palette in palette_ids:
            image, _ = native_image(source, palettes[palette], canvas, anchor)
            with Image.open(manifest_path.parent / 'native_variants' / f'{name}_{palette}.png') as reference:
                if not np.array_equal(np.asarray(image), np.asarray(reference)):
                    raise ValueError('Direct native decoding differs from existing original: ' + name + '/' + palette)
            result = apply_guides(image, guides)
            relative = Path('native_variants') / f'{name}_{palette}.png'
            path = output / relative
            result.save(path)
            # Validate saved pixels, not just the in-memory computation.
            with Image.open(path) as saved:
                before, after = np.asarray(image), np.asarray(saved)
                if saved.size != image.size or not np.array_equal(after[:, :, 3], before[:, :, 3]):
                    raise ValueError('Geometry changed: ' + str(relative))
                if not np.array_equal(after, np.asarray(result)):
                    raise ValueError('Saved RGB differs: ' + str(relative))
                inside = before[:, :, 3] > 0
                if not np.array_equal(after[~inside], before[~inside]):
                    raise ValueError('Transparent padding changed: ' + str(relative))
                if name in preserved and not np.array_equal(after, before):
                    raise ValueError('Preserved action changed: ' + str(relative))
                changed_pixels += int(np.count_nonzero(np.any(before[:, :, :3] != after[:, :, :3], axis=2)))
                band = inside & (ndimage.distance_transform_edt(inside) <= 4)
                # Cyan was the native reference matte. Score changes only, so intended
                # blue palette colors are not mistaken for newly introduced spill.
                def cyan(rgb):
                    rgb = rgb.astype(float)
                    return np.maximum(0, np.minimum(rgb[:, :, 1], rgb[:, :, 2]) - rgb[:, :, 0])
                increase = np.where(band, cyan(after) - cyan(before), -np.inf)
                y, x = np.unravel_index(np.argmax(increase), increase.shape)
                edge_candidates.append((float(increase[y, x]), name, palette, int(x), int(y)))
            images[palette] = relative.as_posix()
            artifacts[relative.as_posix()] = digest(path)
            originals[name, palette], guided[name, palette] = image, result
        frames[name] = {key: frame[key] for key in ['source', 'source_canvas', 'native_offset', 'referenced']}
        frames[name].update(source_sha256=source['sha256'], images=images, guide=guide_path.as_posix(),
                            processing='native_bypass' if name in preserved else 'contrast_guides')

    # Keep native manifest order, which groups actions and stored views; all frames are reviewed.
    names = list(frames)
    for start in range(0, len(names), 4):
        rows = [(name, [(originals[name, base], 'native'), (guided[name, base], 'guided')])
                for name in names[start:start + 4]]
        contact(output / 'review' / f'sequence_{start // 4 + 1:02d}.png', rows, canvas)
    representative = [names[0], names[2], names[-1]]
    contact(output / 'review/base.png',
            [(name, [(guided[name, palette], original['variants'][palette]['name']) for palette in palette_ids])
             for name in representative], canvas)
    edge_rows = []
    for score, name, palette, x, y in sorted(edge_candidates, reverse=True)[:6]:
        box = (x - 20, y - 20, x + 20, y + 20)
        pictures = []
        for background in [(30, 30, 30), (238, 238, 238)]:
            for image, label in [(originals[name, palette], 'native'), (guided[name, palette], 'guided')]:
                patch = image.crop(box)
                composite = Image.new('RGBA', patch.size, (*background, 255))
                composite.alpha_composite(patch)
                pictures.append((composite.convert('RGB').resize((160, 160), Image.Resampling.NEAREST), label))
        edge_rows.append((f'{name}/{palette} delta {score:g}', pictures))
    contact(output / 'review/edges.png', edge_rows, [160, 160])
    if any(digest(path) != sha for path, sha in protected.items()):
        raise ValueError('Existing project or native source changed during guide export')

    # Reuse native animation metadata verbatim; deliberately omit restored atlas/registration fields.
    manifest = {key: original[key] for key in ['schema_version', 'creature', 'logical_canvas', 'logical_pivot',
                'anchor', 'animations', 'animations_by_palette', 'native_group_bindings', 'native_frame_scale']}
    manifest['animations_by_palette'] = {base: original['animations_by_palette'][base]}
    if base in original['native_group_bindings']:
        manifest['native_group_bindings'] = {base: original['native_group_bindings'][base]}
    else:
        groups = {animation['native_group'] for animation in original['animations_by_palette'][base].values()}
        manifest['native_group_bindings'] = {key: original['native_group_bindings'][key] for key in groups}
    manifest.update(
        asset_role='native_generation_guides', installed=False, pixels_per_logical_pixel=1,
        quality_status='static_checked_visual_review_pending',
        variants={base: {'name': original['variants'][base]['name'], 'exact_base_bypass': True}},
        base_palette=base, frames=frames, pixel_aliases=sources['pixel_aliases'], artifacts=artifacts,
        provenance={
            'sources': {'path': str(sources_path.relative_to(REPO)), 'sha256': digest(sources_path)},
            'native_manifest': {'path': str(manifest_path.relative_to(REPO)), 'sha256': digest(manifest_path)},
            'palette_sources': {base: sources['palette_sources'][base]},
            'processor': {'path': str(Path(__file__).resolve().relative_to(REPO)), 'sha256': digest(Path(__file__))},
        },
        processing={
            'method': 'alpha-normalized multiscale luminance guides; scalar RGB gain; native alpha bypass',
            'settings': SETTINGS,
            'guide_channels': ['inward silhouette', 'dark native crease', 'bright native ridge'],
            'guide_palette': base, 'guide_reuse': 'one guide set for the base palette only',
            'geometry_transform': 'identity; no resampling, cropping, displacement or alpha filtering',
            'preserved_actions': preserve_actions,
            'preserved_frames': sorted(preserved),
        },
        validation={
            'saved_images_checked': len(frames) * len(palette_ids), 'changed_rgb_pixels': changed_pixels,
            'guided_frames': len(frames) - len(preserved), 'unchanged_frames': len(preserved),
            'native_decoding_matches_existing_originals': True,
            'dimensions_alpha_offsets_pivot_unchanged': True, 'animation_bindings_checked': True,
            'existing_project_and_native_files_unchanged': len(protected),
            'edge_band_px': 4, 'edge_scan_frames_and_palettes': len(edge_candidates),
            'maximum_cyan_excess_increase_rgb_units': max(row[0] for row in edge_candidates),
            'edge_interpretation': 'Ranking only; palette hues preserved by scalar RGB gain, rounded once.',
        },
        memory_bytes={
            'native_variants_rgba': len(frames) * len(palette_ids) * canvas[0] * canvas[1] * 4,
            'shared_guides_rgb': len(frames) * canvas[0] * canvas[1] * 3,
            'png_disk': sum((output / path).stat().st_size for path in artifacts),
        },
        limitations=[
            'Source-only 1x references, not enhanced masters; no new generated detail.',
            'Guides emphasize existing contrast; they do not infer hidden anatomy or guarantee later AI proportions.',
            'Native scale texture and existing image artifacts are retained.',
        ],
        generation_guidance='Use these originals as pose, proportion and placement authority for future masters. '
                            'Guides mark existing boundaries, not additional anatomy. Preserve limb thickness, '
                            'joint positions, wing roots and torso proportions across frames.',
    )
    write(output / 'manifest.json', manifest)
    print(json.dumps({'output': str(output), 'frames': len(frames), 'variants': len(palette_ids),
                      'images': len(frames) * len(palette_ids), 'validation': manifest['validation']}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('--manifest', type=Path, required=True, help='Existing family manifest, relative to project')
    parser.add_argument('--output', type=Path, required=True, help='New directory, relative to project')
    parser.add_argument('--preserve-actions', nargs='*', default=[],
                        help='Copy these native actions unchanged, e.g. disintegration effects')
    args = parser.parse_args()
    project = args.project.resolve()
    prepare(project, project / args.manifest, project / args.output, args.preserve_actions)


if __name__ == '__main__':
    main()
