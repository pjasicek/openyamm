#!/usr/bin/env python3
"""Installed vs reduced GLB: effect meshes byte-identical (every accessor of Eyes and Flash), node names/transforms,
skins, animations (channel targets and sampler data), materials, variants and images unchanged.
Usage: compare_glb.py <installed.glb> <reduced.glb>"""
import sys, hashlib, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes
a, ab = read_glb(Path(sys.argv[1])); b, bb = read_glb(Path(sys.argv[2]))
def mesh_sig(d, raw, node):
    n = next(x for x in d['nodes'] if x.get('name') == node); m = d['meshes'][n['mesh']]
    return [(d['materials'][p['material']]['name'], json.dumps(p.get('extensions'), sort_keys=True), {k: hashlib.sha1(accessor_bytes(d, raw, i)).hexdigest() for k, i in p['attributes'].items()},
             hashlib.sha1(accessor_bytes(d, raw, p['indices'])).hexdigest()) for p in m['primitives']]
for node in ('Eyes', 'Flash'):
    print(node, 'byte-identical' if mesh_sig(a, ab, node) == mesh_sig(b, bb, node) else 'DIFFERENT')
strip = lambda n: {k: v for k, v in n.items() if k not in ('mesh',)}
print('nodes', 'same' if [strip(n) for n in a['nodes']] == [strip(n) for n in b['nodes']] else 'DIFFERENT')
def anim(d, raw):
    return [(x['name'], [(c['target'].get('node'), c['target']['path'], hashlib.sha1(accessor_bytes(d, raw, x['samplers'][c['sampler']]['input']) + accessor_bytes(d, raw, x['samplers'][c['sampler']]['output'])).hexdigest(), x['samplers'][c['sampler']].get('interpolation')) for c in x['channels']]) for x in d['animations']]
aa, ba = anim(a, ab), anim(b, bb)
print('animations', 'same' if aa == ba else 'DIFFERENT', [(x[0], len(x[1])) for x in ba])
if aa != ba:
    for (n1, c1), (n2, c2) in zip(aa, ba):
        diff = [(p, q) for p, q in zip(c1, c2) if p != q]
        print('  ', n1, len(c1), len(c2), 'differing channels', len(diff), [(a['nodes'][p[0]]['name'], p[1]) for p, q in diff[:6]])
print('materials', 'same' if a['materials'] == b['materials'] else 'DIFFERENT', 'variants', 'same' if a.get('extensions') == b.get('extensions') else 'DIFFERENT')
img = lambda d, raw: [hashlib.sha1(raw[d['bufferViews'][i['bufferView']].get('byteOffset', 0):][:d['bufferViews'][i['bufferView']]['byteLength']]).hexdigest() for i in d['images']]
print('images', 'same' if img(a, ab) == img(b, bb) else 'DIFFERENT')
print('skins', 'same' if [s['joints'] for s in a['skins']] == [s['joints'] for s in b['skins']] else 'DIFFERENT')
