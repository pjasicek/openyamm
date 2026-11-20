#!/usr/bin/env python3
"""Everything but the mesh geometry is the installed file's: animation samplers (input/output bytes), skin joints and
inverse binds, node TRS and names, images, materials, variants. Usage: same_clips.py <installed.glb> <candidate.glb>"""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbio_monk as glbio  # noqa: E402
(a, ab), (b, bb) = glbio.read_glb(Path(sys.argv[1])), glbio.read_glb(Path(sys.argv[2]))
h = lambda d, B, i: hashlib.sha1(glbio.accessor_bytes(d, B, i)).hexdigest()
def views(d, B, i):
    v = d['bufferViews'][i]; o = v.get('byteOffset', 0); return hashlib.sha1(B[o:o + v['byteLength']]).hexdigest()
bad = []
anim = lambda d, B: [(x['name'], [(h(d, B, s['input']), h(d, B, s['output']), s.get('interpolation')) for s in x['samplers']],
                      [(c['target']['node'], c['target']['path'], c['sampler']) for c in x['channels']]) for x in d['animations']]
if anim(a, ab) != anim(b, bb): bad.append('animations')
skin = lambda d, B: [(s['joints'], h(d, B, s['inverseBindMatrices'])) for s in d['skins']]
if skin(a, ab) != skin(b, bb): bad.append('skins')
nodes = lambda d: [{k: v for k, v in n.items() if k != 'mesh'} for n in d['nodes']]
if nodes(a) != nodes(b): bad.append('nodes')
for k in ('materials', 'textures', 'samplers', 'extensions', 'extensionsUsed'):
    if a.get(k) != b.get(k): bad.append(k)
if [views(a, ab, i['bufferView']) for i in a['images']] != [views(b, bb, i['bufferView']) for i in b['images']]: bad.append('images')
print('SAME CLIPS/SKIN/NODES/MATERIALS/IMAGES' if not bad else f'DIFFERENT: {bad}', '|', len(a['animations']), 'clips,', len(a['images']), 'images')
