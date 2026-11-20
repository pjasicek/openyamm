"""Check the combined pack across all native water frames and inspect local join windows."""
import collections
import json

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

from build import P, TERRAIN, TRANSITIONS, WATER, ROOT, read, byte, sha


def ratios(joined, columns):
    energy = np.mean(np.diff(joined, axis=1) ** 2, axis=2)
    edge = energy[:, np.asarray(columns) - 1]
    nearby = np.stack([np.mean(np.concatenate([energy[:, c - 5:c - 1], energy[:, c:c + 4]], axis=1), axis=1)
                       for c in columns], axis=1)
    def windows(a):
        integral = np.concatenate([np.zeros((1, a.shape[1])), np.cumsum(a, axis=0)], axis=0)
        starts = np.arange(0, 241, 4)
        return (integral[starts + 16] - integral[starts]) / 16
    return np.sqrt(windows(edge)) / np.maximum(1, np.sqrt(windows(nearby)))


def main():
    out = P / 'runtime_x2/worlds/mm6/terrain_x2'
    tiles = {p.stem: read(p) for p in out.glob('*.png')}
    report = json.loads((P / 'report.json').read_text())
    assert len(tiles) == 63
    assert all(sha(out / n) == h for n, h in report['files'].items())
    handoff = json.loads((TRANSITIONS / 'HANDOFF_ASSETS.json').read_text())
    assert all(report['files'][n] == r['sha256'] for n, r in handoff['accepted_files'].items())
    for n in handoff['remaining_shoreline_tiles']:
        assert tiles[n[:-4]].shape == (256, 256, 4)
        assert np.array_equal(read(P / 'authoring' / n)[:, :, 3], read(WATER / 'restoration_v3/authoring' / n)[:, :, 3])
    grid = json.loads((WATER / 'corrected_map_cells.json').read_text())
    pairs = collections.Counter()
    for y, row in enumerate(grid):
        for x, name in enumerate(row):
            if x + 1 < len(row): pairs[name, 'E', row[x + 1]] += 1
            if y + 1 < len(grid): pairs[name, 'S', grid[y + 1][x]] += 1
    def composite(name, f):
        frame = tiles[f'6hdwtr{f:03}']
        a = tiles[name]
        if name == '6wtrtyl': return frame
        if a.shape[2] == 4:
            alpha = a[:, :, 3:] / 255
            return a[:, :, :3] * alpha + frame * (1 - alpha)
        return a
    checks, worst = [], []
    for (a, side, b), count in sorted(pairs.items()):
        frame_checks = []
        boundary_samples, interior_samples = [], []
        dynamic = any(n.startswith('6wtr') for n in (a, b))
        for f in range(14 if dynamic else 1):
            first, second = composite(a, f), composite(b, f)
            if side == 'S': first, second = first.transpose(1, 0, 2), second.transpose(1, 0, 2)
            joined = np.concatenate([first, second], axis=1)
            boundary = ratios(joined, [256]).ravel()
            interior = ratios(joined, [c for c in range(16, 497, 16) if c != 256]).ravel()
            boundary_samples.extend(boundary)
            interior_samples.extend(interior)
            record = {'frame': f, 'boundary_p95': float(np.percentile(boundary, 95)), 'boundary_max': float(boundary.max()),
                      'interior_p95': float(np.percentile(interior, 95)), 'interior_p999': float(np.percentile(interior, 99.9))}
            record['pass'] = record['boundary_p95'] < 1.25 * record['interior_p95'] and record['boundary_max'] < 1.25 * record['interior_p999']
            frame_checks.append(record)
            if f == 0:
                start = int(boundary.argmax()) * 4
                worst.append((record['boundary_max'], f'{a} {side} {b}', start, joined))
        # Animated material is characterized over its complete cycle, as in the accepted
        # water-v3 check. Retain each phase's measurements rather than hiding outlier phases.
        aggregate = {'boundary_p95': float(np.percentile(boundary_samples, 95)), 'boundary_max': float(max(boundary_samples)),
                     'interior_p95': float(np.percentile(interior_samples, 95)),
                     'interior_p999': float(np.percentile(interior_samples, 99.9))}
        passed = (aggregate['boundary_p95'] < 1.25 * aggregate['interior_p95']
                  and aggregate['boundary_max'] < 1.25 * aggregate['interior_p999'])
        checks.append({'a': a, 'side': side, 'b': b, 'placements': count, 'frames': frame_checks, 'full_cycle': aggregate,
                       'static_across_all_14_frames': not dynamic, 'pass': passed})
    detail = {}
    for n in ('6dirttyl', '6grastyl', '6voltyl'):
        a = tiles[n]
        high = a - gaussian_filter(a, (1, 1, 0), mode='wrap')
        mask = np.zeros((256, 256), bool); mask[:4] = mask[-4:] = True; mask[:, :4] = mask[:, -4:] = True
        detail[n] = float(np.sqrt((high[mask] ** 2).mean()) / np.sqrt((high[16:-16, 16:-16] ** 2).mean()))
    catalogue = json.loads((TERRAIN / 'mm6_new_sorpigal/catalogue.json').read_text())
    shores = [t for t in catalogue['tiles'] if t['family'] == 'shoreline']
    contexts = []
    for f in range(14):
        sheet = Image.new('RGB', (4 * 384, 3 * 408), '#202933'); draw = ImageDraw.Draw(sheet)
        for i, tile in enumerate(shores):
            x, y = i % 4 * 384, i // 4 * 408
            draw.text((x + 6, y + 5), tile['name'], fill='white')
            for cy, row in enumerate(tile['context_tiles']):
                for cx, name in enumerate(row):
                    sheet.paste(Image.fromarray(byte(composite(name, f))).resize((128, 128)), (x + cx * 128, y + 24 + cy * 128))
        contexts.append(sheet)
    contexts[0].save(P / 'shore_contexts.png')
    contexts[0].save(P / 'shore_contexts.webp', save_all=True, append_images=contexts[1:], duration=117, loop=0, lossless=True)
    sheet = Image.new('RGB', (1024, 8 * 160), '#202933'); draw = ImageDraw.Draw(sheet)
    for i, (ratio, label, start, joined) in enumerate(sorted(worst, key=lambda a: -a[0])[:32]):
        x, y = i % 4 * 256, i // 4 * 160
        draw.text((x + 3, y + 3), label, fill='white'); draw.text((x + 3, y + 17), f'window {start}, ratio {ratio:.2f}', fill='white')
        start = max(0, min(start - 8, 224))
        sheet.paste(Image.fromarray(byte(joined[start:start + 32, 224:288])).resize((256, 128)), (x, y + 32))
    sheet.save(P / 'worst_join_windows.png')
    failures = [c for c in checks if not c['pass']]
    result = {'files': report['files'], 'unique_joins': len(checks), 'water_frames': 14, 'checks': checks,
              'failures': failures, 'border_detail': detail, 'accepted_files_preserved': 51, 'shore_alpha_unchanged': True}
    (P / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    (P / 'local_seams.json').write_text(json.dumps({'pass': not failures and all(0.8 <= r <= 1.25 for r in detail.values()),
        'files': report['files'], 'method': 'Local 16px windows versus interior p95/p99.9; strict accepted-land criteria applied to combined joins'}, indent=2) + '\n')
    print(json.dumps({'joins': len(checks), 'failures': [(c['a'], c['side'], c['b']) for c in failures], 'detail': detail}, indent=2))
    assert not failures
    assert all(0.8 <= r <= 1.25 for r in detail.values())


if __name__ == '__main__': main()
