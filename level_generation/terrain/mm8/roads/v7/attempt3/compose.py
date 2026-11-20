"""Reconstruct connected join neighborhoods from aligned imagegen repairs."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / 'v1'))
import importlib.util
spec = importlib.util.spec_from_file_location('road_fields', HERE.parent / 'v2/compose.py')
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
from common import *
from finish_donors import insert
from scipy.ndimage import distance_transform_edt, gaussian_filter, binary_fill_holes, gaussian_filter1d, map_coordinates
import json
import shutil
import cv2
from scipy.ndimage import label


def main():
    old = HERE.parent / 'v6'
    build = json.loads((old / 'build.json').read_text())
    dirt = read(M / 'materials/dirt.png'); grey = read(M / 'materials/grey_dirt.png')
    yy, xx = np.mgrid[:512, :512]
    border = np.minimum.reduce([xx, yy, 511 - xx, 511 - yy])
    for record in build['tiles']:
        for folder, suffix in [('runtime', '.png'), ('authoring', '.png'), ('masks', '.png'), ('fields', '.npz')]:
            (HERE / folder).mkdir(exist_ok=True)
            shutil.copy2(old / folder / (record['name'] + suffix), HERE / folder / (record['name'] + suffix))
    joined_repairs = {}
    for side in ('east', 'south'):
        target = read(HERE / 'inputs' / (side + '.png'))
        generated = read(HERE / 'raw' / (side + '.png'), 512)
        # Register the generated image to its input so the untouched neighboring
        # stones, not a hard rectangular crop, anchor the repair.
        def luminance(im):
            return cv2.cvtColor(seams.byte(im), cv2.COLOR_RGB2GRAY)
        flow = cv2.calcOpticalFlowFarneback(luminance(target), luminance(generated), None,
                                           .5, 5, 41, 8, 7, 1.5, 0)
        aligned = cv2.remap(generated.astype(np.float32),
                            (xx + flow[:, :, 0]).astype(np.float32),
                            (yy + flow[:, :, 1]).astype(np.float32), cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_REFLECT)
        coordinate = xx if side == 'east' else yy
        distance = abs(coordinate - 255.5)
        road = c.coverage(target) | c.coverage(aligned)
        domain = (distance >= 4) & (distance < 104) & (distance_transform_edt(~road) < 18)
        result = insert(target, aligned, domain)
        save(HERE / 'joined' / (side + '.png'), result)
        joined_repairs[side] = result
    changed, repairs = [], []
    for name in ('drsrne1', 'drsrne2'):
        original = read(old / 'authoring' / (name + '.png'))
        pixels = original.copy()
        def apply(region, patch):
            before = original[region]
            changed = np.any(abs(patch - before) > .01, axis=2)
            pixels[region][changed] = patch[changed]
        if name.endswith('1'):
            apply(np.s_[:, :256], joined_repairs['east'][:, 256:])
            apply(np.s_[256:, :], joined_repairs['south'][:256, :])
        else:
            apply(np.s_[:, 256:], joined_repairs['east'][:, :256])
            apply(np.s_[:256, :], joined_repairs['south'][256:, :])
        # The two repaired neighborhoods meet only on substrate, outside the road.
        alpha = np.load(old / 'fields' / (name + '.npz'))['alpha'].copy()
        new_mask = c.coverage(pixels)
        domain = np.any(pixels != original, axis=2)
        new_alpha = gaussian_filter(new_mask.astype(float), .65)
        alpha[domain] = new_alpha[domain]
        # A one-pixel threshold hole can appear where old/new soft masks meet.
        # Continuous cobbles own a solid footprint, including dark mortar.
        holes = binary_fill_holes(alpha > .5) & (alpha <= .5)
        alpha[holes] = 1
        components, count = label(alpha > .5)
        sizes = np.bincount(components.ravel()); sizes[0] = 0
        alpha[(components != 0) & (components != sizes.argmax())] = 0
        # Both substrates own the same stone shapes. Grey uses scalar contact
        # shading; preserve all old artwork outside the local repair domain.
        contact = np.clip((20 - distance_transform_edt(alpha <= .5)) / 14, 0, 1)
        shade = 1 + (np.clip(pixels.mean(2) / np.maximum(dirt.mean(2), 1), .4, 1.05) - 1) * contact
        chroma = (pixels[:, :, 0] - pixels[:, :, 2]) / np.maximum(pixels.mean(2), 1)
        fringe = np.clip((20 - distance_transform_edt(alpha > .5)) / 8, 0, 1)
        earth = np.clip((chroma - .5) / .3, 0, 1) * fringe
        foreground = pixels * (1 - earth[:, :, None]) + grey * shade[:, :, None] * earth[:, :, None]
        a = alpha[:, :, None]
        grey_pixels = foreground * a + grey * shade[:, :, None] * (1 - a)
        for prefix, substrate, repaired in [('drsr', dirt, pixels), ('gdrd', grey, grey_pixels)]:
            tile = prefix + name[4:]
            base = read(old / 'authoring' / (tile + '.png'))
            result = base.copy(); result[domain] = repaired[domain]
            assert np.array_equal(result[~domain], base[~domain])
            save(HERE / 'authoring' / (tile + '.png'), result)
            save(HERE / 'masks' / (tile + '.png'), alpha * 255)
            np.savez_compressed(HERE / 'fields' / (tile + '.npz'), rgb=result, alpha=alpha)
            # Existing directional filter gutters are retained exactly.
            padded = seams.pad(result, 'edge')
            padded += (seams.pad(substrate, 'wrap') - seams.pad(substrate, 'edge')) * (1 - seams.pad(alpha, 'edge')[:, :, None])
            save(HERE / 'runtime' / (tile + '.png'), seams.reduce(padded))
            changed.append(tile)
        repairs.append(dict(name=name, source_authoring_sha256=sha(old / 'authoring' / (name + '.png')),
                            protected_fraction=float(np.mean(~domain))))
    for record in build['tiles']:
        name = record['name']
        record['runtime_sha256'] = sha(HERE / 'runtime' / (name + '.png'))
        record['field_sha256'] = sha(HERE / 'fields' / (name + '.npz'))
    build.update(status='diagonal_candidate_pending_exact_pose_review', changed=changed,
                 repairs=repairs, source_build_sha256=sha(old / 'build.json'), imagegen_calls=2)
    (HERE / 'build.json').write_text(json.dumps(build, indent=2) + '\n')
    print('Built four joined diagonal repairs;32 road textures and both joined borders reconstructed')


if __name__ == '__main__': main()
