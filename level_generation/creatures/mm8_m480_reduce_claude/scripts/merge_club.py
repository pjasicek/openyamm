#!/usr/bin/env python3
"""Review-only GLB: the Troll Peasant body with its rigid club merged under the Club bone node (as the engine
attaches mm8_m480_club.glb to node Club), so viewers and close-ups show the grip. Club meshes, materials, textures, images and
variant mappings are appended; only the club's LOD0 is attached. Usage: merge_club.py <body.glb> <club.glb> <out.glb>"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

body, club, out = (Path(a) for a in sys.argv[1:4])
doc, binary = read_glb(body); binary = bytearray(binary)
cdoc, cbin = read_glb(club)
off = len(binary) + (-len(binary) % 4); binary.extend(b'\0' * (-len(binary) % 4)); binary.extend(cbin)
vbase, abase, ibase, tbase, mbase, sbase = (len(doc.get(k, [])) for k in
                                            ('bufferViews', 'accessors', 'images', 'textures', 'materials', 'samplers'))
for v in cdoc['bufferViews']:
    doc['bufferViews'].append(dict(v, buffer=0, byteOffset=v.get('byteOffset', 0) + off))
for a in cdoc['accessors']:
    doc['accessors'].append(dict(a, bufferView=a['bufferView'] + vbase))
for im in cdoc.get('images', []):
    doc.setdefault('images', []).append(dict(im, bufferView=im['bufferView'] + vbase))
for s in cdoc.get('samplers', []):
    doc.setdefault('samplers', []).append(s)
for t in cdoc.get('textures', []):
    t = dict(t, source=t['source'] + ibase)
    if 'sampler' in t:
        t['sampler'] += sbase
    doc.setdefault('textures', []).append(t)


def retex(o):
    if isinstance(o, dict):
        return {k: (v + tbase if k == 'index' and isinstance(v, int) else retex(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [retex(x) for x in o]
    return o


for m in cdoc['materials']:
    doc['materials'].append(retex(copy.deepcopy(m)))
cvariants = [v['name'] for v in cdoc.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])]
bvariants = [v['name'] for v in doc.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])]
mesh = copy.deepcopy(cdoc['meshes'][cdoc['nodes'][0]['mesh']]); mesh.pop('extras', None); mesh['name'] = 'ClubReview'
for p in mesh['primitives']:
    p['attributes'] = {k: v + abase for k, v in p['attributes'].items()}; p['indices'] += abase; p['material'] += mbase
    ext = p.get('extensions', {}).get('KHR_materials_variants')
    if ext:
        for mp in ext['mappings']:
            mp['material'] += mbase
            mp['variants'] = [bvariants.index(cvariants[i]) for i in mp['variants']]
doc['meshes'].append(mesh)
doc['nodes'].append({'name': 'ClubReview', 'mesh': len(doc['meshes']) - 1})
bone = next(n for n in doc['nodes'] if n.get('name') == 'Club')
bone.setdefault('children', []).append(len(doc['nodes']) - 1)
write_glb(out, doc, bytes(binary)); print('MERGED club into', out.name)
