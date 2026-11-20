"""Compose restored cobble artwork over native substrates and continue finished donor strips.

Only retained raw candidates are built. The partial manifest is not installation approval.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import json
import cv2
from PIL import ImageDraw
from scipy.ndimage import binary_closing, binary_fill_holes, distance_transform_edt, gaussian_filter, label, median_filter
from common import *

FOLDER = Path(__file__).resolve().parent
V1 = FOLDER.parent / 'v1'


def coverage(rgb):
    candidate = (rgb[:, :, 1] / np.maximum(rgb[:, :, 0], 1) > .77) & (rgb[:, :, 2] / np.maximum(rgb[:, :, 0], 1) > .58)
    candidate = binary_closing(np.pad(candidate, 12, mode='edge'), iterations=4)[12:-12, 12:-12]
    components, _ = label(candidate)
    counts = np.bincount(components.ravel()); counts[0] = 0
    return binary_fill_holes(components == counts.argmax())


def topology(mask):
    return {side: bool(values.mean() > .10) for side, values in
            [('N', mask[:4]), ('S', mask[-4:]), ('W', mask[:, :4]), ('E', mask[:, -4:])]}


def layer_from_rgb(rgb, mask, dirt):
    alpha = np.clip(gaussian_filter(mask.astype(float), .65), 0, 1)
    outside = distance_transform_edt(~mask)
    contact = np.clip((20 - outside) / 14, 0, 1)
    ratio = np.clip(rgb / np.maximum(dirt, 1), .4, 1.1)
    # RGB scalar bank field; unchanged earth must remain the authoritative material.
    shade = 1 + (ratio - 1) * contact[:, :, None]
    shade[mask] = 1
    return dict(rgb=rgb, alpha=alpha, shade=shade)


def compose_layer(layer, dirt):
    a = layer['alpha'][:, :, None]
    return layer['rgb'] * a + dirt * layer['shade'] * (1 - a)


def graft(layer, donors, sides):
    result = {k: v.copy() for k, v in layer.items()}
    for side, opened in sides.items():
        if not opened:
            continue
        donor = donors['drsrns' if side in 'NS' else 'drsrew']
        current_spans, donor_spans = [], []
        for depth in range(80):
            sample = 256 + depth if side in 'NW' else 255 - depth
            destination = depth if side in 'NW' else 511 - depth
            current_alpha = layer['alpha'][destination] if side in 'NS' else layer['alpha'][:, destination]
            donor_alpha = donor['alpha'][sample] if side in 'NS' else donor['alpha'][:, sample]
            current_span, donor_span = [np.flatnonzero(alpha > .5) for alpha in (current_alpha, donor_alpha)]
            assert len(current_span) and len(donor_span), (side, depth, 'missing road opening')
            current_spans.append(current_span[[0, -1]])
            donor_spans.append(donor_span[[0, -1]])
        current_spans = gaussian_filter(median_filter(np.asarray(current_spans, float), size=(11, 1), mode='nearest'), (5, 0))
        donor_spans = gaussian_filter(median_filter(np.asarray(donor_spans, float), size=(11, 1), mode='nearest'), (5, 0))
        for depth in range(80):
            sample = 256 + depth if side in 'NW' else 255 - depth
            destination = depth if side in 'NW' else 511 - depth
            weight = np.clip((80 - depth) / 40, 0, 1)
            weight = weight * weight * (3 - 2 * weight)
            current_lo, current_hi = current_spans[depth]
            donor_lo, donor_hi = donor_spans[depth]
            target_lo = current_lo * (1 - weight) + donor_lo * weight
            target_hi = current_hi * (1 - weight) + donor_hi * weight
            coordinates = np.arange(512)
            phase = (coordinates - target_lo) / max(target_hi - target_lo, 1)
            current_coordinates = current_lo + phase * (current_hi - current_lo)
            donor_coordinates = donor_lo + phase * (donor_hi - donor_lo)
            def sample_line(values, positions):
                if values.ndim == 1:
                    return np.interp(positions, coordinates, values)
                return np.stack([np.interp(positions, coordinates, values[:, c])
                                 for c in range(values.shape[1])], axis=1)
            for key in result:
                values = donor[key][sample] if side in 'NS' else donor[key][:, sample]
                target = result[key][destination] if side in 'NS' else result[key][:, destination]
                original = layer[key][destination] if side in 'NS' else layer[key][:, destination]
                # Both finished RGB contours follow the same interpolated outline.
                # Fading two differently placed outlines exposes loose stone fragments.
                proposal = sample_line(original, current_coordinates) * (1 - weight) + sample_line(values, donor_coordinates) * weight
                # At intersecting collars, the closest edge owns its boundary.
                # Never re-warp artwork already deformed by another side.
                other_distance = np.minimum(coordinates, 511 - coordinates)
                selected = other_distance >= depth
                target[selected] = proposal[selected]
    return result


def main():
    dirt = read(M / 'materials/dirt.png'); grey = read(M / 'materials/grey_dirt.png')
    donors = {}
    for name in ('drsrew', 'drsrns'):
        rgb = read(V1 / 'donors/authoring' / (name + '.png'))
        mask = read(V1 / 'donors/masks' / (name + '.png'))[:, :, 0] > 127
        donors[name] = layer_from_rgb(rgb, mask, dirt)
    layers = dict(donors)
    records = {}
    yy, xx = np.mgrid[:512, :512].astype('float32')
    for raw in sorted((FOLDER / 'raw').glob('*.png')):
        name = raw.stem
        original = read(P / 'references' / (name + '.png'), 512)
        generated = read(raw, 512)
        old_mask, new_mask = coverage(original), coverage(generated)
        # Register the broad footprint; surface grain must not drive width changes.
        a, b = [seams.byte(gaussian_filter(mask.astype(float), 7) * 255) for mask in (old_mask, new_mask)]
        flow = cv2.calcOpticalFlowFarneback(a, b, None, .5, 5, 65, 10, 7, 1.5, 0)
        flow = gaussian_filter(flow, (5, 5, 0))
        aligned = cv2.remap(generated.astype('float32'), xx + flow[:, :, 0], yy + flow[:, :, 1],
                            cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        mask = coverage(aligned)
        native_stones, ai_stones = original[old_mask], aligned[mask]
        aligned = np.clip((aligned - ai_stones.mean(0)) * np.clip(native_stones.std(0) / np.maximum(ai_stones.std(0), 1), .65, 1.35) + native_stones.mean(0), 0, 255)
        layers[name] = layer_from_rgb(aligned, mask, dirt)
        records[name] = dict(raw_sha256=sha(raw), max_registration_pixels=float(np.max(np.linalg.norm(flow, axis=2))))
    reports = []
    inv = json.loads((P / 'inventory.json').read_text())
    requested = [r for r in inv['tiles'] if r['family'] in ('roads_dirt', 'roads_grey')]
    sheet = Image.new('RGB', (768, 280 * sum(('drsr' + r['name'][4:]) in layers for r in requested)), '#202933')
    draw = ImageDraw.Draw(sheet)
    for r in requested:
        name = r['name']; source = 'drsr' + name[4:]
        if source not in layers:
            continue
        # Source stones share their native designs across substrates; final openings
        # use one finished donor contract instead of retaining native 2-4px misalignments.
        native = read(P / 'references' / (source + '.png'), 512)
        sides = topology(coverage(native))
        final = graft(layers[source], donors, sides)
        pixels = compose_layer(final, grey if r['family'] == 'roads_grey' else dirt)
        runtime = seams.reduce(seams.pad(pixels, 'wrap'))
        save(FOLDER / 'authoring' / (name + '.png'), pixels)
        save(FOLDER / 'runtime' / (name + '.png'), runtime)
        save(FOLDER / 'masks' / (name + '.png'), final['alpha'] * 255)
        (FOLDER / 'fields').mkdir(exist_ok=True)
        np.savez_compressed(FOLDER / 'fields' / (name + '.npz'), **final)
        reports.append(dict(name=name, source=source, topology=sides, family=r['family'],
                            runtime_sha256=sha(FOLDER / 'runtime' / (name + '.png')),
                            field_sha256=sha(FOLDER / 'fields' / (name + '.npz')),
                            generation=records.get(source, dict(donor=True))))
        row = len(reports) - 1
        for col, path in enumerate((P / 'references' / (name + '.png'), FOLDER / 'runtime' / (name + '.png'), FOLDER / 'masks' / (name + '.png'))):
            sheet.paste(Image.open(path).convert('RGB').resize((256, 256)), (col * 256, row * 280 + 24))
            draw.text((col * 256 + 3, row * 280 + 5), name + ' ' + ['native', 'candidate x2', 'coverage'][col], fill='white')
    sheet.save(FOLDER / 'comparison.png')
    (FOLDER / 'build.json').write_text(json.dumps(dict(status='partial_candidate_road_set', tiles=reports,
                                                       missing=[r['name'] for r in requested if 'drsr' + r['name'][4:] not in layers]), indent=2) + '\n')
    print('Built', len(reports), 'cobble road candidates; missing', len(requested) - len(reports))


if __name__ == '__main__': main()
