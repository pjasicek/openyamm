#!/usr/bin/env python3
"""Binding-relevant comparison of a reduced GLB with its source: node names and transforms, skin joints and inverse
bind matrices, materials (incl. extras: region ramps, specular), KHR_materials_variants per primitive, animations
(names, channels, sampler data bytes), images (bytes), mesh names and LOD/shadow extras, triangles per mesh.
Usage: compare_glb.py <source.glb> <reduced.glb>"""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
(a, ab), (b, bb) = (read_glb(Path(p)) for p in sys.argv[1:3])
h = lambda d, bn, i: hashlib.sha1(accessor_bytes(d, bn, i)).hexdigest()
ok = True


def check(name, x, y):
    global ok
    same = x == y; ok &= same; print(('SAME ' if same else 'DIFF ') + name + ('' if same else f': {str(x)[:200]} vs {str(y)[:200]}'))


check('nodes', [(n.get('name'), n.get('translation'), n.get('rotation'), n.get('scale'), n.get('children')) for n in a['nodes']],
      [(n.get('name'), n.get('translation'), n.get('rotation'), n.get('scale'), n.get('children')) for n in b['nodes']])
check('skins joints', [s['joints'] for s in a.get('skins', [])], [s['joints'] for s in b.get('skins', [])])
check('inverse bind', [h(a, ab, s['inverseBindMatrices']) for s in a.get('skins', [])], [h(b, bb, s['inverseBindMatrices']) for s in b.get('skins', [])])
check('materials', a['materials'], b['materials'])
check('variants ext', a.get('extensions'), b.get('extensions'))
check('extensionsUsed', a.get('extensionsUsed'), b.get('extensionsUsed'))
check('prim variant mappings', [[p.get('extensions') for p in m['primitives']] for m in a['meshes']],
      [[p.get('extensions') for p in m['primitives']] for m in b['meshes']])
check('mesh names', [m['name'] for m in a['meshes']], [m['name'] for m in b['meshes']])
check('mesh extras', [m.get('extras') for m in a['meshes']], [m.get('extras') for m in b['meshes']])
check('attributes', [[sorted(p['attributes']) for p in m['primitives']] for m in a['meshes']], [[sorted(p['attributes']) for p in m['primitives']] for m in b['meshes']])
anim = lambda d, bn: [(x['name'], [(c['target'].get('node'), c['target']['path']) for c in x['channels']],
                       [(h(d, bn, s['input']), h(d, bn, s['output']), s.get('interpolation')) for s in x['samplers']]) for x in d.get('animations', [])]
check('animations', anim(a, ab), anim(b, bb))
img = lambda d, bn: [(i.get('name'), i.get('mimeType'), hashlib.sha1(bytes(bn[d['bufferViews'][i['bufferView']].get('byteOffset', 0):][:d['bufferViews'][i['bufferView']]['byteLength']])).hexdigest()) for i in d.get('images', [])]
check('images', img(a, ab), img(b, bb))
check('textures/samplers', (a.get('textures'), a.get('samplers')), (b.get('textures'), b.get('samplers')))
check('scene', (a.get('scene'), a.get('scenes')), (b.get('scene'), b.get('scenes')))
tri = lambda d: {m['name']: sum(d['accessors'][p['indices']]['count'] // 3 for p in m['primitives']) for m in d['meshes']}
print('TRIS source', tri(a)); print('TRIS reduced', tri(b)); print('RESULT', 'identical apart from geometry' if ok else 'DIFFERENCES above')
