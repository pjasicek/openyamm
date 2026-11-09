"""Bake explicitly named equipment candidates; keep each failure reviewable."""
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codex_texture as texture

names = sys.argv[sys.argv.index('--') + 1:]
assert names and all(name in texture.DESIGNS for name in names)
results = {}
for name in names:
    try:
        texture.bake(name)
        export = Path(texture.WORK) / f'{name}_export.glb'
        results[name] = {'baked': True, 'export_sha256': hashlib.sha256(export.read_bytes()).hexdigest()}
    except Exception as error:
        results[name] = {'baked': False, 'error': str(error)}
        print('BAKE_FAILED', name, str(error), flush=True)
    (Path(texture.HERE) / 'review' / f'{name}_bake_status.json').write_text(
        json.dumps(results[name], indent=2) + '\n')
path = Path(texture.HERE) / 'review' / 'bake_batch_latest.json'
path.write_text(json.dumps(results, indent=2) + '\n')
(path.parent / ('bake_batch_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json')).write_text(
    path.read_text())
assert all(result['baked'] for result in results.values()), results
