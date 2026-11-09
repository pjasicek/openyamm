#!/usr/bin/env python3
"""Set material extras and install one v2 tier. Usage: finalize.py <tier>...
work/t<N>_export.glb -> openyamm_specular (tiers.py), metallicFactor 0, roughnessFactor 1, the gem material's
emissiveFactor, single-sided -> assets_dev/engine/models/loot_satchel_t<N>.glb (0644, no LOD chain). Then parses the
installed GLB and checks: one mesh node, no skins or animations, no openyamm_lods, min Y = 0, plan width = the tier's
width."""
import json, os, struct, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tiers import ROOT, REPO, TIERS
sys.path.insert(0, os.path.join(REPO, 'tools'))
from link_static_model_lods import read_glb, write_glb

for tier in sys.argv[1:]:
    N = int(tier); CFG = TIERS[N]
    doc, binary = read_glb(Path(ROOT) / 'work' / f't{N}_export.glb')
    for mat in doc['materials']:
        # The sack is closed except under its gathered neck: single-sided halves the shaded fragments.
        mat['doubleSided'] = False
        mat.setdefault('extras', {})['openyamm_specular'] = CFG['specular']
        pbr = mat.setdefault('pbrMetallicRoughness', {})
        pbr['metallicFactor'] = 0.0
        pbr['roughnessFactor'] = 1.0
        if mat['name'].endswith('_Gem'):
            mat['emissiveFactor'] = list(CFG['gem_emissive'])
        else:
            mat.pop('emissiveFactor', None)
    out = Path(REPO) / 'assets_dev' / 'engine' / 'models' / f'loot_satchel_t{N}.glb'
    write_glb(out, doc, binary)
    os.chmod(out, 0o644)

    raw = out.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; d = json.loads(raw[20:20 + n])
    mesh_nodes = [x for x in d['nodes'] if 'mesh' in x]
    mesh = d['meshes'][mesh_nodes[0]['mesh']]
    tris = sum(d['accessors'][p['indices']]['count'] // 3 for p in mesh['primitives'])
    lo = [min(d['accessors'][p['attributes']['POSITION']]['min'][i] for p in mesh['primitives']) for i in range(3)]
    hi = [max(d['accessors'][p['attributes']['POSITION']]['max'][i] for p in mesh['primitives']) for i in range(3)]
    width = max(hi[0] - lo[0], hi[2] - lo[2])
    ok = (len(mesh_nodes) == 1 and len(d['meshes']) == 1 and not d.get('skins') and not d.get('animations')
          and 'openyamm_lods' not in mesh.get('extras', {}) and abs(lo[1]) < 1e-3 and abs(width - CFG['width']) < 0.01)
    print('VALID' if ok else 'INVALID', out.name, 'tris', tris, 'width', round(width, 3), 'height', round(hi[1], 3),
          'materials', [(m['name'], m['extras']['openyamm_specular'], m.get('emissiveFactor')) for m in d['materials']],
          'bytes', len(raw))
