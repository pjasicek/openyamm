"""Locally insert an AI stone-edge repair and propagate its shared NS road openings."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / 'v1'))
# Load v2 explicitly: this script has the same basename.
import importlib.util
spec = importlib.util.spec_from_file_location('road_compose', HERE.parent / 'v2/compose.py')
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
from common import *
from finish_donors import insert
from scipy.ndimage import distance_transform_edt
import json
import shutil


def main():
    previous = HERE.parent / 'v3'
    dirt = read(M / 'materials/dirt.png'); grey = read(M / 'materials/grey_dirt.png')
    original = read(HERE.parent / 'v1/donors/authoring/drsrns.png')
    painted = read(HERE / 'raw/drsrns.png', 512)
    old_mask, new_mask = c.coverage(original), c.coverage(painted)
    # Preserve the central stones; only repaint the two side contours and their shade.
    distance = np.minimum(distance_transform_edt(old_mask), distance_transform_edt(new_mask))
    outside = distance_transform_edt(~(old_mask | new_mask))
    domain = (distance < 32) & (outside < 20)
    pixels = insert(original, painted, domain)
    mask = old_mask.copy(); mask[domain] = new_mask[domain]
    donors = {'drsrns': c.layer_from_rgb(pixels, mask, dirt)}
    ew = read(HERE.parent / 'v1/donors/authoring/drsrew.png')
    donors['drsrew'] = c.layer_from_rgb(ew, c.coverage(ew), dirt)
    save(HERE / 'donor.png', c.compose_layer(donors['drsrns'], dirt))
    build = json.loads((previous / 'build.json').read_text())
    changed = set()
    for record in build['tiles']:
        name = record['name']
        for folder in ('authoring', 'runtime', 'masks', 'fields'):
            (HERE / folder).mkdir(exist_ok=True)
            suffix = '.npz' if folder == 'fields' else '.png'
            shutil.copy2(previous / folder / (name + suffix), HERE / folder / (name + suffix))
        if record['family'] != 'roads_dirt' or not (record['topology']['N'] or record['topology']['S']):
            continue
        if name == 'drsrns':
            layer = donors[name]
        else:
            rgb = read(previous / 'authoring' / (name + '.png'))
            alpha = np.load(previous / 'fields' / (name + '.npz'))['alpha']
            # Existing rendered art already contains the contact shading. Preserve
            # it exactly outside the opening grafts instead of recompositing it.
            layer = dict(rgb=rgb, alpha=alpha, shade=np.ones_like(rgb))
        # Quilt rendered art and coverage together; never clip new masks through old stones.
        rendered_donors = {k: dict(rgb=c.compose_layer(v, dirt), alpha=v['alpha'], shade=np.ones_like(pixels)) for k, v in donors.items()}
        if name == 'drsrns':
            layer = rendered_donors[name]
        final = c.graft(layer, rendered_donors, record['topology'])
        save(HERE / 'authoring' / (name + '.png'), final['rgb'])
        save(HERE / 'masks' / (name + '.png'), final['alpha'] * 255)
        np.savez_compressed(HERE / 'fields' / (name + '.npz'), **final)
        changed.add(name)
    for record in build['tiles']:
        name = record['name']; source = 'drsr' + name[4:]
        if record['family'] != 'roads_grey' or source not in changed:
            continue
        brown = read(HERE / 'authoring' / (source + '.png'))
        alpha = np.load(HERE / 'fields' / (source + '.npz'))['alpha']
        contact = np.clip((20 - distance_transform_edt(alpha <= .5)) / 14, 0, 1)
        shade = 1 + (np.clip(brown.mean(2) / np.maximum(dirt.mean(2), 1), .4, 1.05) - 1) * contact
        chroma = (brown[:, :, 0] - brown[:, :, 2]) / np.maximum(brown.mean(2), 1)
        fringe = np.clip((20 - distance_transform_edt(alpha > .5)) / 8, 0, 1)
        earth = np.clip((chroma - .5) / .3, 0, 1) * fringe
        foreground = brown * (1 - earth[:, :, None]) + grey * shade[:, :, None] * earth[:, :, None]
        a = alpha[:, :, None]
        rgb = foreground * a + grey * shade[:, :, None] * (1 - a)
        save(HERE / 'authoring' / (name + '.png'), rgb)
        save(HERE / 'masks' / (name + '.png'), alpha * 255)
        np.savez_compressed(HERE / 'fields' / (name + '.npz'), rgb=foreground, alpha=alpha, shade=shade)
        changed.add(name)
    for record in build['tiles']:
        name = record['name']
        if name in changed:
            rgb = read(HERE / 'authoring' / (name + '.png'))
            alpha = np.load(HERE / 'fields' / (name + '.npz'))['alpha']
            substrate = grey if record['family'] == 'roads_grey' else dirt
            padded = seams.pad(rgb, 'edge')
            padded += (seams.pad(substrate, 'wrap') - seams.pad(substrate, 'edge')) * (1 - seams.pad(alpha, 'edge')[:, :, None])
            save(HERE / 'runtime' / (name + '.png'), seams.reduce(padded))
        record['runtime_sha256'] = sha(HERE / 'runtime' / (name + '.png'))
        record['field_sha256'] = sha(HERE / 'fields' / (name + '.npz'))
    build.update(status='NS_edge_candidate_not_accepted', changed=sorted(changed), raw_sha256=sha(HERE / 'raw/drsrns.png'), source_build_sha256=sha(previous / 'build.json'))
    (HERE / 'build.json').write_text(json.dumps(build, indent=2) + '\n')
    print('Changed', len(changed), 'of 36 road candidates; installation unchanged')


if __name__ == '__main__': main()
