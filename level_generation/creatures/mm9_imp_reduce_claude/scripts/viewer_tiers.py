#!/usr/bin/env python3
"""Review-viewer GLBs for the Imp reduction (after ../mm9_imp_claude/scripts/viewer_tiers.py): three.js has no region
ramps, so each tier's ramps are baked into its base colours with the engine rule (claude_shared/tier_textures.apply). Unlike the
creature's script, everything is read from the GLB itself: each material's base colour image, its region mask and its
openyamm_region_ramps extras; a material without ramps (ImpHead_C, the Yeti's own head image) keeps its image.
Imp (imp-reduce-20261104): the runtime attachments are added as children of their joints the way the game attaches them
(mm9_guard_reduce_claude/scripts/viewer_tiers.py): the trident on Yweaponbase (every tier), the shin wraps on Xwrap L/R (B), the
tongue on Xtongue (C), LOD0 from the installed attachment GLBs (unchanged by the reduction). The result goes straight to
review/viewer/<prefix>_{a,b,c}.glb. Usage: viewer_tiers.py <glb> <prefix>"""
import copy
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT  # noqa: E402
import region_variants as RV  # noqa: E402
sys.path.insert(0, str(HERE / 'scripts'))
import glbpack as G  # noqa: E402
ATTS = HERE.parents[2] / 'assets_source/worlds/mm9/models'
ATT = {'imp_a': [('trident', 'Yweaponbase')], 'imp_b': [('trident', 'Yweaponbase'), ('wrapl', 'Xwrap L'), ('wrapr', 'Xwrap R')],
       'imp_c': [('trident', 'Yweaponbase'), ('tongue', 'Xtongue')]}
GLB, PREFIX = Path(sys.argv[1]), sys.argv[2]
OUT = HERE / 'work'
doc0, bin0 = RV.read_glb(GLB)


def image(doc, binary, tex_index):
    im = doc['images'][doc['textures'][tex_index]['source']]; v = doc['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0); return Image.open(io.BytesIO(bytes(binary[o:o + v['byteLength']])))


def add_bytes(doc, binary, data):
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary += data
    return len(doc['bufferViews']) - 1


def attach(doc, binary, path, joint):
    ad, ab = G.read(path); ab = bytes(ab)
    am = ad['meshes'][ad['nodes'][0]['mesh']]; pr = am['primitives'][0]
    att = {}
    for sem, i in pr['attributes'].items():
        a = ad['accessors'][i]
        att[sem] = G.append(doc, binary, a, G.raw_rows(ad, ab, i)); G.set_minmax(doc, binary, att[sem])
    idx = G.append(doc, binary, ad['accessors'][pr['indices']], G.raw_rows(ad, ab, pr['indices']))
    mat = copy.deepcopy(ad['materials'][pr['material']])
    tmap = {}

    def tex(i):
        if i not in tmap:
            src = ad['textures'][i]['source']; im = ad['images'][src]; v = ad['bufferViews'][im['bufferView']]
            o = v.get('byteOffset', 0); bv = add_bytes(doc, binary, ab[o:o + v['byteLength']])
            doc['images'].append({'name': im.get('name', 'att'), 'mimeType': im.get('mimeType', 'image/png'), 'bufferView': bv})
            doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': 0}); tmap[i] = len(doc['textures']) - 1
        return tmap[i]
    pbr = mat.get('pbrMetallicRoughness', {})
    for k in ('baseColorTexture', 'metallicRoughnessTexture'):
        if k in pbr: pbr[k]['index'] = tex(pbr[k]['index'])
    for k in ('normalTexture', 'occlusionTexture', 'emissiveTexture'):
        if k in mat: mat[k]['index'] = tex(mat[k]['index'])
    mat.pop('extensions', None); mat.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.25}
    doc['materials'].append(mat)
    doc['meshes'].append({'name': Path(path).stem, 'primitives': [{'attributes': att, 'indices': idx, 'material': len(doc['materials']) - 1}]})
    doc['nodes'].append({'name': Path(path).stem, 'mesh': len(doc['meshes']) - 1})
    jn = next(i for i, n in enumerate(doc['nodes']) if n.get('name') == joint)
    doc['nodes'][jn].setdefault('children', []).append(len(doc['nodes']) - 1)



baked = {}
for m in doc0['materials']:
    ex = m.get('extras', {})
    if 'openyamm_region_ramps' not in ex:
        continue
    base = np.asarray(image(doc0, bin0, m['pbrMetallicRoughness']['baseColorTexture']['index']).convert('RGB'), np.float64) / 255
    size = (base.shape[1], base.shape[0])
    bands = image(doc0, bin0, ex['openyamm_region_mask']['index']).convert('RGBA').split()
    mask = np.stack([np.asarray(b if b.size == size else b.resize(size, Image.BILINEAR), np.float64) / 255 for b in bands], -1)
    img = Image.fromarray((np.clip(TT.apply(base, mask, ex['openyamm_region_ramps']), 0, 1) * 255).astype(np.uint8))
    buf = io.BytesIO(); img.save(buf, 'PNG'); baked[m['name']] = buf.getvalue(); print('baked', m['name'])
vnames = [v['name'] for v in doc0['extensions']['KHR_materials_variants']['variants']]
for idx, variant in enumerate(vnames):
    doc, binary = RV.read_glb(GLB); binary = bytearray(binary)
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            for mp in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                if idx in mp['variants']:
                    prim['material'] = mp['material']
            prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if not prim.get('extensions'):
                prim.pop('extensions', None)
    for mat in doc['materials']:
        data = baked.get(mat['name'])
        if data is not None:
            binary.extend(b'\0' * (-len(binary) % 4))
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
            binary.extend(data)
            doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f"{mat['name']}_baked"})
            doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)})
            mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
        mat.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
    if not doc.get('samplers'):
        doc['samplers'] = [{}]
    for name, joint in ATT[variant]:
        attach(doc, binary, ATTS / f'mm9_imp_{name}.glb', joint)
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants'] + ['KHR_materials_specular']
    d2, b2 = RV._compact(doc, bytes(binary))
    out = HERE / 'review' / 'viewer' / f'{PREFIX}_{variant[-1]}.glb'; out.parent.mkdir(parents=True, exist_ok=True)
    RV.write_glb(out, d2, b2)
    print('VIEWER', out.name, round(len(b2) / 1e6, 1), 'MB', len(d2['images']), 'images')
