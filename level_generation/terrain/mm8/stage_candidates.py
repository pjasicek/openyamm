"""Stage the current terrain candidates without installing them into development assets."""
import argparse
import configparser
import json
import shutil
import time
from common import *
from inventory import GROUPS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--grey-family', action='store_true', help='Stage the reviewed shared-art family candidate')
    parser.add_argument('--stepping-paths', action='store_true', help='Stage the screened desert stepping paths')
    parser.add_argument('--liquids', action='store_true', help='Stage the screened water/lava/tar cycles')
    parser.add_argument('--banks-v2', action='store_true', help='Stage the cleaned, topology-preserving liquid banks')
    parser.add_argument('--volcano-variant', action='store_true', help='Stage the corrected volcanic patch variant')
    args = parser.parse_args()
    overrides = {}
    if args.grey_family:
        folder = P / 'transitions/grey_family_v1'
        build = json.loads((folder / 'build.json').read_text())
        validation = json.loads((folder / 'validation.json').read_text())
        assert validation['build_sha256'] == sha(folder / 'build.json')
        assert not validation['failures']
        for record in build['tiles']:
            source = folder / 'runtime' / (record['name'] + '.png')
            assert sha(source) == record['runtime_sha256']
            overrides[source.name] = source
        effective = json.loads((P / 'effective_inventory.json').read_text())
        assert 'gdtyl' in effective['runtime_names']
        overrides['gdtyl.png'] = M / 'runtime/grey_dirt.png'
    if args.stepping_paths:
        folder = P / 'roads/stepping_v1'
        build = json.loads((folder / 'build.json').read_text())
        validation = json.loads((folder / 'validation.json').read_text())
        assert validation['build_sha256'] == sha(folder / 'build.json')
        assert not validation['failures'] and not validation['native_failures']
        assert len(build['tiles']) == 12
        for record in build['tiles']:
            source = folder / 'runtime' / (record['name'] + '.png')
            assert sha(source) == record['runtime_sha256']
            overrides[source.name] = source
    if args.liquids:
        folder = P / 'liquids/v1'
        build = json.loads((folder / 'build.json').read_text())
        validation = json.loads((folder / 'validation.json').read_text())
        assert validation['build_sha256'] == sha(folder / 'build.json')
        assert not validation['failures'] and validation['opaque_bank_max_phase_change'] == 0
        assert set(build['families']) == {'water', 'lava', 'tar'}
        for family in build['families'].values():
            assert family['seams']['passed'] and len(family['files']) == 15
            for record in family['files']:
                source = folder / 'runtime' / record['name']
                assert sha(source) == record['sha256']
                overrides[source.name] = source
    if args.banks_v2:
        assert args.liquids, '--banks-v2 requires --liquids'
        folder = P / 'liquids/banks_v2'
        build = json.loads((folder / 'build.json').read_text())
        validation = json.loads((folder / 'validation.json').read_text())
        assert validation['transition_build_sha256'] == sha(folder / 'build.json')
        assert validation['build_sha256'] == sha(P / 'liquids/v1/build.json')
        assert not validation['failures'] and validation['opaque_bank_max_phase_change'] == 0
        assert len(build['tiles']) == 57
        for record in build['tiles']:
            source = folder / 'runtime' / (record['name'] + '.png')
            assert sha(source) == record['runtime_sha256']
            assert record['original_components'] == record['components']
            assert record['original_void_components'] == record['void_components']
            overrides[source.name] = source
    if args.volcano_variant:
        folder = P / 'variants/volcano_v2'
        build = json.loads((folder / 'build.json').read_text())
        review = json.loads((folder / 'review.json').read_text())
        assert review['build_sha256'] == sha(folder / 'build.json')
        assert review['status'] == 'offline_context_review_pass_native_capture_pending'
        assert build['compatible_checks'] and all(r['passed'] for r in build['compatible_checks'])
        source = folder / 'runtime/voltylx.png'
        assert sha(source) == build['runtime_sha256']
        overrides[source.name] = source
    inventory = json.loads((P / 'inventory.json').read_text())
    for record in inventory['tiles']:
        source = M / 'runtime' / (record['family'] + '.png')
        if record['kind'] == 'base' and source.exists():
            OUT.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, OUT / (record['name'] + '.png'))
    root = STAGE / 'enhanced'
    assets = root / 'assets_dev'
    assets.mkdir(parents=True, exist_ok=True)
    for path in (ROOT / 'assets_dev').iterdir():
        if path.name != 'worlds' and not (assets / path.name).exists():
            (assets / path.name).symlink_to(path, target_is_directory=path.is_dir())
    (assets / 'worlds').mkdir(exist_ok=True)
    for world in (ROOT / 'assets_dev/worlds').iterdir():
        target = assets / 'worlds' / world.name
        if world.name != 'mm8':
            if not target.exists():
                target.symlink_to(world, target_is_directory=world.is_dir())
            continue
        target.mkdir(exist_ok=True)
        for path in world.iterdir():
            if path.name != 'terrain_x2' and not (target / path.name).exists():
                (target / path.name).symlink_to(path, target_is_directory=path.is_dir())
        terrain = target / 'terrain_x2'
        terrain.mkdir(exist_ok=True)
        for path in OUT.glob('*.png'):
            shutil.copy2(overrides.get(path.name, path), terrain / path.name)
        for name, source in overrides.items():
            if not (OUT / name).exists():
                shutil.copy2(source, terrain / name)
    config = configparser.ConfigParser(interpolation=None)
    config.read(STAGE / 'original/settings.ini')
    config['assets']['root'] = str(assets)
    config['video_quality']['terrain'] = 'x2'
    with (root / 'settings.ini').open('w') as stream:
        config.write(stream)
    files = {p.name: sha(overrides.get(p.name, p)) for p in OUT.glob('*.png')}
    files.update({name: sha(path) for name, path in overrides.items()})
    report = dict(status='partial_candidate_stage_not_final_installation', files=files,
                  overrides={name: str(path.relative_to(P)) for name, path in overrides.items()},
                  stage=str(root), assets_updated_ns=time.time_ns(), binary_sha256=sha(STAGE / 'openyamm'))
    (P / 'reports/candidate_stage.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Staged', len(files), 'candidate PNGs; production assets unchanged')


if __name__ == '__main__':
    main()
