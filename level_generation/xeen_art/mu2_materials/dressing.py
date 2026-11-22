#!/usr/bin/env python3
"""Decorations (trees, rocks, plants) of the shipped reference maps, counted per map from `oymap export`, and the
ground tiles' material layers from each map's terrain_materials file: dressing.json."""
import collections, json, subprocess, sys, yaml
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from capture import REFS
SKIP = ('start', 'torch', 'fire', 'campfire', 'well', 'fountain', 'sign', 'chest', 'barrel', 'cart', 'pedestal',
        'brazier', 'lamp', 'bench', 'banner', 'boat', 'ship', 'flag', 'shrine', 'statue', 'cauldron', 'crate', 'pole',
        'trash', 'sound', 'fence', 'post', 'buoy', 'gate', 'column', 'obelisk')
out = {}
for world, stem in REFS:
    tmp = ROOT / 'output/xeen_a6_mu2_exports' / f'{world}_{stem[:-4]}.json'
    tmp.parent.mkdir(parents=True, exist_ok=True)
    if not tmp.exists():
        subprocess.run([str(ROOT / 'openyamm-studio/build-xeen/oymap'), 'export', stem, '--world', world, '--assets',
                        str(ROOT / 'assets_dev'), '--out', str(tmp)], check=True, capture_output=True)
    data = json.loads(tmp.read_text())['map']
    names = collections.Counter(e['name'].lower() for e in data['entities'])
    deco = [(n, c) for n, c in names.most_common() if not any(s in n for s in SKIP)][:14]
    mat = ROOT / f'assets_dev/worlds/{world}/terrain_materials/{stem[:-4]}.yml'
    layers = []
    if mat.exists():
        layers = [(l['name'], l['library'], l.get('tint')) for l in yaml.safe_load(mat.read_text())['layers']]
    out[f'{world}/{stem}'] = {'decorations': deco, 'layers': layers}
    print(world, stem, [f'{n}x{c}' for n, c in deco][:10], [l[1] for l in layers])
(HERE / 'dressing.json').write_text(json.dumps(out, indent=1) + '\n')
