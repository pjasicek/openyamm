"""Compose new-dirt shore overlays and assemble the 63-file accepted terrain pack."""
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

P = Path(__file__).resolve().parent
TRANSITIONS = P.parent
TERRAIN = TRANSITIONS.parents[1]
ROOT = TERRAIN.parents[1]
WATER = TERRAIN / 'mm6_new_sorpigal_water'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return np.asarray(Image.open(path), dtype=float)


def pad(a, mode):
    return np.pad(a, [(8, 8), (8, 8)] + [(0, 0)] * (a.ndim - 2), mode=mode)


def byte(a):
    return np.uint8(np.clip(np.rint(a), 0, 255))


def main():
    handoff = json.loads((TRANSITIONS / 'HANDOFF_ASSETS.json').read_text())
    out = P / 'runtime_x2/worlds/mm6/terrain_x2'
    for directory in (out, P / 'authoring', P / 'shading'):
        directory.mkdir(parents=True, exist_ok=True)
    assert len(handoff['accepted_files']) == 51
    for name, record in handoff['accepted_files'].items():
        source = ROOT / record['source']
        assert sha(source) == record['sha256'], source
        shutil.copy2(source, out / name)
    for path, record in handoff['master_references'].items():
        assert sha(ROOT / path) == record['sha256'], path
    dirt_source = TRANSITIONS / 'seam_repair/materials/dirt.png'
    dirt = read(dirt_source)
    assert dirt.shape == (512, 512, 3)
    bank_source = P / 'bank_detail/periodic.png'
    bank = read(bank_source)
    assert bank.shape == dirt.shape
    records = []
    for name in handoff['remaining_shoreline_tiles']:
        coverage_source = WATER / 'restoration_v3/authoring' / name
        source = read(coverage_source)
        alpha = source[:, :, 3]
        # Extend the existing compatible coverage profiles beyond the tile before measuring
        # distance. This preserves the same bank width through shared shoreline edges.
        distance = distance_transform_edt(np.pad(alpha > 127, 128, mode='edge'))[128:-128, 128:-128]
        t = np.clip(distance / 80, 0, 1)
        weight = .85 * (1 - t * t * (3 - 2 * t))
        shade = 1 - .22 * np.exp(-distance / 18)
        interior = distance >= 80
        shade[interior] = 1
        np.save(P / 'shading' / (Path(name).stem + '.npy'), shade)
        padded = np.dstack([(pad(dirt, 'wrap') * (1 - pad(weight, 'edge')[:, :, None]) +
                             pad(bank, 'wrap') * pad(weight, 'edge')[:, :, None]) * pad(shade, 'edge')[:, :, None], pad(alpha, 'edge')])
        author = byte(padded[8:-8, 8:-8])
        assert np.array_equal(author[:, :, 3], alpha)
        assert np.array_equal(author[:, :, :3][interior], dirt[interior])
        Image.fromarray(author).save(P / 'authoring' / name)
        # Pillow's RGBA Lanczos reduction uses premultiplied alpha. Materials wrap in the
        # gutter; coverage/contact shade extend the compatible neighbouring edge profile.
        runtime = Image.fromarray(byte(padded)).resize((264, 264), Image.Resampling.LANCZOS).crop((4, 4, 260, 260))
        runtime.save(out / name)
        records.append({'tile': name, 'coverage_source': str(coverage_source.relative_to(ROOT)),
                        'coverage_source_sha256': sha(coverage_source), 'authoring_alpha_unchanged': True,
                        'interior_dirt_exact': True, 'shade_range': [float(shade.min()), float(shade.max())]})
    files = {f.name: sha(f) for f in sorted(out.glob('*.png'))}
    assert len(files) == 63
    assert all(files[n] == r['sha256'] for n, r in handoff['accepted_files'].items())
    report = {'iteration': 'dirt_fidelity_shores_v2', 'files': files, 'runtime_size': 256, 'authoring_size': 512,
              'accepted_files_preserved': 51, 'accepted_handoff_sha256': sha(TRANSITIONS / 'HANDOFF_ASSETS.json'),
              'dirt_source': str(dirt_source.relative_to(ROOT)), 'dirt_sha256': sha(dirt_source),
              'shorelines': records, 'method': 'Accepted repeating dirt, existing alpha, AI damp-earth detail blended within 80px of shore, contact shade; wrapped material gutters',
              'new_ai_painting': True, 'bank_detail_sha256': sha(bank_source),
              'bank_detail_source': str(bank_source.relative_to(ROOT)), 'bank_width_authoring_pixels': 80}
    (P / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    manifest = {'iteration': report['iteration'], 'size': [256, 256], 'dirt_master': 'dirt_fidelity_v2_periodic',
                'water': 'native_water_v3 unchanged', 'files': {'worlds/mm6/terrain_x2/' + n: h for n, h in files.items()}}
    (P / 'runtime_x2/manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Built 12 new-dirt RGBA shores; preserved all 51 accepted land/water files.')


if __name__ == '__main__':
    main()
