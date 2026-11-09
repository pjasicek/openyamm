"""Insert four imagegen outline repairs with locked shared borders and native interiors."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / 'v1'))
import json
import shutil
from PIL import ImageDraw
from scipy.ndimage import distance_transform_edt, gaussian_filter
from common import *
from finish_donors import insert
from compose import coverage, layer_from_rgb, compose_layer

F = HERE / 'outline_repairs'
DEST = HERE.parent / 'v3'


def main():
    build = json.loads((HERE / 'build.json').read_text())
    inputs = {r['name']: r for r in json.loads((F / 'inputs.json').read_text())}
    dirt = read(M / 'materials/dirt.png'); grey = read(M / 'materials/grey_dirt.png')
    yy, xx = np.mgrid[:512, :512]; border = np.minimum.reduce([xx, yy, 511 - xx, 511 - yy])
    results = {}
    sheet = Image.new('RGB', (1024, 1120), '#202933'); draw = ImageDraw.Draw(sheet)
    for row, (name, record) in enumerate(inputs.items()):
        path = HERE / 'authoring' / (name + '.png')
        assert sha(path) == record['source_sha256'], name
        original = read(path)
        painted = read(F / 'raw' / (name + '.png'), 512)
        old = np.load(HERE / 'fields' / (name + '.npz'))
        old_mask = old['alpha'] > .5
        requested = read(F / 'inputs' / (name + '_coverage.png'))[:, :, 0] > 127
        new_mask = coverage(painted)
        domain = (border > 8) & (border < 140) & (distance_transform_edt(~(old_mask | requested | new_mask)) < 24)
        pixels = insert(original, painted, domain)
        # Coverage is the reviewed footprint guide. Reclassifying dark painted
        # joints by colour creates false earth holes in the repaired stone strip.
        new_layer = layer_from_rgb(pixels, requested, dirt)
        alpha = old['alpha'].copy(); alpha[domain] = new_layer['alpha'][domain]
        for prefix, substrate in [('drsr', dirt), ('gdrd', grey)]:
            tile = prefix + name[4:]
            base = read(HERE / 'authoring' / (tile + '.png'))
            mapped = pixels if prefix == 'drsr' else compose_layer(new_layer, substrate)
            final = base.copy(); final[domain] = mapped[domain]
            assert np.array_equal(final[~domain], base[~domain])
            results[tile] = dict(pixels=final, alpha=alpha.copy(), repair=name,
                                 protected_fraction=float(np.mean(~domain)), raw_sha256=sha(F / 'raw' / (name + '.png')))
        for col, im in enumerate((original, painted, pixels, alpha[:, :, None].repeat(3, 2) * 255)):
            sheet.paste(Image.fromarray(seams.byte(im)).resize((256, 256)), (col * 256, row * 280 + 24))
            draw.text((col * 256 + 3, row * 280 + 5), name + ' ' + ['before', 'AI repair', 'local insertion', 'coverage'][col], fill='white')
    for record in build['tiles']:
        name = record['name']
        for folder in ('authoring', 'runtime', 'masks', 'fields'): (DEST / folder).mkdir(parents=True, exist_ok=True)
        if name not in results:
            for folder in ('authoring', 'runtime', 'masks'): shutil.copy2(HERE / folder / (name + '.png'), DEST / folder / (name + '.png'))
            shutil.copy2(HERE / 'fields' / (name + '.npz'), DEST / 'fields' / (name + '.npz'))
        else:
            result = results[name]
            save(DEST / 'authoring' / (name + '.png'), result['pixels'])
            save(DEST / 'runtime' / (name + '.png'), seams.reduce(seams.pad(result['pixels'], 'wrap')))
            save(DEST / 'masks' / (name + '.png'), result['alpha'] * 255)
            np.savez_compressed(DEST / 'fields' / (name + '.npz'), rgb=result['pixels'], alpha=result['alpha'])
            record['outline_repair'] = {k: v for k, v in result.items() if k not in ('pixels', 'alpha')}
        record['runtime_sha256'] = sha(DEST / 'runtime' / (name + '.png'))
        record['field_sha256'] = sha(DEST / 'fields' / (name + '.npz'))
    for record in build['tiles']:
        if record['family'] != 'roads_grey':
            continue
        name = record['name']; source = 'drsr' + name[4:]
        brown = read(DEST / 'authoring' / (source + '.png'))
        alpha = np.load(DEST / 'fields' / (source + '.npz'))['alpha']
        outside = distance_transform_edt(alpha <= .5)
        contact = np.clip((20 - outside) / 14, 0, 1)
        ratio = np.clip(brown.mean(2) / np.maximum(dirt.mean(2), 1), .4, 1.05)
        shade = 1 + (ratio - 1) * contact
        a = alpha[:, :, None]
        # A rounded AI stone can uncover brown earth inside the old footprint.
        # Keep that fringe on the grey substrate rather than carrying brown soil.
        chroma = (brown[:, :, 0] - brown[:, :, 2]) / np.maximum(brown.mean(2), 1)
        fringe = np.clip((20 - distance_transform_edt(alpha > .5)) / 8, 0, 1)
        earth = np.clip((chroma - .5) / .3, 0, 1) * fringe
        foreground = brown * (1 - earth[:, :, None]) + grey * shade[:, :, None] * earth[:, :, None]
        pixels = foreground * a + grey * shade[:, :, None] * (1 - a)
        save(DEST / 'authoring' / (name + '.png'), pixels)
        save(DEST / 'runtime' / (name + '.png'), seams.reduce(seams.pad(pixels, 'wrap')))
        save(DEST / 'masks' / (name + '.png'), alpha * 255)
        np.savez_compressed(DEST / 'fields' / (name + '.npz'), rgb=foreground, alpha=alpha, shade=shade)
        record['grey_contact'] = 'Scalar brightness ratio: preserves grey substrate chroma'
        record['runtime_sha256'] = sha(DEST / 'runtime' / (name + '.png'))
        record['field_sha256'] = sha(DEST / 'fields' / (name + '.npz'))
    # Road coverage is directional: the opposite side of the same tile is not
    # necessarily its neighbour. Extend finished road art in the filter gutter,
    # while the exposed periodic earth retains its proper wrapped phase.
    for record in build['tiles']:
        name = record['name']
        pixels = read(DEST / 'authoring' / (name + '.png'))
        alpha = np.load(DEST / 'fields' / (name + '.npz'))['alpha']
        substrate = grey if record['family'] == 'roads_grey' else dirt
        padded = seams.pad(pixels, 'edge')
        padded += (seams.pad(substrate, 'wrap') - seams.pad(substrate, 'edge')) * (1 - seams.pad(alpha, 'edge')[:, :, None])
        save(DEST / 'runtime' / (name + '.png'), seams.reduce(padded))
        record['runtime_sha256'] = sha(DEST / 'runtime' / (name + '.png'))
    build.update(status='complete_cobble_candidates_outline_review_pending', source_build_sha256=sha(HERE / 'build.json'))
    (DEST / 'build.json').write_text(json.dumps(build, indent=2) + '\n')
    sheet.save(DEST / 'outline_comparison.png')
    print('Built36 cobble candidates, with8 local outline repairs across two substrates')


if __name__ == '__main__': main()
