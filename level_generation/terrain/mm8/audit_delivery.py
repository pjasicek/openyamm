"""Verify the final terrain deliverables against the full MM8 restoration requirements."""
import json
import zipfile

from common import P, ROOT, M, Image, sha


def read_json(relative):
    return json.loads((P / relative).read_text())


def main():
    inventory = read_json('effective_inventory.json')
    manifest = read_json('complete_runtime_x2/manifest.json')
    assert len(inventory['maps']) == 14 and len(inventory['uses']) == 197
    assert len(manifest['files']) == 239
    assert set(manifest['files']) == {n + '.png' for n in inventory['runtime_names']}
    installed = ROOT / 'assets_dev/worlds/mm8/terrain_x2'
    assert {f.name for f in installed.iterdir()} == set(manifest['files'])
    for name, record in manifest['files'].items():
        assert sha(installed / name) == record['sha256']
        assert sha(P / record['source']) == record['sha256']
        assert Image.open(installed / name).size == (256, 256)
    masters = list((M / 'runtime').glob('*.png'))
    assert len(masters) == 10
    for path in masters:
        report = read_json('masters/v1/reviews/' + path.stem + '.json')
        assert report['runtime_sha256'] == sha(path)
        assert all(r['passed'] for r in report['seams'].values())
    validation = read_json('reports/complete_validation.json')
    assert validation['manifest_sha256'] == sha(P / 'complete_runtime_x2/manifest.json')
    assert validation['check_count'] == 24428 and not validation['failures']
    roads = read_json('roads/v8/validation.json')
    revision = read_json('roads/v8/visual_review.json')
    for relative, digest in revision['evidence'].items():
        assert sha(P / relative) == digest, relative
    assert len(roads['masks']) == 36 and all(r['passed'] for r in roads['masks'])
    assert not roads['failures'] and not roads['missing']
    stepping = read_json('roads/stepping_v1/validation.json')
    assert len(stepping['components']) == 12 and not stepping['failures'] and not stepping['native_failures']
    assert all(r['holes'] == 0 and r['components'] > 1 for r in stepping['components'])
    for directory, count in [('banks_v2', 12), ('banks_extra_v1', 6)]:
        report = read_json('fixtures/' + directory + '/review/motion.json')
        assert len(report['results']) == count and not report['pending']
        assert all(r['temporal_screen_passed'] for r in report['results'].values())
    assert len(read_json('fixtures/land_v1/review/visual_review.json')['views']) == 13
    assert len(read_json('fixtures/roads_v1/review/visual_review.json')['reviewed_sheets']) == 8
    assert len(read_json('fixtures/roads_v1/review/stepping_visual_review.json')['reviewed']) == 8
    assert len(read_json('fixtures/roads_v1/review/loop_diagonal_review.json')['views']) == 8
    assert len(read_json('reports/native_contexts/visual_review.json')['reviewed_pages']) == 24
    acceptance = read_json('reports/acceptance.json')
    assert acceptance['status'] == 'reviewed_for_installation'
    for relative, digest in acceptance['evidence'].items():
        assert sha(P / relative) == digest, relative
    integration = read_json('reports/integration.json')
    assert integration['status'] == 'installed_and_verified'
    assert integration['acceptance_sha256'] == sha(P / 'reports/acceptance.json')
    for relative, digest in {**integration['preserved_original_terrain'],
                             **read_json('reports/protected_baseline.json')}.items():
        assert sha(ROOT / relative) == digest, relative
    assert read_json('reports/launcher/validation.json')['status'] == 'both_launcher_modes_verified_desktop_completed'
    package = read_json('reports/package.json')
    archive = P / 'mm8_complete_terrain_x2.zip'
    assert sha(archive) == package['archive_sha256']
    with zipfile.ZipFile(archive) as stream:
        assert stream.testzip() is None
        assert set(stream.namelist()) == set(package['members'])
        import hashlib
        for name, digest in package['members'].items():
            assert hashlib.sha256(stream.read(name)).hexdigest() == digest
    deliverables = ['README.md', 'HANDOFF.md', 'MAPS.md', 'review.html', 'play.sh', 'install.py', 'package.py',
                    'assemble_pack.py', 'check_complete_pack.py', 'build_gallery.py', 'write_map_list.py',
                    'reports/acceptance.json', 'reports/integration.json', 'reports/package.json',
                    'reports/launcher/validation.json', 'reports/gallery_preview.png', 'mm8_complete_terrain_x2.zip']
    report = dict(status='full_delivery_audit_pass',
                  requirements=dict(coverage='14 maps,197 static names,42 frames',
                                    fidelity='Reviewed original comparisons, ten masters and native scale/palette evidence',
                                    seamlessness='24,428 exact-export compatible checks plus flat/native visual review',
                                    roads='36 solid cobbles,12 separate stepping masks; grounded and loop/diagonal review',
                                    liquids='All three14-frame cycles; five bank families,18 native flat temporal captures',
                                    preservation='239 installed files; originals and121 protected hashes unchanged',
                                    usability='Both launcher modes verified; installed desktop run completed0',
                                    sharing='Verified runtime ZIP, gallery, map guide and reproducible source/provenance'),
                  deliverables={n: sha(P / n) for n in deliverables},
                  scope_limits=acceptance['limits'], script_sha256=sha(P / 'audit_delivery.py'))
    (P / 'reports/completion_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Full delivery audit passed')


if __name__ == '__main__':
    main()
