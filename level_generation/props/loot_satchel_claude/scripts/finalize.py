#!/usr/bin/env python3
"""Link LODs, set material extras and install one tier. Usage: finalize.py <tier 1..4>
work/t<N>_export.glb -> tools/link_static_model_lods.py -> material extras openyamm_specular 0.3, metallicFactor 0,
roughnessFactor 1 -> assets_dev/engine/models/loot_satchel_t<N>.glb (0644). Then parses the installed GLB and prints
the per-LOD triangle counts, bounds and the openyamm_lods check."""
import json, os, struct, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tiers import ROOT, REPO

N = int(sys.argv[1])
work = os.path.join(ROOT, 'work')
linked = os.path.join(work, f't{N}_linked.glb')
out = os.path.join(REPO, 'assets_dev', 'engine', 'models', f'loot_satchel_t{N}.glb')
subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'link_static_model_lods.py'),
                os.path.join(work, f't{N}_export.glb'), linked], check=True)
sys.path.insert(0, os.path.join(REPO, 'tools'))
from link_static_model_lods import read_glb, write_glb

from pathlib import Path
doc, binary = read_glb(Path(linked))
for mat in doc['materials']:
    mat.setdefault('extras', {})['openyamm_specular'] = 0.3
    pbr = mat.setdefault('pbrMetallicRoughness', {})
    pbr['metallicFactor'] = 0.0
    pbr['roughnessFactor'] = 1.0
write_glb(Path(out), doc, binary)
os.chmod(out, 0o644)

raw = open(out, 'rb').read(); n = struct.unpack_from('<I', raw, 12)[0]; d = json.loads(raw[20:20 + n])
mesh_nodes = [x for x in d['nodes'] if 'mesh' in x]
base = d['meshes'][mesh_nodes[0]['mesh']]
lods = base.get('extras', {}).get('openyamm_lods', [])
tri = lambda m: sum(d['accessors'][p['indices']]['count'] // 3 for p in m['primitives'])
counts = [tri(base)] + [tri(d['meshes'][i]) for i in lods]
pos = d['accessors'][base['primitives'][0]['attributes']['POSITION']]
ok = (len(mesh_nodes) == 1 and len(lods) == 3 and len(d['materials']) <= 2 and not d.get('skins')
      and not d.get('animations') and all(a > b for a, b in zip(counts, counts[1:])) and abs(pos['min'][1]) < 1e-3)
print('VALID' if ok else 'INVALID', os.path.relpath(out, REPO), 'tris', counts, 'lods', lods,
      'min', [round(v, 3) for v in pos['min']], 'max', [round(v, 3) for v in pos['max']],
      'materials', [(m['name'], m.get('extras'), m['pbrMetallicRoughness'].get('metallicFactor'), m.get('emissiveFactor')) for m in d['materials']],
      'bytes', len(raw))
