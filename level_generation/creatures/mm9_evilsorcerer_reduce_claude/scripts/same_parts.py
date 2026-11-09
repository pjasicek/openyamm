#!/usr/bin/env python3
"""Everything but geometry must be byte for byte the installed file's: clips (sampler input/output bytes), images,
materials, textures, samplers, skins (joints, inverse binds), nodes (TRS, extras, sockets), document extensions
(KHR_materials_variants list). Also prints LOD0/LOD1-3 triangle counts and every primitive's variant mapping.
Usage: same_parts.py <installed.glb> <candidate.glb>"""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
(a, ab), (b, bb) = (read_glb(Path(p)) for p in sys.argv[1:3])
h = lambda x: hashlib.sha256(x).hexdigest()[:12]


def clips(doc, binary):
    return {an['name']: h(b''.join(accessor_bytes(doc, binary, s['input']) + accessor_bytes(doc, binary, s['output'])
                                    for s in an['samplers'])) + json.dumps(an['channels'], sort_keys=True)
            for an in doc.get('animations', [])}


def images(doc, binary):
    out = {}
    for im in doc.get('images', []):
        v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
        out[im.get('name')] = h(bytes(binary[o:o + v['byteLength']]))
    return out


def skins(doc, binary):
    return [(s['joints'], h(accessor_bytes(doc, binary, s['inverseBindMatrices']))) for s in doc['skins']]


ok = True
for label, fa, fb in (('clips', clips(a, ab), clips(b, bb)), ('images', images(a, ab), images(b, bb)),
                      ('materials', a['materials'], b['materials']), ('textures', a.get('textures'), b.get('textures')),
                      ('samplers', a.get('samplers'), b.get('samplers')), ('skins', skins(a, ab), skins(b, bb)),
                      ('nodes', [{k: v for k, v in n.items() if k != 'mesh'} for n in a['nodes']],
                       [{k: v for k, v in n.items() if k != 'mesh'} for n in b['nodes']]),
                      ('extensions', a.get('extensions'), b.get('extensions')), ('scenes', a.get('scenes'), b.get('scenes'))):
    same = json.dumps(fa, sort_keys=True) == json.dumps(fb, sort_keys=True); ok &= same
    print('SAME' if same else 'DIFF', label, len(fa) if fa else 0)


def tris(doc):
    node = next(n for n in doc['nodes'] if n.get('name') == 'Sorcerer'); m = doc['meshes'][node['mesh']]
    lods = [m] + [doc['meshes'][i] for i in m.get('extras', {}).get('openyamm_lods', [])]
    sh = [doc['meshes'][i] for i in m.get('extras', {}).get('openyamm_shadow_lods', [])]
    cnt = lambda mm: sum(doc['accessors'][p['indices']]['count'] // 3 for p in mm['primitives'])
    var = [sorted({str(p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings')) != 'None' for p in mm['primitives']}) for mm in lods + sh]
    return [cnt(x) for x in lods], [cnt(x) for x in sh], var


for label, doc in (('installed', a), ('candidate', b)):
    print(label, 'LODs', *tris(doc))
print('ALL SAME' if ok else 'SOMETHING DIFFERS')
