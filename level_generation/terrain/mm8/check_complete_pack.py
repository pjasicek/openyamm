"""Check compatible joins in the exact complete export, including cross-family joins."""
import json

from common import P, Image, np, read, sha
from check_land import checks
from inventory import GROUPS


def main():
    root = P / 'complete_runtime_x2'
    manifest_path = root / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    folder = root / 'worlds/mm8/terrain_x2'
    inventory = json.loads((P / 'effective_inventory.json').read_text())
    assert set(manifest['files']) == {n + '.png' for n in inventory['runtime_names']}
    assert {f.name: sha(f) for f in folder.glob('*.png')} == {
        n: r['sha256'] for n, r in manifest['files'].items()}
    labels = {base: dict.fromkeys('NSEW', family) for family, (base, _) in GROUPS.items()
              if base in inventory['uses']}
    for name in ('dirt1', 'dirt2'):
        labels[name] = dict.fromkeys('NSEW', 'dirt')
    for r in json.loads((P / 'transitions/build.json').read_text())['tiles']:
        if r['overlay']:
            continue
        binding = r['binding']
        labels[r['name']] = {s: binding['background'] if t == '00' else
                             binding['foreground'] if t == '11' else r['family'] + ':' + t
                             for s, t in r['topology'].items()}
    labels['voltylx'] = dict.fromkeys('NSEW', 'volcano')
    for r in json.loads((P / 'roads/v3/build.json').read_text())['tiles']:
        land = 'dirt' if r['family'] == 'roads_dirt' else 'grey_dirt'
        labels[r['name']] = {s: r['family'] if open_edge else land for s, open_edge in r['topology'].items()}
    for r in json.loads((P / 'roads/stepping_v1/build.json').read_text())['tiles']:
        labels[r['name']] = dict.fromkeys('NSEW', 'plains')
    banks = json.loads((P / 'liquids/banks_v2/build.json').read_text())['tiles']
    overlays = {}
    for r in banks:
        labels[r['name']] = {s: r['binding']['liquid'] if t == '00' else
                             r['binding']['land'] if t == '11' else r['family'] + ':' + t
                             for s, t in r['topology'].items()}
        overlays[r['name']] = np.asarray(Image.open(folder / (r['name'] + '.png')), float)
    assert set(labels) == set(inventory['uses']), (set(inventory['uses']) - set(labels))
    bodies = dict(water=('wtrtyl', 'hdwtr'), lava=('lavtyl', 'hdlav'), tar=('tartyl', 'hwoil'))
    animated = set(overlays) | {base for base, _ in bodies.values()}
    tiles = {n: read(folder / (n + '.png')) for n in labels if n not in animated}
    pairs = [(a, side, b) for a in sorted(labels) for b in sorted(labels)
             for side, opposite in [('E', 'W'), ('S', 'N')] if labels[a][side] == labels[b][opposite]]
    results = []
    for phase in range(14):
        liquid = {family: read(folder / ('%s%03d.png' % (prefix, phase)))
                  for family, (_, prefix) in bodies.items()}
        for family, (base, _) in bodies.items():
            tiles[base] = liquid[family]
        for r in banks:
            rgba = overlays[r['name']]
            alpha = rgba[:, :, 3:4] / 255
            tiles[r['name']] = rgba[:, :, :3] * alpha + liquid[r['binding']['liquid']] * (1 - alpha)
        for a, side, b in pairs:
            if phase and a not in animated and b not in animated:
                continue
            metrics, _, _ = checks.metrics(tiles[a], tiles[b], side)
            results.append(dict(a=a, side=side, b=b, phase=phase, **metrics))
    failures = [r for r in results if not r['passed']]
    report = dict(scope='Every compatible E/S edge pair among197 used static tiles; all14 liquid phases',
                  checks=results, check_count=len(results), failures=failures, edge_contracts=labels,
                  manifest_sha256=sha(manifest_path), script_sha256=sha(P / 'check_complete_pack.py'),
                  metric_source_sha256=sha(P.parent / 'mm7/check.py'))
    (P / 'reports/complete_validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(len(results), 'complete-export compatible checks;', len(failures), 'failures', flush=True)
    assert not failures, [(r['a'], r['side'], r['b'], r['phase']) for r in failures[:20]]


if __name__ == '__main__':
    main()
