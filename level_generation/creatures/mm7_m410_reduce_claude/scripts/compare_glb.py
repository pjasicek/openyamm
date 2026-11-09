#!/usr/bin/env python3
"""Structure of the reduced GLB against the source: node names and transforms, skins and inverse binds, materials
(with extras), images (bytes), textures, samplers, animations (sampler data bytes), variants and mesh extras; prints
triangles and attributes per mesh and any difference. Usage: compare_glb.py <source.glb> <reduced.glb>"""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
(A, a), (B, b) = read_glb(Path(sys.argv[1])), read_glb(Path(sys.argv[2]))
h = lambda d, x, i: hashlib.sha1(accessor_bytes(d, x, i)).hexdigest()
def img(d, x, im):
    v = d['bufferViews'][im['bufferView']]; s = v.get('byteOffset', 0); return hashlib.sha1(bytes(x[s:s + v['byteLength']])).hexdigest()
bad = []
chk = lambda name, p, q: bad.append(name) if p != q else None
chk('nodes', [{k: v for k, v in n.items() if k != 'mesh'} for n in A['nodes']], [{k: v for k, v in n.items() if k != 'mesh'} for n in B['nodes']])
chk('materials', A['materials'], B['materials']); chk('textures', A.get('textures'), B.get('textures'))
chk('samplers', A.get('samplers'), B.get('samplers')); chk('extensions', A.get('extensions'), B.get('extensions'))
chk('extensionsUsed', sorted(A.get('extensionsUsed', [])), sorted(B.get('extensionsUsed', [])))
chk('images', [(i.get('name'), img(A, a, i)) for i in A['images']], [(i.get('name'), img(B, b, i)) for i in B['images']])
chk('skins', [(s.get('name'), s['joints'], h(A, a, s['inverseBindMatrices'])) for s in A['skins']],
    [(s.get('name'), s['joints'], h(B, b, s['inverseBindMatrices'])) for s in B['skins']])
anim = lambda d, x: [(an['name'], an['channels'], [(h(d, x, s['input']), h(d, x, s['output']), s.get('interpolation')) for s in an['samplers']]) for an in d['animations']]
chk('animations', anim(A, a), anim(B, b))
chk('mesh names/extras', [(m['name'], m.get('extras')) for m in A['meshes']], [(m['name'], m.get('extras')) for m in B['meshes']])
for (ma, mb) in zip(A['meshes'], B['meshes']):
    for pa, pb in zip(ma['primitives'], mb['primitives']):
        chk(f"{ma['name']} material/variants", (pa.get('material'), pa.get('extensions')), (pb.get('material'), pb.get('extensions')))
        chk(f"{ma['name']} attributes", sorted(pa['attributes']), sorted(pb['attributes']))
    print(f"{ma['name']:20s} {sum(A['accessors'][p['indices']]['count'] for p in ma['primitives']) // 3:6d} -> "
          f"{sum(B['accessors'][p['indices']]['count'] for p in mb['primitives']) // 3:6d}  variants on all: "
          f"{all('KHR_materials_variants' in p.get('extensions', {}) for p in mb['primitives'])}")
print('SIZE', Path(sys.argv[1]).stat().st_size, '->', Path(sys.argv[2]).stat().st_size)
print('DIFFERENCES', bad or 'none')
