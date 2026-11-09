#!/usr/bin/env python3
"""Installed Banshee GLB + a rebuilt candidate (same chain, reduced LOD0) -> the installed GLB with only its meshes
replaced. Materials (by name), images, textures, samplers, variants list, skin, nodes and clips stay the installed file's
bytes; the script first reports whether the candidate's own copies of them differ (they should not, except the floor fix
of Death/Dead, which reads the lowest point of the mesh). The untouched primitives (head, neck, hair: KEEP) are taken from the
installed file on every LOD, so Blender's LOD decimation (not bit-reproducible: a rebuild moved ~1 % of a LOD head's vertices)
cannot change a face anywhere. Usage: splice.py installed.glb candidate.glb out.glb"""
import copy, hashlib, json, sys
import numpy as np
import glbpack as G

I, ib = G.read(sys.argv[1]); C, cb = G.read(sys.argv[2])
h = lambda doc, b, i: hashlib.sha1(bytes(G.raw_rows(doc, b, i))).hexdigest()
# report differences outside the meshes
inames = [m['name'] for m in I['materials']]; cnames = [m['name'] for m in C['materials']]
assert len(set(inames)) == len(inames) and set(cnames) <= set(inames), 'material names'
diff = []
for m in C['materials']:
    a = json.dumps(m, sort_keys=True); b = json.dumps(I['materials'][inames.index(m['name'])], sort_keys=True)
    if a != b:
        diff.append('material ' + m['name'])
img = lambda doc, b, im: hashlib.sha1(bytes(b[doc['bufferViews'][im['bufferView']].get('byteOffset', 0):][:doc['bufferViews'][im['bufferView']]['byteLength']])).hexdigest()
if [img(I, ib, x) for x in I['images']] != [img(C, cb, x) for x in C['images']]:
    diff.append('images')
for key in ('textures', 'samplers', 'extensionsUsed', 'scenes'):
    if I.get(key) != C.get(key):
        diff.append(key)
if I.get('extensions') != C.get('extensions'):
    diff.append('extensions (variants list)')
strip = lambda n: {k: v for k, v in n.items() if k != 'mesh'}
if [strip(n) for n in I['nodes']] != [strip(n) for n in C['nodes']]:
    diff.append('nodes')
if h(I, ib, I['skins'][0]['inverseBindMatrices']) != h(C, cb, C['skins'][0]['inverseBindMatrices']) or \
        I['skins'][0]['joints'] != C['skins'][0]['joints']:
    diff.append('skin')
anim_diff = []
for a1, a2 in zip(I['animations'], C['animations']):
    for s1, s2 in zip(a1['samplers'], a2['samplers']):
        if h(I, ib, s1['input']) != h(C, cb, s2['input']) or h(I, ib, s1['output']) != h(C, cb, s2['output']):
            x = G.acc(I, bytes(ib), s1['output']); y = G.acc(C, bytes(cb), s2['output'])
            anim_diff.append((a1['name'], float(np.abs(x - y).max()) if x.shape == y.shape else 'shape'))
            break
print('OUTSIDE MESHES differ:', diff or 'nothing', '| clips differing (max abs):', anim_diff or 'none')
# replace the meshes
doc = copy.deepcopy(I); binary = bytearray(ib)
meshes = copy.deepcopy(C['meshes'])
for m in meshes:
    for p in m['primitives']:
        p['attributes'] = {k: G.append(doc, binary, C['accessors'][v], G.raw_rows(C, cb, v)) for k, v in p['attributes'].items()}
        for k, v in p['attributes'].items():
            G.set_minmax(doc, binary, v)
        p['indices'] = G.append(doc, binary, C['accessors'][p['indices']], G.raw_rows(C, cb, p['indices']))
        p['material'] = inames.index(cnames[p['material']])
        for mp in p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
            mp['material'] = inames.index(cnames[mp['material']])
KEEP = ('BansheeHead', 'BansheeNeck', 'BansheeHairL', 'BansheeHairR')
for m, mi in zip(meshes, I['meshes']):
    assert m['name'] == mi['name'] and len(m['primitives']) == len(mi['primitives'])
    for k, (p, pi) in enumerate(zip(m['primitives'], mi['primitives'])):
        base = inames[pi['material']].rsplit('_', 1)[0]
        assert inames[p['material']].rsplit('_', 1)[0] == base
        if base in KEEP:
            m['primitives'][k] = copy.deepcopy(pi)
doc['meshes'] = meshes
for n, cn in zip(doc['nodes'], C['nodes']):
    if 'mesh' in cn:
        n['mesh'] = cn['mesh']
doc, binary = G.compact(doc, binary)
G.write(sys.argv[3], doc, binary)
tris = [sum(doc['accessors'][p['indices']]['count'] // 3 for p in m['primitives']) for m in doc['meshes']]
print('SPLICED meshes', [m['name'] for m in doc['meshes']], 'tris', tris)
