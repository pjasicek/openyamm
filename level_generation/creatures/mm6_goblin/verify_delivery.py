"""Verify delivered artifact provenance, sheet placement, timing and ZIP integrity without rerendering."""
import ast
import hashlib
import json
import struct
from pathlib import Path
from zipfile import ZipFile
from PIL import Image

ROOT = Path(__file__).resolve().parent


def read(relative):
    return json.loads((ROOT / relative).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    expected = {'Standing', 'Walk', 'Attack', 'Hit', 'Death', 'Corpse', 'Fidget'}
    for item in read('source_manifest.json')['images']:
        assert sha(ROOT.parents[2] / 'assets_dev/engine/sprites' / item['name']) == item['sha256']
    model_hash = sha(ROOT / 'mm6_goblin.blend')
    glb_hash = sha(ROOT / 'mm6_goblin.glb')
    assert read('export_work/import_report.json')['glb_sha256'] == glb_hash
    for name, item in read('export_work/asset_stats.json')['files'].items():
        assert sha(ROOT / name) == item['sha256']
    assert all(read('export_work/imported_motion_report.json')['passes'].values())
    assert read('export_work/blend_reopen_report.json')['action_slot_bound']
    data = (ROOT / 'mm6_goblin.glb').read_bytes()
    size, kind = struct.unpack_from('<II', data, 12)
    assert kind == 0x4e4f534a
    gltf = json.loads(data[20:20 + size])
    assert {a['name'] for a in gltf['animations']} == expected
    assert len(gltf['skins']) == 1 and len(gltf['skins'][0]['joints']) == 88
    primitives = [p for mesh in gltf['meshes'] for p in mesh['primitives']]
    assert all({'TANGENT', 'JOINTS_0', 'WEIGHTS_0'} <= set(p['attributes']) for p in primitives)
    assert all('JOINTS_1' not in p['attributes'] for p in primitives)
    dense = read('spritesheets/manifest.json')
    assert dense['source_blend_sha256'] == model_hash
    legacy = read('spritesheets/legacy_manifest.json')
    assert {clip['name'] for clip in dense['clips']} == expected
    names = {f['texture_stem'] + str(d) for clip in dense['clips'] for f in clip['frames'] for d in range(8)}
    assert len(names) == 552
    for folder, suffix in [('masters_710x578', 'png'), ('png_355x289', 'png'), ('bmp_355x289', 'bmp')]:
        assert {f.stem for f in (ROOT / 'spritesheets' / folder).glob('*.' + suffix)} == names
    for clip in dense['clips']:
        assert abs(sum(f['duration_seconds'] for f in clip['frames']) - clip['duration_seconds']) < 1e-8
        assert all(f['duration_seconds'] > 0 for f in clip['frames'])
        old = legacy['clips'][clip['name']]
        assert all(f['frame_length_raw'] > 0 for f in old['frames'])
        assert sum(f['frame_length_raw'] for f in old['frames']) == old['animation_length_raw']
        assert abs(old['animation_length_raw'] / 16 - clip['duration_seconds']) < 1e-8
        assert all(f['texture_stem'] + '0' in names for f in old['frames'])
        with Image.open(ROOT / 'spritesheets/sheets_8view' / (clip['name'].lower() + '.png')) as atlas:
            assert atlas.size == (355 * clip['count'], 289 * 8) and atlas.mode == 'RGBA'
            # Check every atlas cell against its standalone PNG: catches ordering/offset or alpha-copy mistakes.
            for frame in clip['frames']:
                x = 355 * frame['index']
                for direction in range(8):
                    y = 289 * direction
                    with Image.open(ROOT / 'spritesheets/png_355x289' / (frame['texture_stem'] + str(direction) + '.png')) as png:
                        assert atlas.crop((x, y, x + 355, y + 289)).tobytes() == png.tobytes()
    archive_path = ROOT / 'spritesheets/mm6_goblin_mm_sprites.zip'
    with ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        files = {str(f.relative_to(ROOT / 'spritesheets')) for f in (ROOT / 'spritesheets').rglob('*')
                 if f.is_file() and f.suffix != '.zip' and f.name != 'status.txt'}
        assert set(archive.namelist()) == files
        for name in ['README.md', 'manifest.json', 'legacy_manifest.json', 'palette.json', 'validation.json']:
            assert archive.read(name) == (ROOT / 'spritesheets' / name).read_bytes()
        zip_entries = len(files)
    for script in ROOT.glob('*.py'):
        ast.parse(script.read_text(), filename=str(script))
    report = {'status': 'PASS', 'original_sprite_hashes_unchanged': 59, 'model_sha256': model_hash,
              'glb_sha256': glb_hash, 'clips': sorted(expected), 'masters_png_bmp_each': 552,
              'all_552_atlas_cells_match_png': True, 'precise_and_legacy_timing': 'PASS',
              'zip_crc_and_inventory': 'PASS', 'zip_entries': zip_entries,
              'zip_bytes': archive_path.stat().st_size, 'zip_sha256': sha(archive_path),
              'visual_review': 'See DELIVERY_AUDIT.md; this script verifies artifact integrity, not artistic quality.'}
    (ROOT / 'delivery_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    build()
