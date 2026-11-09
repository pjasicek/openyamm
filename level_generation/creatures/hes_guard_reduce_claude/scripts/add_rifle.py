#!/usr/bin/env python3
"""Review copies with the rifle: the rifle and glow primitives of the source project's portable LOD0
(../hes_guard_claude/export/hes_guard_lod0.glb: skinned rigidly to the Rifle / RifleGlow bones, the same rig) are
appended to the full-detail mesh of a review GLB (viewer tiers from viewer_tiers.py), with their materials and
textures; joints are remapped by name and the inverse bind matrices checked. The runtime export keeps the rifle as
the separate attachments (export/hes_guard_rifle*.glb, unchanged). Usage: add_rifle.py <in.glb> <out.glb> [lod0.glb]"""
import copy, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402
src, out = Path(sys.argv[1]), Path(sys.argv[2])
lod0 = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(__file__).resolve().parents[2] / 'hes_guard_claude/export/hes_guard_lod0.glb'
doc, binary = read_glb(src); binary = bytearray(binary)
rd, rb = read_glb(lod0)
node = next(n for n in doc['nodes'] if 'mesh' in n and 'skin' in n)
rnode = next(n for n in rd['nodes'] if 'mesh' in n and 'skin' in n)
names = [doc['nodes'][i]['name'] for i in doc['skins'][node['skin']]['joints']]
rnames = [rd['nodes'][i]['name'] for i in rd['skins'][rnode['skin']]['joints']]
remap = [names.index(n) for n in rnames]
bind = list(struct.iter_unpack('<16f', accessor_bytes(doc, binary, doc['skins'][node['skin']]['inverseBindMatrices'])))
rbind = list(struct.iter_unpack('<16f', accessor_bytes(rd, rb, rd['skins'][rnode['skin']]['inverseBindMatrices'])))
for i, m in zip(remap, rbind):
    assert all(abs(a - b) < 1e-4 for a, b in zip(bind[i], m)), f'bind of {names[i]} differs'
for prim in rd['meshes'][rnode['mesh']]['primitives']:
    mat = rd['materials'][prim['material']]
    if not mat['name'].startswith('Rifle'):
        continue
    m = copy.deepcopy(mat); m.pop('extras', None)
    # textures of the material: copy image bytes and texture entries
    def tex(info):
        t = rd['textures'][info['index']]; im = rd['images'][t['source']]; bv = rd['bufferViews'][im['bufferView']]
        data = bytes(rb[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])
        binary.extend(b'\0' * (-len(binary) % 4)); doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
        binary.extend(data); doc.setdefault('images', []).append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': im.get('mimeType', 'image/png')})
        doc.setdefault('textures', []).append({'source': len(doc['images']) - 1, **({'sampler': 0} if doc.get('samplers') else {})})
        info = dict(info); info['index'] = len(doc['textures']) - 1; return info
    pbr = m.get('pbrMetallicRoughness', {})
    for k in ('baseColorTexture', 'metallicRoughnessTexture'):
        if k in pbr:
            pbr[k] = tex(pbr[k])
    for k in ('normalTexture', 'occlusionTexture', 'emissiveTexture'):
        if k in m:
            m[k] = tex(m[k])
    doc['materials'].append(m)
    attrs = {}
    for sem, idx in prim['attributes'].items():
        acc = rd['accessors'][idx]; packed = accessor_bytes(rd, rb, idx)
        if sem.startswith('JOINTS_'):
            code = {5121: 'B', 5123: 'H'}[acc['componentType']]
            packed = struct.pack('<' + code * (len(packed) // struct.calcsize(code)),
                                 *(remap[v[0]] for v in struct.iter_unpack('<' + code, packed)))
        attrs[sem] = append_accessor(doc, binary, acc, packed)
    p = {'attributes': attrs, 'indices': append_accessor(doc, binary, rd['accessors'][prim['indices']], accessor_bytes(rd, rb, prim['indices'])),
         'material': len(doc['materials']) - 1, 'mode': prim.get('mode', 4)}
    doc['meshes'][node['mesh']]['primitives'].append(p)
    print('RIFLE added', mat['name'], rd['accessors'][prim['indices']]['count'] // 3, 'tris')
write_glb(out, doc, bytes(binary))
