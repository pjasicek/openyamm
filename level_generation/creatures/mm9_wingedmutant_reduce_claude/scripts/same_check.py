#!/usr/bin/env python3
"""What must stay byte-identical between the installed and the reduced GLB: images, materials, textures, samplers, skins
(+ inverse binds), nodes, animations (every sampler's input/output bytes), the KHR_materials_variants list and every
LOD0 primitive's variant mapping. Usage: same_check.py <installed.glb> <reduced.glb>"""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
A, ab = read_glb(Path(sys.argv[1])); B, bb = read_glb(Path(sys.argv[2]))
h = lambda b: hashlib.sha256(b).hexdigest()[:12]
def img(doc, b, im):
    v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0); return h(b[o:o + v['byteLength']])
ok = True
def same(name, x, y):
    global ok
    r = x == y; ok &= r; print(f'{name:28s}', 'same' if r else 'DIFFERENT')
same('images', [img(A, ab, i) for i in A['images']], [img(B, bb, i) for i in B['images']])
for k in ('materials', 'textures', 'samplers', 'nodes', 'scenes'):
    same(k, A.get(k), B.get(k))
same('variants', A.get('extensions'), B.get('extensions'))
same('skin joints', [s['joints'] for s in A['skins']], [s['joints'] for s in B['skins']])
same('inverse binds', [h(accessor_bytes(A, ab, s['inverseBindMatrices'])) for s in A['skins']], [h(accessor_bytes(B, bb, s['inverseBindMatrices'])) for s in B['skins']])
anim = lambda d, b: [(a['name'], [(h(accessor_bytes(d, b, s['input'])), h(accessor_bytes(d, b, s['output'])), s.get('interpolation')) for s in a['samplers']], a['channels']) for a in d['animations']]
same('animations', anim(A, ab), anim(B, bb))
na = next(n for n in A['nodes'] if n.get('name') == 'Wmut'); nb = next(n for n in B['nodes'] if n.get('name') == 'Wmut')
same('LOD0 prim materials+variants', [(p['material'], p.get('extensions')) for p in A['meshes'][na['mesh']]['primitives']],
     [(p['material'], p.get('extensions')) for p in B['meshes'][nb['mesh']]['primitives']])
for d, n in ((A, 'installed'), (B, 'reduced')):
    lods = [d['meshes'][na['mesh']]] + [d['meshes'][i] for i in d['meshes'][na['mesh']]['extras']['openyamm_lods']]
    print(n, 'LOD tris', [sum(d['accessors'][p['indices']]['count'] // 3 for p in m['primitives']) for m in lods],
          'shadow', [sum(d['accessors'][p['indices']]['count'] // 3 for p in d['meshes'][i]['primitives']) for i in d['meshes'][na['mesh']]['extras'].get('openyamm_shadow_lods', [])],
          'variants on every prim', all('extensions' in p for m in d['meshes'] for p in m['primitives']))
print('ALL SAME' if ok else 'SOMETHING DIFFERS')
