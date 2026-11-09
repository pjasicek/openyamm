"""Install only the accepted MM8 terrain directory, preserving existing content."""
import argparse
import json
import os
import shutil
from pathlib import Path

from common import P, ROOT, sha


def assets_snapshot(excluded):
    result = {}
    for directory, subdirectories, files in os.walk(ROOT / 'assets_dev', followlinks=False):
        parent = Path(directory)
        subdirectories[:] = [n for n in subdirectories if parent / n != excluded]
        for name in files + [n for n in subdirectories if (parent / n).is_symlink()]:
            path = parent / name
            stat = path.lstat()
            result[str(path.relative_to(ROOT))] = [stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_mode,
                                                  os.readlink(path) if path.is_symlink() else None]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-installed', action='store_true')
    args = parser.parse_args()
    acceptance_path = P / 'reports/acceptance.json'
    acceptance = json.loads(acceptance_path.read_text())
    assert acceptance['status'] == 'reviewed_for_installation'
    for relative, digest in acceptance['evidence'].items():
        assert sha(P / relative) == digest, relative
    manifest_path = P / 'complete_runtime_x2/manifest.json'
    assert sha(manifest_path) == acceptance['manifest_sha256']
    manifest = json.loads(manifest_path.read_text())
    expected = {name: record['sha256'] for name, record in manifest['files'].items()}
    source = manifest_path.parent / 'worlds/mm8/terrain_x2'
    assert {f.name: sha(f) for f in source.glob('*.png')} == expected
    destination = ROOT / 'assets_dev/worlds/mm8/terrain_x2'
    if args.verify_installed:
        assert {f.name: sha(f) for f in destination.glob('*.png')} == expected
        print('Verified', len(expected), 'installed MM8 terrain textures')
        return
    # Existing different content needs an explicit migration, never silent replacement.
    if destination.exists():
        assert {f.name: sha(f) for f in destination.iterdir()} == expected
        print('Accepted pack already installed; unchanged')
        return
    baseline = json.loads((P / 'reports/protected_baseline.json').read_text())
    for relative, digest in baseline.items():
        assert sha(ROOT / relative) == digest, relative
    originals = {str(f.relative_to(ROOT)): sha(f)
                 for directory in ('assets_dev/engine/terrain', 'assets_dev/worlds/mm8/textures')
                 for f in (ROOT / directory).iterdir() if f.is_file()}
    before = assets_snapshot(destination)
    destination.mkdir()
    for name in expected:
        shutil.copyfile(source / name, destination / name)
        (destination / name).chmod(0o644)
    assert {f.name: sha(f) for f in destination.iterdir()} == expected
    assert assets_snapshot(destination) == before, 'Unrelated asset entries changed during installation'
    for relative, digest in {**baseline, **originals}.items():
        assert sha(ROOT / relative) == digest, relative
    report = dict(status='installed_and_verified', files=expected,
                  acceptance_sha256=sha(acceptance_path), manifest_sha256=sha(manifest_path),
                  preserved_asset_entries=len(before), preserved_original_terrain=originals,
                  protected_baseline_sha256=sha(P / 'reports/protected_baseline.json'),
                  script_sha256=sha(P / 'install.py'))
    (P / 'reports/integration.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Installed', len(expected), 'textures; preserved', len(before), 'other asset entries')


if __name__ == '__main__':
    main()
