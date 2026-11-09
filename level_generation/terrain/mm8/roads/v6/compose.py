"""Align AI-painted continuous diagonal bands to fixed road openings."""
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


def main():
    old = HERE.parent / 'v5'
    build = json.loads((old / 'build.json').read_text())
    dirt = read(M / 'materials/dirt.png'); grey = read(M / 'materials/grey_dirt.png')
    yy, xx = np.mgrid[:512, :512]
    border = np.minimum.reduce([xx, yy, 511 - xx, 511 - yy])
    for record in build['tiles']:
        for folder, suffix in [('runtime', '.png'), ('authoring', '.png'), ('masks', '.png'), ('fields', '.npz')]:
            (HERE / folder).mkdir(exist_ok=True)
            shutil.copy2(old / folder / (record['name'] + suffix), HERE / folder / (record['name'] + suffix))
    changed, repairs = [], []
    for name in ('drsrne1', 'drsrne2'):
        original = read(old / 'authoring' / (name + '.png'))
        painted = read(HERE / 'raw' / (name + '.png'), 512)
        alpha = np.load(old / 'fields' / (name + '.npz'))['alpha'].copy()
        guide = read(HERE / 'inputs' / (name + '_coverage.png'))[:, :, 0] > 127
        # Registration in diagonal coordinates moves complete stones and their
        # shading, instead of clipping their artwork with a replacement mask.
        t, s_coord = xx + yy, yy - xx
        raw_mask = c.coverage(painted)
        def extents(mask):
            low, high = np.full(1023, np.nan), np.full(1023, np.nan)
            for k in range(1023):
                values = s_coord[(t == k) & mask]
                if len(values): low[k], high[k] = values.min(), values.max()
            good = np.isfinite(low)
            return [gaussian_filter1d(np.interp(np.arange(1023), np.where(good)[0], v[good]), 9)
                    for v in (low, high)]
        raw_low, raw_high = extents(raw_mask)
        dst_low, dst_high = extents(guide)
        # Preserve fine stone contour variation; correct only band-scale drift.
        fraction = np.clip((s_coord - dst_low[t]) / np.maximum(dst_high[t] - dst_low[t], 1), 0, 1)
        offset = (raw_low[t] - dst_low[t]) * (1 - fraction) + (raw_high[t] - dst_high[t]) * fraction
        mapped_s = s_coord + offset
        coords = [(t + mapped_s) / 2, (t - mapped_s) / 2]
        painted = np.stack([map_coordinates(painted[:, :, channel], coords, order=1, mode='nearest')
                            for channel in range(3)], 2)
        old_mask, new_mask = alpha > .5, c.coverage(painted)
        outside = distance_transform_edt(~(old_mask | new_mask))
        domain = (border >= 16) & (outside < 24)
        pixels = insert(original, painted, domain)
        new_alpha = gaussian_filter(new_mask.astype(float), .65)
        alpha[domain] = new_alpha[domain]
        # A one-pixel threshold hole can appear where old/new soft masks meet.
        # Continuous cobbles own a solid footprint, including dark mortar.
        holes = binary_fill_holes(alpha > .5) & (alpha <= .5)
        alpha[holes] = 1
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
            runtime = read(HERE / 'runtime' / (tile + '.png')); previous = read(old / 'runtime' / (tile + '.png'))
            for edge in (np.s_[:4, :], np.s_[-4:, :], np.s_[:, :4], np.s_[:, -4:]):
                assert np.array_equal(runtime[edge], previous[edge]), (tile, 'edge changed')
            changed.append(tile)
        repairs.append(dict(name=name, raw_sha256=sha(HERE / 'raw' / (name + '.png')),
                            prompt_sha256=sha(HERE / 'prompts' / (name + '.txt')),
                            protected_fraction=float(np.mean(~domain))))
    for record in build['tiles']:
        name = record['name']
        record['runtime_sha256'] = sha(HERE / 'runtime' / (name + '.png'))
        record['field_sha256'] = sha(HERE / 'fields' / (name + '.npz'))
    build.update(status='diagonal_candidate_pending_exact_pose_review', changed=changed,
                 repairs=repairs, source_build_sha256=sha(old / 'build.json'), imagegen_calls=3)
    (HERE / 'build.json').write_text(json.dumps(build, indent=2) + '\n')
    print('Built four connected diagonal bands;32 road textures and all runtime border strips unchanged')


if __name__ == '__main__': main()
