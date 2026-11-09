#!/usr/bin/env python3
"""Structure of the reduced export against the source: node names and order, skins, materials (with extras), images,
textures, animations (bytes of every sampler), extensions, mesh extras, and per primitive: attributes, triangle count,
KHR_materials_variants mappings. Usage: compare_structure.py <source.glb> <reduced.glb>"""
import json, sys, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
(a, ab), (b, bb) = read_glb(Path(sys.argv[1])), read_glb(Path(sys.argv[2]))
ok = True
def check(name, x, y):
    global ok
    same = x == y; ok &= same; print('SAME' if same else 'DIFF', name, '' if same else f'\n   {str(x)[:300]}\n   {str(y)[:300]}')
strip = lambda n: {k: v for k, v in n.items() if k != 'mesh'}
check('nodes', [strip(n) for n in a['nodes']], [strip(n) for n in b['nodes']])
check('skins joints', [s['joints'] for s in a['skins']], [s['joints'] for s in b['skins']])
check('materials', a['materials'], b['materials'])
check('textures', a['textures'], b['textures'])
check('images (names, bytes)', [(i.get('name'), hashlib.sha1(bytes(ab[a['bufferViews'][i['bufferView']].get('byteOffset', 0):][:a['bufferViews'][i['bufferView']]['byteLength']])).hexdigest()) for i in a['images']],
      [(i.get('name'), hashlib.sha1(bytes(bb[b['bufferViews'][i['bufferView']].get('byteOffset', 0):][:b['bufferViews'][i['bufferView']]['byteLength']])).hexdigest()) for i in b['images']])
check('extensions', (a.get('extensions'), a.get('extensionsUsed')), (b.get('extensions'), b.get('extensionsUsed')))
anim = lambda d, bin_: [(x['name'], [hashlib.sha1(accessor_bytes(d, bin_, s['input']) + accessor_bytes(d, bin_, s['output'])).hexdigest() for s in x['samplers']], [(c['target']['node'], c['target']['path']) for c in x['channels']]) for x in d['animations']]
check('animations (bytes)', anim(a, ab), anim(b, bb))
check('mesh names + extras', [(m['name'], m.get('extras')) for m in a['meshes']], [(m['name'], m.get('extras')) for m in b['meshes']])
for name, d in (('source', a), ('reduced', b)):
    print(name, [(m['name'], [(d['accessors'][p['indices']]['count'] // 3, sorted(p['attributes']), json.dumps(p.get('extensions'))) for p in m['primitives']]) for m in d['meshes']])
print('STRUCTURE', 'OK' if ok else 'DIFFERENCES')
