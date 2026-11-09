"""Install explicitly reviewed owned designs through the shared per-model installer."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw

project = Path(__file__).resolve().parents[1]
repo = project.parents[2]
designs = json.loads((project / 'designs.json').read_text())
owned = {entry['icon'] for entry in json.loads((project / 'ownership.json').read_text())}
ledger = json.loads((project / 'ledger.json').read_text())
entries = {entry['icon']: entry for entry in ledger}
names = sys.argv[1:]
assert names and len(names) == len(set(names))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for name in names:
    design = designs[name]
    icon = design['master_icon']
    assert design['icons'] == [icon] and icon in owned
    entry = entries[icon]
    assert not entry.get('external_install'), (icon, 'preserve concurrent job installation')
    assert not entry.get('delegated_geometry_project'), (icon, 'reserved for geometry-finish worker')
    export = project / 'work/codex_tex' / f'{name}_export.glb'
    status = json.loads((project / 'review' / f'{name}_bake_status.json').read_text())
    assert status['baked'] and status['export_sha256'] == digest(export), (name, 'latest bake failed or changed')
    report_path = project / 'review' / f'{name}_export_check.json'
    report = json.loads(report_path.read_text())
    assert report['export_sha256'] == digest(export), (name, 'stale export check')
    review_time = max(export.stat().st_mtime, (project / 'scripts/review_items.py').stat().st_mtime)
    for view in ['above', 'three_quarter', 'low', 'front', 'back']:
        assert (project / 'review/codex_tex' / f'{name}_{view}.png').stat().st_mtime >= review_time
    source = repo / 'assets_source/engine/world_items/models' / f'item_{icon}.glb'
    runtime = repo / 'assets_dev/engine/world_items/models' / f'item_{icon}.glb'
    expected = 'installed' if entry['replacement_installed'] else 'baseline'
    assert digest(source) == entry[f'{expected}_source_sha256'], (icon, 'source changed since inspection')
    assert digest(runtime) == entry[f'{expected}_runtime_sha256'], (icon, 'runtime changed since inspection')
    sheet = Image.new('RGBA', (1152, 416), (34, 38, 45, 255))
    ImageDraw.Draw(sheet).text((8, 8), icon + ' / ' + design['title'] + ' / icon, above, low', fill='white')
    paths = [repo / 'assets_dev/engine/icons_x2' / f'{icon}.png']
    paths += [project / 'review/codex_tex' / f'{name}_{view}.png' for view in ['above', 'low']]
    for column, path in enumerate(paths):
        tile = Image.open(path).convert('RGBA')
        tile.thumbnail((384, 384))
        sheet.alpha_composite(tile, (column * 384 + (384 - tile.width) // 2, 32 + (384 - tile.height) // 2))
    sheet_path = project / 'review' / f'accepted_{icon}.png'
    sheet.convert('RGB').save(sheet_path)
    with (project / 'review' / f'install_{icon}.log').open('w') as log:
        subprocess.run([sys.executable, str(repo / 'tools/install_model.py'), str(export), '--world-items',
                        '--name', f'item_{icon}.glb'], cwd=repo, stdout=log, stderr=subprocess.STDOUT, check=True)
    entry.update(decision='replaced', replacement_installed=True, inspected=True,
                 reason='Source icon, above/low comparison and verified front-face review passed; full volume and material classes retained.',
                 triangles=report['triangles'], texture_size=512,
                 review_sheet=str(sheet_path.relative_to(project)),
                 above=f'review/codex_tex/{name}_above.png', low=f'review/codex_tex/{name}_low.png',
                 export_check=str(report_path.relative_to(project)), reviewed_export_sha256=digest(export),
                 installed_source_sha256=digest(source), installed_runtime_sha256=digest(runtime),
                 interior_albedo_review_pending=False, pose_correction_pending=False, native_review_pending=True)
    (project / 'ledger.json').write_text(json.dumps(ledger, indent=2) + '\n')
    print('INSTALLED_REVIEWED', icon, report['triangles'], flush=True)
