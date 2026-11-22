#!/usr/bin/env python3
"""Write the non-Meshy fields of creature_3d_progress.json (run under the lease: creature_workspace.py run).
Usage: update_progress.py <stage> [key=value ...] (status fields)"""
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
p = ROOT / 'creature_3d_progress.json'
d = json.loads(p.read_text())
sha = lambda f: hashlib.sha256(Path(f).read_bytes()).hexdigest()
d['references_hd'] = {f.name: sha(f) for f in sorted((ROOT / 'references_hd').glob('0*.png'))}
d['required_components'] = [{'id': 'body', 'artifact_role': 'body', 'required': True,
                             'note': 'one mesh: body, head, sabre fangs, paws with claws, tail'}]
src = REPO / 'assets_source/worlds/xeen/models/xeen_saber.glb'
if src.exists():
    d['installed'] = {'source': 'assets_source/worlds/xeen/models/xeen_saber.glb', 'sha256': sha(src),
                      'runtime_sha256': sha(REPO / 'assets_dev/worlds/xeen/models/xeen_saber.glb'),
                      'skins': ['saber_a'],
                      'binding': 'integration/actors.yml (Xeen Wolf B, Xeen Wolf D), not merged: the parent xeen-s5 merges it'}
st = d.setdefault('status', {})
st['stage'] = sys.argv[1]
for kv in sys.argv[2:]:
    k, v = kv.split('=', 1); st[k] = v
p.write_text(json.dumps(d, indent=1) + '\n')
print('PROGRESS', st)
