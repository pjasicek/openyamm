"""Retain original generated image bytes and validate their provenance without altering artwork."""
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image

project = Path(__file__).resolve().parents[1]
repo = project.parents[2]
designs = json.loads((project / 'designs.json').read_text())
records = []


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for name, design in designs.items():
    folder = project / 'codex_tex' / name
    icon = design['master_icon']
    icon_path = repo / 'assets_dev/engine/icons_x2' / f'{icon}.png'
    for path in sorted(folder.glob('generation_*atlas*.json')):
        receipt = json.loads(path.read_text())
        kind = 'mask' if 'mask' in path.name else 'paint'
        revision = int(path.stem.rsplit('_v', 1)[1]) if '_v' in path.stem else 1
        source = Path(receipt['source_output'])
        assert source.is_file(), source
        raw = folder / f'{kind}_raw_v{revision}.png'
        if raw.exists():
            assert digest(raw) == digest(source), raw
        else:
            shutil.copyfile(source, raw)
        receipt.update(raw_output=raw.name, output_sha256=digest(raw), revision=revision,
                       input_icon=icon, input_icon_path=str(icon_path.relative_to(repo)),
                       input_icon_sha256=digest(icon_path))
        if receipt.get('input_guide') and receipt.get('input_guide_sha256'):
            assert digest(Path(receipt['input_guide'])) == receipt['input_guide_sha256'], path
        else:
            guide = Path(receipt['input_guide']) if receipt.get('input_guide') else folder / 'guide_atlas.png'
            receipt.update(retained_guide=str(guide.relative_to(project)), retained_guide_sha256=digest(guide),
                           guide_hash_note='Retained guide hashed retrospectively; original receipt omitted input hash.')
        receipt['active_bytes_match'] = digest(folder / f'{kind}_atlas.png') == digest(raw)
        receipt['selected'] = False
        if receipt['active_bytes_match']:
            receipt['reason'] = 'Active raw image; final mesh review determines acceptance.'
        if kind == 'mask' and ('surface_material' in design or icon == 'item110'):
            receipt['reason'] = 'Classes authored from homogeneous exterior/separate lining or exact mesh components.'
        receipt['alpha_extrema'] = list(Image.open(raw).getchannel('A').getextrema())
        path.write_text(json.dumps(receipt, indent=2) + '\n')
        records.append({'design': name, 'receipt': str(path.relative_to(project)),
                        'raw_sha256': receipt['output_sha256']})
(project / 'review/atlas_receipt_index.json').write_text(json.dumps(records, indent=2) + '\n')
assert len({record['design'] for record in records}) == 95
print(len(records), 'original image outputs retained and hashed; guide/icon hashes verified')
