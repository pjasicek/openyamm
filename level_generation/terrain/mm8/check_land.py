"""Screen every compatible opaque MM8 candidate join, including dependency masters.

This is deliberately a land-only report. It does not certify roads, alpha overlays,
liquid animation, native placement, or final inventory coverage.
"""
import importlib.util
import json
from PIL import ImageDraw
from common import *
from inventory import GROUPS

spec = importlib.util.spec_from_file_location('terrain_join_metrics', T / 'mm7/check.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def main():
    build = json.loads((P / 'transitions/build.json').read_text())
    tiles, labels, paths = {}, {}, {}
    for family in sorted({p.stem for p in (M / 'runtime').glob('*.png')}):
        name = GROUPS[family][0]
        path = M / 'runtime' / (family + '.png')
        tiles[name], labels[name], paths[name] = read(path), dict.fromkeys('NSEW', family), path
    for name in ('dirt1', 'dirt2'):
        path = OUT / (name + '.png')
        tiles[name], labels[name], paths[name] = read(path), dict.fromkeys('NSEW', 'dirt'), path
    for record in build['tiles']:
        if record['overlay']:
            continue
        name, binding = record['name'], record['binding']
        path = OUT / (name + '.png')
        assert sha(path) == record['runtime_sha256'], name
        tiles[name], paths[name] = read(path), path
        labels[name] = {side: binding['background'] if kind == '00' else
                        binding['foreground'] if kind == '11' else record['family'] + ':' + kind
                        for side, kind in record['topology'].items()}
    results, worst = [], []
    for a in sorted(tiles):
        for b in sorted(tiles):
            for side, opposite in (('E', 'W'), ('S', 'N')):
                if labels[a][side] != labels[b][opposite]:
                    continue
                metrics, joined, start = checks.metrics(tiles[a], tiles[b], side)
                score = max(metrics['boundary_p95'] / max(metrics['interior_p95'], 1e-6),
                            metrics['boundary_max'] / max(metrics['interior_p999'], 1e-6))
                results.append(dict(a=a, side=side, b=b, contract=labels[a][side], score=score, **metrics))
                worst.append((score, a + ' ' + side + ' ' + b, start, joined))
                worst = sorted(worst, key=lambda row: -row[0])[:24]
    sheet = Image.new('RGB', (1024, 6 * 160), '#202933')
    draw = ImageDraw.Draw(sheet)
    for i, (score, label, start, joined) in enumerate(worst):
        x, y = i % 4 * 256, i // 4 * 160
        draw.text((x + 2, y + 2), label, fill='white')
        draw.text((x + 2, y + 16), 'relative %.2f' % score, fill='white')
        start = max(0, min(start - 8, 224))
        crop = Image.fromarray(seams.byte(joined[start:start + 32, 224:288]))
        sheet.paste(crop.resize((256, 128)), (x, y + 32))
    sheet.save(P / 'reports/land_worst_joins.png')
    report = dict(scope='opaque candidate materials and transitions; includes two dependency masters',
                  checked_tiles=len(tiles), compatible_checks=len(results),
                  failures=[r for r in results if not r['passed']], checks=results,
                  contracts=labels, files={str(paths[n].relative_to(P)): sha(paths[n]) for n in paths},
                  build_sha256=sha(P / 'transitions/build.json'),
                  metric_source_sha256=sha(T / 'mm7/check.py'))
    (P / 'reports/land_validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Land:', len(tiles), 'tiles;', len(results), 'joins;', len(report['failures']), 'failures')
    print([(r['a'], r['side'], r['b'], round(r['score'], 2))
           for r in sorted(report['failures'], key=lambda r: -r['score'])[:12]])


if __name__ == '__main__':
    main()
