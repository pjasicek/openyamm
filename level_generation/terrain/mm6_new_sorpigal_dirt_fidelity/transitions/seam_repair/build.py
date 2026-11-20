"""Recompose the accepted new-dirt transitions with continuous quilted material borders.

Reuse the established terrain quilting workflow and the accepted AI transition deltas.
Material gutters wrap; coverage and contact shading extend to the neighbouring tile.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parent
PROJECT = P.parent
TERRAIN = PROJECT.parents[1]
spec = importlib.util.spec_from_file_location('terrain_seams', TERRAIN / 'seam_repair/build.py')
seams = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seams)


def main():
    study = TERRAIN / 'mm6_new_sorpigal_master_study'
    decisions = json.loads((study / 'material_decisions.json').read_text())
    sources = {name: study / decisions[name]['master_png'] for name in ('grass', 'volcano', 'cobbles')}
    sources['dirt'] = PROJECT.parent / 'generated/dirt_v2_512.png'
    authoring = PROJECT / 'composites/v2'
    runtime = PROJECT / 'edge_treatment/runtime/v2'
    for directory in (P / 'materials', authoring, runtime):
        directory.mkdir(parents=True, exist_ok=True)
    materials = {}
    for name, source in sources.items():
        original = np.asarray(Image.open(source).convert('RGB').resize((512, 512)), dtype=float)
        repaired = seams.periodic(original.copy())
        assert np.array_equal(repaired[64:-64, 64:-64], original[64:-64, 64:-64])
        Image.fromarray(seams.byte(repaired)).save(P / 'materials' / (name + '.png'))
        materials[name] = seams.linear(seams.pad(repaired, 'wrap'))

    def save(name, padded):
        Image.fromarray(seams.byte(padded[8:-8, 8:-8])).save(authoring / (name + '.png'))
        Image.fromarray(seams.reduce(padded)).save(runtime / (name + '.png'))

    for tile, name in [('6dirttyl', 'dirt'), ('6grastyl', 'grass'), ('6voltyl', 'volcano')]:
        save(tile, seams.srgb(materials[name]))
    records = json.loads((PROJECT / 'mask_inventory.json').read_text())['masks']
    for record in records:
        tile = record['tile']
        alpha = seams.pad(seams.read(PROJECT / 'masks/connected_v4' / (tile + '.png')) / 255, 'edge')[:, :, None]
        delta = seams.pad(np.load(PROJECT / 'edge_treatment/layers/v1' / (tile + '.npz'))['linear_rgb_delta'], 'edge')
        save(tile, seams.srgb(materials['dirt'] * (1 - alpha) + materials[record['white']] * alpha + delta))
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    report = {
        'runtime_size': 256, 'authoring_size': 512,
        'method': 'Periodic donor strips with cyclic minimum-error cuts; wrapped material gutters during downsampling.',
        'sources': {name: {'path': str(path.relative_to(TERRAIN)), 'sha256': sha(path)} for name, path in sources.items()},
        'central_384_square_master_pixels_unchanged': True,
        'coverage': 'All 33 connected_v4 masks unchanged, including native directional orientation.',
        'transition_art': 'Accepted v1 AI linear RGB deltas reused unchanged.',
        'files': {f.name: sha(f) for f in sorted(runtime.glob('*.png'))},
        'supersedes': 'v1 mirrored/averaged material borders; opposite samples now continue the texture instead of matching exactly.',
    }
    (P / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Exported {len(report["files"])} tiles to {runtime}')


if __name__ == '__main__':
    main()
