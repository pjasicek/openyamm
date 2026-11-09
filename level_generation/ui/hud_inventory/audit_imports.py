"""Verify native logical canvases of the existing MM9 fitted/imported HUD art."""
import hashlib
import json
from pathlib import Path

import yaml
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    scope = json.loads((HERE / 'scope.json').read_text())
    inventory_manifest = ROOT / 'assets_dev/worlds/mm9/state/item_icon_manifest.yml'
    equipment_manifest = ROOT / 'assets_dev/worlds/mm9/state/item_body_equipment_visuals.yml'
    inventory = yaml.safe_load(inventory_manifest.read_text())
    equipment = yaml.safe_load(equipment_manifest.read_text())
    records = {}
    for icon in inventory['icons']:
        path = ROOT / 'assets_dev/worlds/mm9' / icon['output']
        if not path.exists():
            continue
        with Image.open(path) as image:
            size = list(image.size)
        manifest_size = [icon['width'], icon['height']]
        records[path.relative_to(ROOT).as_posix()] = dict(
            native_baseline_verified=size == manifest_size and sha(path) == icon['output_sha256'],
            native_size=size, manifest=inventory_manifest.relative_to(ROOT).as_posix(),
            manifest_sha256=sha(inventory_manifest), manifest_output_sha256=icon['output_sha256'],
            source='mm9/extracted/' + icon['source'], visual_source=icon['visual_source'],
            proof='Promoted native runtime canvas, not the original square PCX nor the larger imagegen master.',
            existing_art_is_verified_x2=False)
    for item in equipment['items']:
        for variant in item['variants']:
            path = Path(variant['output'])
            if not path.is_absolute():
                path = ROOT / path
            with Image.open(path) as image:
                size = list(image.size)
            reference = ROOT / variant['reference_asset']
            with Image.open(reference) as image:
                reference_size = list(image.size)
            records[path.relative_to(ROOT).as_posix()] = dict(
                native_baseline_verified=size == reference_size
                    and size == [variant['width'], variant['height']]
                    and sha(path) == variant['output_sha256']
                    and sha(reference) == variant['reference_asset_sha256'],
                native_size=reference_size, manifest=equipment_manifest.relative_to(ROOT).as_posix(),
                manifest_sha256=sha(equipment_manifest), manifest_output_sha256=variant['output_sha256'],
                source=variant['reference_asset'], source_sha256=variant['reference_asset_sha256'],
                visual_source=variant['visual_source'],
                proof='Promoted fitted piece has the exact native MM7/MM8 registration canvas; no existing x2 export.',
                existing_art_is_verified_x2=False)
    # The later authored manifest owns pose-pair promotions. Do not treat the older staging report as current.
    authored_path = ROOT / 'tools/mm9_import_discovery/mm9_equipment_generated_art.yml'
    authored = yaml.safe_load(authored_path.read_text())
    for item in authored['items'].values():
        for variant in item['variants'].values():
            path = ROOT / 'assets_dev/worlds/mm9/icons' / Path(variant['asset']).name
            if not path.exists():
                continue
            with Image.open(path) as image:
                size = list(image.size)
            reference = ROOT / variant['reference_asset']
            with Image.open(reference) as image:
                reference_size = list(image.size)
            records[path.relative_to(ROOT).as_posix()] = dict(
                native_baseline_verified=(size == reference_size
                    or ('constructive soft_cap target alpha with attached hanging tail' in variant.get('postprocess', '')
                        and size[0] == reference_size[0] and variant.get('review_status') == 'reviewed'))
                    and size == [variant['width'], variant['height']]
                    and sha(path) == variant['asset_sha256']
                    and sha(reference) == variant['reference_asset_sha256'],
                native_size=size, manifest=authored_path.relative_to(ROOT).as_posix(),
                manifest_sha256=sha(authored_path), manifest_output_sha256=variant['asset_sha256'],
                source=variant['reference_asset'], source_sha256=variant['reference_asset_sha256'],
                visual_source=variant['generation_tool'],
                proof='Current authored native pose-pair promotion; preserve explicitly reviewed soft-cap tail extensions.',
                existing_art_is_verified_x2=False)
    container_provenance = ROOT / 'assets_dev/worlds/mm9/icons/MM9_CONTAINER_BACKGROUND_PROVENANCE.md'
    for name in ('mm9_chest.png', 'mm9_treasure_bag.png'):
        path = container_provenance.parent / name
        with Image.open(path) as image:
            size = list(image.size)
        records[path.relative_to(ROOT).as_posix()] = dict(
            native_baseline_verified=size == [460, 344], native_size=[460, 344],
            manifest=container_provenance.relative_to(ROOT).as_posix(), manifest_sha256=sha(container_provenance),
            visual_source='authored_native_container_background',
            proof='Provenance records downsampling to the native 460x344 OpenYAMM chest panel, checked against file.',
            existing_art_is_verified_x2=False)
    rows = []
    for row in scope['files']:
        if '/worlds/mm9/icons/' not in row['id']:
            continue
        result = dict(path=row['id'], sha256=row['sha256'])
        result.update(records.get(row['id'], dict(native_baseline_verified=False, proof='Needs separate provenance.')))
        rows.append(result)
    result = dict(summary=dict(files=len(rows), verified=sum(r['native_baseline_verified'] for r in rows),
                  remaining=[r['path'] for r in rows if not r['native_baseline_verified']], generation_started=False), files=rows)
    (HERE / 'import_audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['summary'], indent=2))


if __name__ == '__main__':
    main()
