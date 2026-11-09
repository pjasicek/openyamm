"""Assemble the complete candidate union from retained sources, without installing it.

The historical runtime_x2 directory is a build input, not the complete reviewed union.
This export remains a candidate until the separate visual/integration gates are complete.
"""
import json
import shutil

from common import P, OUT, Image, sha


def main():
    stage_path = P / 'reports/candidate_stage.json'
    inventory_path = P / 'effective_inventory.json'
    stage = json.loads(stage_path.read_text())
    inventory = json.loads(inventory_path.read_text())
    expected = {name + '.png' for name in inventory['runtime_names']}
    assert set(stage['files']) == expected
    export = P / 'complete_runtime_x2'
    destination = export / 'worlds/mm8/terrain_x2'
    destination.mkdir(parents=True, exist_ok=True)
    assert not ({f.name for f in destination.iterdir()} - expected), 'Unexpected files in export'
    overlays = {r['name'] + '.png' for r in
                json.loads((P / 'liquids/banks_v2/build.json').read_text())['tiles']}
    records = {}
    for name, digest in sorted(stage['files'].items()):
        source = P / stage['overrides'][name] if name in stage['overrides'] else OUT / name
        assert sha(source) == digest, source
        image = Image.open(source)
        assert image.size == (256, 256), (name, image.size)
        assert image.mode == ('RGBA' if name in overlays else 'RGB'), (name, image.mode)
        target = destination / name
        shutil.copy2(source, target)
        target.chmod(0o644)
        assert sha(target) == digest
        records[name] = dict(sha256=digest, source=str(source.relative_to(P)),
                             mode=image.mode, size=list(image.size), bytes=target.stat().st_size)
    assert {f.name for f in destination.glob('*.png')} == expected
    manifest = dict(status='complete_coverage_candidate_not_installed_or_finally_accepted',
                    world='mm8', scale=2, static_count=len(inventory['uses']),
                    animation_frame_count=len(expected) - len(inventory['uses']),
                    texture_count=len(records), files=records,
                    inventory_sha256=sha(inventory_path), candidate_stage_sha256=sha(stage_path),
                    script_sha256=sha(P / 'assemble_pack.py'))
    (export / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Assembled', len(records), 'textures from retained sources; no production changes')


if __name__ == '__main__':
    main()
