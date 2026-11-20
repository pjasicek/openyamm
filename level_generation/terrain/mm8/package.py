"""Package the installed, accepted terrain export and verify every archive member."""
import hashlib
import json
import zipfile

from common import P, ROOT, sha


def main():
    root = P / 'complete_runtime_x2'
    manifest_path = root / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    acceptance_path = P / 'reports/acceptance.json'
    integration_path = P / 'reports/integration.json'
    acceptance = json.loads(acceptance_path.read_text())
    integration = json.loads(integration_path.read_text())
    assert acceptance['status'] == 'reviewed_for_installation'
    assert integration['status'] == 'installed_and_verified'
    assert integration['acceptance_sha256'] == sha(acceptance_path)
    assert acceptance['manifest_sha256'] == sha(manifest_path)
    for relative, digest in acceptance['evidence'].items():
        assert sha(P / relative) == digest, relative
    members = {'manifest.json': manifest_path.read_bytes(), 'acceptance.json': acceptance_path.read_bytes()}
    for name, record in sorted(manifest['files'].items()):
        relative = 'worlds/mm8/terrain_x2/' + name
        source = root / relative
        assert sha(source) == record['sha256'] == sha(ROOT / 'assets_dev' / relative)
        members[relative] = source.read_bytes()
    members['README.txt'] = (
        'MM8 restored terrain, 2x (256x256), 239 PNGs for all14 outdoor maps.\n'
        'Copy worlds/ into OpenYAMM assets_dev/; originals in engine/terrain and world textures stay unchanged.\n'
        'Select x2 terrain quality. Original mode selects x1; other enhanced categories are independent.\n'
        'All14 water/lava/tar animation frames and57 RGBA banks are included.\n'
        'manifest.json records immutable export provenance; acceptance.json records subsequent review.\n'
        'Native incompatible tile placements are preserved. Full workflow and gallery:\n'
        'level_generation/terrain/mm8/{HANDOFF.md,review.html,MAPS.md}.\n').encode()
    archive_path = P / 'mm8_complete_terrain_x2.zip'
    with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 10, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(members)
        for name, data in members.items():
            assert archive.read(name) == data, name
    report = dict(status='packaged_and_verified', archive_sha256=sha(archive_path),
                  archive_bytes=archive_path.stat().st_size,
                  members={name: hashlib.sha256(data).hexdigest() for name, data in members.items()},
                  manifest_sha256=sha(manifest_path), integration_sha256=sha(integration_path),
                  script_sha256=sha(P / 'package.py'))
    (P / 'reports/package.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Packaged', len(manifest['files']), 'textures:', archive_path)


if __name__ == '__main__':
    main()
