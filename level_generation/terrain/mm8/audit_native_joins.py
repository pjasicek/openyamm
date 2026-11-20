"""Measure every actual MM8 terrain adjacency in the staged union, retaining native comparisons.

This phase-zero placement screen complements, rather than replaces, all-phase compatible-family checks.
Failed joins are review candidates; native placement contradictions must be inspected, not silently exempted.
"""
import json
from collections import Counter

from common import P, STAGE, Image, np, read, sha
from check_land import checks


def load_inputs():
    stage = json.loads((P / 'reports/candidate_stage.json').read_text())
    folder = STAGE / 'enhanced/assets_dev/worlds/mm8/terrain_x2'
    assert {f.name: sha(f) for f in folder.glob('*.png')} == stage['files']
    grids = json.loads((P / 'effective_grids.json').read_text())
    inventory = json.loads((P / 'effective_inventory.json').read_text())
    assert set(stage['files']) == {n + '.png' for n in inventory['runtime_names']}
    transitions = json.loads((P / 'liquids/banks_v2/build.json').read_text())
    overlay = {r['name']: r['binding']['liquid'] for r in transitions['tiles']}
    bases = dict(water='wtrtyl', lava='lavtyl', tar='tartyl')
    frames = dict(water='hdwtr000', lava='hdlav000', tar='hwoil000')
    current, original = {}, {}
    for n in inventory['uses']:
        im = np.asarray(Image.open(folder / (n + '.png')).convert('RGBA'), float)
        old_path = P / 'references' / (n + '.png')
        if not old_path.exists():
            old_path = P.parents[2] / 'assets_dev/worlds/mm8/terrain' / (n + '.bmp')
        old_image = Image.open(old_path).convert('RGB')
        old = np.asarray(old_image.resize((256, 256), Image.Resampling.NEAREST), float)
        if n in overlay:
            family = overlay[n]
            alpha = im[:, :, 3:4] / 255
            current[n] = im[:, :, :3] * alpha + read(folder / (frames[family] + '.png')) * (1 - alpha)
            mask = ((old[:, :, 0] > 240) & (old[:, :, 1] < 10) & (old[:, :, 2] > 240))[:, :, None]
            original[n] = np.where(mask, read(P / 'references' / (frames[family] + '.png'), 256), old)
        else:
            current[n], original[n] = im[:, :, :3], old
    for family, base in bases.items():
        current[base] = read(folder / (frames[family] + '.png'))
        original[base] = read(P / 'references' / (frames[family] + '.png'), 256)
    return current, original, grids


def main():
    current, original, grids = load_inputs()
    pairs, examples = Counter(), {}
    for map_name, grid in grids.items():
        for y, row in enumerate(grid):
            for x, a in enumerate(row):
                for dx, dy, side in ((1, 0, 'E'), (0, 1, 'S')):
                    if y + dy >= len(grid) or x + dx >= len(grid[y + dy]):
                        continue
                    key = a, side, grid[y + dy][x + dx]
                    pairs[key] += 1
                    examples.setdefault(key, dict(map=map_name, row=y, col=x))
    results = []
    for (a, side, b), count in sorted(pairs.items()):
        new, _, _ = checks.metrics(current[a], current[b], side)
        old, _, _ = checks.metrics(original[a], original[b], side)
        results.append(dict(a=a, side=side, b=b, placements=count, example=examples[(a, side, b)],
                            enhanced=new, original=old))
    failures = [r for r in results if not r['enhanced']['passed']]
    report = dict(scope='Every actual adjacency in all14 effective MM8 outdoor grids; liquid phase0 only',
                  unique_pairs=len(results), placements=sum(pairs.values()), checks=results,
                  failures=failures, newly_failing=[r for r in failures if r['original']['passed']],
                  stage_sha256=sha(P / 'reports/candidate_stage.json'),
                  grids_sha256=sha(P / 'effective_grids.json'), script_sha256=sha(P / 'audit_native_joins.py'))
    (P / 'reports/native_join_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Native placement screen:', len(results), 'pairs;', sum(pairs.values()), 'placements;',
          len(failures), 'review candidates;', len(report['newly_failing']), 'newly failing')


if __name__ == '__main__':
    main()
