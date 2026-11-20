"""Bake only the requested, registered gauntlet paintings, with a persistent per-model receipt."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import codex_texture as texture

target = P / 'receipts/gauntlet_bakes.json'
records = json.loads(target.read_text()) if target.exists() else {}
for name in sys.argv[sys.argv.index('--') + 1:]:
    assert texture.DESIGNS[name]['family'] == 'gauntlets', name
    texture.bake(name, str(P / 'codex_tex' / name / 'aligned'))
    source = P / 'work/codex_tex' / f'{name}_export.glb'
    output = P / 'work/finished' / source.name
    shutil.copy2(source, output)
    records[name] = {'export': str(output.relative_to(P)), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                     'paint_views': texture.PAINT_VIEWS, 'geometry': 'Reused paid Meshy Smart Topology, lined locally',
                     'normal': 'OpenGL tangent detail derived from the Imagegen painting',
                     'pbr': 'Discrete painted classes; metal binary; roughness by physical material'}
    target.write_text(json.dumps(records, indent=2) + '\n')
    print('FINISHED', name, flush=True)
