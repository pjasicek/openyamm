#!/usr/bin/env python3
"""What else changed besides geometry: compares the installed and the candidate GLB's images, materials, textures,
samplers, skins (joints, inverse binds), nodes, animations (sampler bytes), the root extensions (variants) and each
LOD0 primitive's variant mappings. Usage: same_parts.py <installed.glb> <candidate.glb>"""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
A, a = read_glb(Path(sys.argv[1])); B, b = read_glb(Path(sys.argv[2]))
h = lambda doc, bin_, i: hashlib.sha256(accessor_bytes(doc, bin_, i)).hexdigest()
def view(doc, bin_, i):
    v = doc['bufferViews'][i]; o = v.get('byteOffset', 0); return hashlib.sha256(bin_[o:o + v['byteLength']]).hexdigest()
res = {}
res['images'] = [view(A, a, im['bufferView']) for im in A['images']] == [view(B, b, im['bufferView']) for im in B['images']]
for k in ('materials', 'textures', 'samplers', 'nodes', 'extensions', 'extensionsUsed'):
    res[k] = A.get(k) == B.get(k)
res['skins'] = [(s['joints'], h(A, a, s['inverseBindMatrices'])) for s in A['skins']] == [(s['joints'], h(B, b, s['inverseBindMatrices'])) for s in B['skins']]
an = lambda doc, bin_: [(x['name'], [(c['target'], x['samplers'][c['sampler']].get('interpolation')) for c in x['channels']],
                         [(h(doc, bin_, s['input']), h(doc, bin_, s['output'])) for s in x['samplers']]) for x in doc['animations']]
res['animations'] = an(A, a) == an(B, b)
res['lod0 variant mappings'] = [p.get('extensions') for p in A['meshes'][0]['primitives']] == [p.get('extensions') for p in B['meshes'][0]['primitives']]
res['mesh extras'] = A['meshes'][0].get('extras') == B['meshes'][0].get('extras')
print(json.dumps(res)); print('ALL SAME' if all(res.values()) else 'DIFFERENT: ' + ', '.join(k for k, v in res.items() if not v))
