"""Recover native MM8 land/contact fields and keyed liquid banks over consistent restored materials."""
import collections
import importlib.util
import json

from PIL import ImageDraw
from scipy.ndimage import distance_transform_edt, gaussian_filter
from common import *
from inventory import GROUPS

spec = importlib.util.spec_from_file_location('native_terrain_recovery', T / 'mm6_remaining/transitions/build.py')
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


def topology(alpha, side):
    values = recovery.edge(alpha, side)
    return ''.join(str(int(values[start:stop].mean() > .5)) for start, stop in ((8, 40), (472, 504)))


def reduce_float(array):
    if array.ndim == 3:
        return np.stack([reduce_float(array[:, :, c]) for c in range(array.shape[2])], axis=2)
    return np.asarray(Image.fromarray(array.astype('float32')).resize((264, 264),
                      Image.Resampling.LANCZOS), float)[4:-4, 4:-4]


def recover_grey_stone(original, background, foreground):
    # These two grey sources have almost collinear RGB, so unconstrained colour
    # decomposition trades coverage against shade and produces salt-and-pepper holes.
    # Their native luminance contrast is strong; exact source samples anchor interiors.
    b, f, o = [gaussian_filter(a.mean(axis=2), .7) for a in (background, foreground, original)]
    alpha = np.clip((b - o) / np.maximum(b - f, 8), 0, 1)
    same_b = np.max(abs(original - background), axis=2) <= 3
    same_f = np.max(abs(original - foreground), axis=2) <= 3
    alpha[same_b], alpha[same_f] = 0, 1
    blend = background * (1 - alpha[:, :, None]) + foreground * alpha[:, :, None]
    shade = np.sum(original * blend, axis=2) / np.maximum(np.sum(blend * blend, axis=2), 1)
    shade[same_b | same_f] = 1
    shade = gaussian_filter(np.clip(shade, .45, 1.15), .55)
    error = float(np.mean(abs(original - blend * shade[:, :, None])))
    return np.clip(recovery.up(alpha), 0, 1), np.clip(recovery.up(shade), .45, 1.15), error


def main():
    inventory = json.loads((P / 'inventory.json').read_text())
    bindings = json.loads((P / 'materials.json').read_text())
    native = {g: read(P / 'references' / (base + '.png')) for g, (base, _) in GROUPS.items() if base}
    masters = {p.stem: read(p) for p in (M / 'materials').glob('*.png')}
    fields = {}
    measurements = collections.defaultdict(list)
    records = [r for r in inventory['tiles'] if r['kind'] in ('transition', 'variant')
               and r['family'] in set(bindings['land']) | set(bindings['liquid_overlays'])]
    for record in records:
        name, group = record['name'], record['family']
        assert sha(ROOT / record['source']) == record['sha256']
        original = read(P / 'references' / (name + '.png'))
        overlay = group in bindings['liquid_overlays']
        binding = bindings['liquid_overlays' if overlay else 'land'][group]
        background = binding['land'] if overlay else binding['background']
        base = native[background]
        if overlay:
            solid = ~((original[:, :, 0] > 240) & (original[:, :, 1] < 10) & (original[:, :, 2] > 240))
            assert .001 < solid.mean() < .999, (name, 'missing keyed liquid coverage')
            alpha = np.clip(recovery.up(solid.astype(float)), 0, 1)
            ratio = original / np.maximum(base, 1)
            bank = solid & (np.max(abs(original - base), axis=2) > 4)
            ratio[~bank] = 1
            ratio = np.clip(ratio, .45, 1.35)
            shade = np.stack([recovery.up(gaussian_filter(ratio[:, :, c], .6)) for c in range(3)], axis=2)
            error = float(np.mean(abs(original[solid] - (base * ratio)[solid])))
        else:
            foreground = native[binding['foreground']]
            fit = recover_grey_stone if group == 'grey_stone' else recovery.recover
            alpha, shade, error = fit(original, base, foreground)
            bulk = gaussian_filter(alpha, 8) > .5
            inside, outside = distance_transform_edt(bulk), distance_transform_edt(~bulk)
            fi, fo = np.clip((48 - inside) / 24, 0, 1), np.clip((48 - outside) / 24, 0, 1)
            alpha = np.where(bulk, 1 - (1 - alpha) * fi, alpha * fo)
            shade = 1 + (shade - 1) * fi * fo
        sides = {s: topology(alpha, s) for s in 'NSEW'}
        fields[name] = dict(alpha=alpha, shade=shade, topology=sides, error=error,
                            group=group, binding=binding, overlay=overlay,
                            exact_background_fraction=float(np.mean(np.max(abs(original - base), 2) <= 3)))
        for side, contract in sides.items():
            measurements[(group, 'h' if side in 'NS' else 'v', contract)].append(
                (recovery.edge(alpha, side), recovery.edge(shade, side)))
    profiles = {}
    for key, values in measurements.items():
        group, axis, contract = key
        channels = 3 if group in bindings['liquid_overlays'] else None
        if contract in ('00', '11'):
            alpha = np.full(512, int(contract[0]), float)
            shade = np.ones((512, 3) if channels else 512)
        else:
            alpha = gaussian_filter(np.median(np.stack([v[0] for v in values]), 0), 1)
            shade = np.median(np.stack([v[1] for v in values]), 0)
            alpha[:32], alpha[-32:] = int(contract[0]), int(contract[-1])
            shade[:32] = shade[-32:] = 1
        profiles[key] = (alpha, shade)
    reports = []
    for name, field in fields.items():
        group, binding = field['group'], field['binding']
        targets = {s: profiles[(group, 'h' if s in 'NS' else 'v', kind)]
                   for s, kind in field['topology'].items()}
        alpha = recovery.connect(field['alpha'].copy(), {s: v[0] for s, v in targets.items()})
        shade = recovery.connect(field['shade'].copy(), {s: v[1] for s, v in targets.items()})
        folder = P / 'transitions'
        save(folder / 'masks' / (name + '.png'), alpha * 255)
        save(folder / 'shading' / (name + '.png'), shade * 200)
        (folder / 'fields').mkdir(exist_ok=True)
        np.savez_compressed(folder / 'fields' / (name + '.npz'),
                            coverage=alpha.astype('float32'), shade=shade.astype('float32'))
        coverage = seams.pad(alpha, 'edge')
        if field['overlay']:
            rgb = seams.pad(masters[binding['land']], 'wrap') * seams.pad(shade, 'edge')
            premul = reduce_float(rgb * coverage[:, :, None])
            reduced_alpha = np.clip(reduce_float(coverage), 0, 1)
            hidden = reduce_float(rgb)
            visible = reduced_alpha > 1e-6
            hidden[visible] = premul[visible] / reduced_alpha[visible, None]
            result = np.dstack([hidden, reduced_alpha * 255])
        else:
            a = coverage[:, :, None]
            rgb = seams.srgb(seams.linear(seams.pad(masters[binding['background']], 'wrap')) * (1 - a)
                              + seams.linear(seams.pad(masters[binding['foreground']], 'wrap')) * a)
            rgb = rgb * seams.pad(shade, 'edge')[:, :, None]
            result = seams.reduce(rgb)
        save(OUT / (name + '.png'), result)
        reports.append(dict(name=name, family=group, binding=binding, overlay=field['overlay'],
                            topology=field['topology'], reconstruction_mae=field['error'],
                            exact_background_fraction=field['exact_background_fraction'],
                            shade_min=float(shade.min()), shade_max=float(shade.max()),
                            runtime_sha256=sha(OUT / (name + '.png')),
                            field_sha256=sha(folder / 'fields' / (name + '.npz'))))
    for group in sorted({r['family'] for r in reports}):
        members = [r for r in reports if r['family'] == group]
        sheet = Image.new('RGB', (1024, 280 * len(members)), '#202933')
        draw = ImageDraw.Draw(sheet)
        for row, record in enumerate(members):
            name = record['name']
            paths = [P / 'references' / (name + '.png'), OUT / (name + '.png'),
                     P / 'transitions/masks' / (name + '.png'), P / 'transitions/shading' / (name + '.png')]
            for column, path in enumerate(paths):
                image = Image.open(path).convert('RGBA').resize((256, 256))
                canvas = Image.new('RGBA', image.size, '#202933')
                canvas.alpha_composite(image)
                sheet.paste(canvas.convert('RGB'), (column * 256, row * 280 + 24))
                draw.text((column * 256 + 4, row * 280 + 5), name + ' ' +
                          ['original', 'candidate x2', 'coverage', 'shade neutral200'][column], fill='white')
        (P / 'transitions/sheets').mkdir(exist_ok=True)
        sheet.save(P / 'transitions/sheets' / (group + '.png'))
    report = dict(status='candidate_fields_require_visual_and_join_review', tiles=reports,
                  land_count=sum(not r['overlay'] for r in reports),
                  overlay_count=sum(r['overlay'] for r in reports),
                  masters={g: sha(M / 'materials' / (g + '.png')) for g in masters},
                  source_bindings_sha256=sha(P / 'materials.json'))
    (P / 'transitions/build.json').write_text(json.dumps(report, indent=2) + '\n')
    (P / 'transitions/edge_profiles.json').write_text(json.dumps({':'.join(k): dict(
        coverage=a.tolist(), shade=s.tolist()) for k, (a, s) in profiles.items()}, indent=2) + '\n')
    print('Built', report['land_count'], 'land transitions and', report['overlay_count'], 'liquid overlays')
    print('Largest reconstruction errors:', [(r['name'], round(r['reconstruction_mae'], 2))
                                              for r in sorted(reports, key=lambda r: -r['reconstruction_mae'])[:12]])


if __name__ == '__main__':
    main()
