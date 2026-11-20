"""Inspect local join gradients, border detail, worst windows and assembled layouts.

Equality of opposite pixels is deliberately not a success criterion: they represent
consecutive samples. Inspect the generated images in addition to the numeric report.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

P = Path(__file__).resolve().parent
PROJECT = P.parent


def read(path):
    return np.asarray(Image.open(path).convert('RGB'), dtype=float)


def windows(a, column):
    across = (a[:, column] - a[:, column - 1]) ** 2
    nearby = np.concatenate([np.diff(a[:, column - 5:column], axis=1),
                             np.diff(a[:, column:column + 5], axis=1)], axis=1) ** 2
    return [(start, float(np.sqrt(across[start:start + 16].mean()) /
                          max(1, np.sqrt(nearby[start:start + 16].mean()))))
            for start in range(0, len(a) - 15, 4)]


def main():
    previous = json.loads((PROJECT / 'reports/rgb_join_check_v1.json').read_text())
    all_checks = {}
    worst = []
    for version in ('v1', 'v2'):
        images = {f.stem: read(f) for f in (PROJECT / 'edge_treatment/runtime' / version).glob('*.png')}
        assert len(images) == 36 and all(a.shape == (256, 256, 3) for a in images.values())
        checks = []
        for pair in previous['checks']:
            a, b = images[pair['a']], images[pair['b']]
            if pair['direction'] == 'south':
                a, b = a.transpose(1, 0, 2), b.transpose(1, 0, 2)
            joined = np.concatenate([a, b], axis=1)
            boundary = windows(joined, 256)
            interior = [ratio for column in range(16, 497, 16) if column != 256
                        for _, ratio in windows(joined, column)]
            ratios = [ratio for _, ratio in boundary]
            check = {k: pair[k] for k in ('a', 'b', 'direction', 'count')}
            check.update(boundary_p95=float(np.percentile(ratios, 95)), boundary_max=max(ratios),
                         interior_p95=float(np.percentile(interior, 95)),
                         interior_p999=float(np.percentile(interior, 99.9)))
            check['pass'] = (check['boundary_p95'] < 1.25 * check['interior_p95'] and
                             check['boundary_max'] < 1.25 * check['interior_p999'])
            checks.append(check)
            if version == 'v2':
                start, ratio = max(boundary, key=lambda item: item[1])
                worst.append((ratio, check, start, joined))
        detail = {}
        for name in ('6dirttyl', '6grastyl', '6voltyl'):
            a = images[name]
            high = a - gaussian_filter(a, sigma=(1, 1, 0), mode='wrap')
            border = np.zeros(a.shape[:2], bool)
            border[:4] = border[-4:] = True
            border[:, :4] = border[:, -4:] = True
            detail[name] = float(np.sqrt(np.mean(high[border] ** 2)) /
                                 np.sqrt(np.mean(high[16:-16, 16:-16] ** 2)))
        all_checks[version] = {'checks': checks, 'failures': [c for c in checks if not c['pass']],
                               'border_to_interior_detail': detail,
                               'border_detail_pass': all(0.8 <= ratio <= 1.25 for ratio in detail.values())}
    sheet = Image.new('RGB', (1536, 4 * 550), '#202933')
    draw = ImageDraw.Draw(sheet)
    for y, name in enumerate(('6dirttyl', '6grastyl', '6voltyl', '6drsrew')):
        for x, version in enumerate(('v1', 'v2')):
            a = read(PROJECT / 'edge_treatment/runtime' / version / (name + '.png')).astype('uint8')
            shifted = np.roll(a, (128, 128), (0, 1))
            sheet.paste(Image.fromarray(shifted).resize((512, 512)), (x * 512, y * 550 + 26))
            draw.text((x * 512 + 8, y * 550 + 6), name + ' ' + version + ' offset', fill='white')
        sheet.paste(Image.fromarray(np.tile(a, (2, 2, 1))), (1024, y * 550 + 26))
        draw.text((1032, y * 550 + 6), name + ' v2 repeat', fill='white')
    sheet.save(P / 'offset_comparison.png')
    sheet = Image.new('RGB', (1024, 8 * 160), '#202933')
    draw = ImageDraw.Draw(sheet)
    for i, (ratio, check, start, joined) in enumerate(sorted(worst, key=lambda item: -item[0])[:32]):
        x, y = i % 4 * 256, i // 4 * 160
        draw.text((x + 4, y + 3), f'{check["a"]} {check["direction"]} {check["b"]}', fill='white')
        draw.text((x + 4, y + 17), f'window {start}:{start + 16}, ratio {ratio:.2f}', fill='white')
        crop = joined[max(0, min(start - 8, 224)):max(0, min(start - 8, 224)) + 32, 224:288]
        sheet.paste(Image.fromarray(crop.astype('uint8')).resize((256, 128)), (x, y + 32))
    sheet.save(P / 'worst_join_windows.png')
    cases = json.loads((PROJECT / 'test_cases.json').read_text())
    for case in cases:
        if case['group'] != 'Large legal layouts':
            continue
        grid = case['tiles']
        sheet = Image.new('RGB', (len(grid[0]) * 256, len(grid) * 256))
        for y, row in enumerate(grid):
            for x, tile in enumerate(row):
                sheet.paste(Image.fromarray(images[tile].astype('uint8')), (x * 256, y * 256))
        sheet.save(P / (case['id'].replace(':', '_') + '.png'))
    for offset in range(0, len(worst), 40):
        sheet = Image.new('RGB', (8 * 256, 5 * 150), '#202933')
        draw = ImageDraw.Draw(sheet)
        for i, (_, check, _, joined) in enumerate(worst[offset:offset + 40]):
            x, y = i % 8 * 256, i // 8 * 150
            draw.text((x + 3, y + 3), f'{check["a"]} {check["direction"]} {check["b"]}', fill='white')
            sheet.paste(Image.fromarray(joined.astype('uint8')).resize((256, 128)), (x, y + 22))
        sheet.save(P / f'all_joins_{offset // 40:02}.png')
    report = {'method': '16-pixel windows every 4 pixels along each compatible join; compare p95/max to 1.25x interior p95/p99.9.',
              'unique_joins': len(worst), 'placements': previous['placed_joins'], 'versions': all_checks,
              'detail_rule': 'Pure-material border high-frequency RMS must be within 0.8 to 1.25 of interior RMS.',
              'limitations': 'Local gradient ratios detect sharp breaks, not softened stripes alone. Border-detail and offset/repeat images must also be reviewed.'}
    (P / 'local_joins.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({v: {'failures': len(d['failures']), 'detail': d['border_to_interior_detail']} for v, d in all_checks.items()}, indent=2))
    assert not all_checks['v2']['failures'], all_checks['v2']['failures'][:3]
    assert all_checks['v2']['border_detail_pass'], all_checks['v2']['border_to_interior_detail']


if __name__ == '__main__':
    main()
