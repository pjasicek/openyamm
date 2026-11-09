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
    # Quilt complete finished artwork. Stretching a straight donor into diagonal
    # stones folds their shapes; choose a low-error cut through the overlap instead.
    result = {k: v.copy() for k, v in layer.items()}
    dirt = read(M / 'materials/dirt.png')
    length, minimum = 128, 24
    for side, opened in sides.items():
        if not opened:
            continue
        donor = donors['drsrns' if side in 'NS' else 'drsrew']
        samples = 256 + np.arange(length) if side in 'NW' else 255 - np.arange(length)
        destinations = np.arange(length) if side in 'NW' else 511 - np.arange(length)
        strips, current = {}, {}
        for key in result:
            strips[key] = donor[key][samples].copy() if side in 'NS' else np.swapaxes(donor[key][:, samples], 0, 1).copy()
            current[key] = result[key][destinations].copy() if side in 'NS' else np.swapaxes(result[key][:, destinations], 0, 1).copy()
        earth = dirt[destinations] if side in 'NS' else np.swapaxes(dirt[:, destinations], 0, 1)
        source_rgb, target_rgb = [compose_layer(fields, earth) for fields in (current, strips)]
        cost = np.mean((source_rgb - target_rgb) ** 2, axis=2)
        cost += 20000 * (current['alpha'] - strips['alpha']) ** 2
        cost = cost[minimum:length - 4].T
        distance = cost.copy()
        back = np.zeros(cost.shape, dtype='int16')
        for cross in range(1, 512):
            previous = np.pad(distance[cross - 1], (2, 2), constant_values=np.inf)
            choices = np.stack([previous[offset:offset + cost.shape[1]] for offset in range(5)])
            best = np.argmin(choices, axis=0)
            distance[cross] += np.min(choices, axis=0)
            back[cross] = np.arange(cost.shape[1]) + best - 2
        seam = np.empty(512, int); seam[-1] = np.argmin(distance[-1])
        for cross in range(510, -1, -1):
            seam[cross] = back[cross + 1, seam[cross + 1]]
        seam += minimum
        weight = np.clip((seam[None, :] - np.arange(length)[:, None] + 2) / 4, 0, 1)
        weight = weight * weight * (3 - 2 * weight)
        for key in result:
            w = weight[:, :, None] if current[key].ndim == 3 else weight
            values = current[key] * (1 - w) + strips[key] * w
            if side in 'NS': result[key][destinations] = values
            else: result[key][:, destinations] = np.swapaxes(values, 0, 1)
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
