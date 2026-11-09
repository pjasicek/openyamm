"""Restore voltylx as a patched volcano material with pure volcanic outer borders."""
import json
from scipy.ndimage import distance_transform_edt, gaussian_filter
from PIL import ImageDraw
from common import *
from build_transitions import recovery
from check_land import checks


def main():
    folder = P / 'variants/volcano_v2'
    (folder / 'runtime').mkdir(parents=True, exist_ok=True)
    original = read(P / 'references/voltylx.png')
    dirt = read(P / 'references/dirttyl.png')
    volcano = read(P / 'references/voltyl.png')
    alpha, shade, error = recovery.recover(original, dirt, volcano)
    bulk = gaussian_filter(alpha, 8) > .5
    inside, outside = distance_transform_edt(bulk), distance_transform_edt(~bulk)
    fi, fo = np.clip((48 - inside) / 24, 0, 1), np.clip((48 - outside) / 24, 0, 1)
    alpha = np.where(bulk, 1 - (1 - alpha) * fi, alpha * fo)
    shade = 1 + (shade - 1) * fi * fo
    # This is an interior patch variant, not a directional dirt/volcano transition.
    # The native placement joins it to volcanic ground on every side.
    targets = {s: np.ones(512) for s in 'NSEW'}
    alpha, shade = recovery.connect(alpha, targets), recovery.connect(shade, targets)
    a = seams.pad(alpha, 'edge')[:, :, None]
    rgb = seams.srgb(seams.linear(seams.pad(read(M / 'materials/dirt.png'), 'wrap')) * (1 - a)
                    + seams.linear(seams.pad(read(M / 'materials/volcano.png'), 'wrap')) * a)
    result = seams.reduce(rgb * seams.pad(shade, 'edge')[:, :, None])
    output = folder / 'runtime/voltylx.png'
    save(output, result)
    save(folder / 'mask.png', alpha * 255)
    np.savez_compressed(folder / 'fields.npz', coverage=alpha.astype('float32'), shade=shade.astype('float32'))
    audit = json.loads((P / 'reports/native_join_audit.json').read_text())
    current = STAGE / 'enhanced/assets_dev/worlds/mm8/terrain_x2'
    transition_build = json.loads((P / 'transitions/build.json').read_text())
    contracts = {r['name']: r['topology'] for r in transition_build['tiles'] if r['family'] == 'volcano'}
    contracts['voltylx'] = contracts['voltyl'] = dict.fromkeys('NSEW', '11')
    compatible = []
    for a in contracts:
        for b in contracts:
            if 'voltylx' not in (a, b):
                continue
            for side, opposite in [('E', 'W'), ('S', 'N')]:
                if contracts[a][side] != contracts[b][opposite]:
                    continue
                images = [read(output if n == 'voltylx' else current / (n + '.png')) for n in (a, b)]
                metrics, _, _ = checks.metrics(*images, side)
                compatible.append(dict(a=a, b=b, side=side, **metrics))
    assert all(r['passed'] for r in compatible)
    results = []
    for record in audit['checks']:
        if 'voltylx' not in (record['a'], record['b']):
            continue
        images = [read(output if n == 'voltylx' else current / (n + '.png'))
                  for n in (record['a'], record['b'])]
        metrics, _, _ = checks.metrics(*images, record['side'])
        results.append(dict(a=record['a'], b=record['b'], side=record['side'],
                            original=record['original'], previous=record['enhanced'], enhanced=metrics,
                            placements=record['placements'], example=record['example']))
    sheet = Image.new('RGB', (1024, 540), '#202933')
    draw = ImageDraw.Draw(sheet)
    for i, (label, path) in enumerate([('native', P / 'references/voltylx.png'),
                                      ('previous', current / 'voltylx.png'), ('corrected', output),
                                      ('volcano master', current / 'voltyl.png')]):
        draw.text((i * 256 + 4, 4), label, fill='white')
        sheet.paste(Image.open(path).convert('RGB').resize((256, 256)), (i * 256, 24))
        sheet.paste(Image.open(path).convert('RGB').resize((256, 256)), (i * 256, 280))
    sheet.save(folder / 'comparison.png')
    report = dict(status='candidate_not_staged', name='voltylx', topology=dict.fromkeys('NSEW', '11'),
                  runtime_sha256=sha(output), source_sha256=sha(P / 'references/voltylx.png'),
                  script_sha256=sha(P / 'repair_volcano_variant.py'), reconstruction_mae=error,
                  compatible_checks=compatible,
                  checks=results, failures=[r for r in results if not r['enhanced']['passed']])
    (folder / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(len(results), 'native pairs;', len(report['failures']), 'remaining metric failures')


if __name__ == '__main__':
    main()
