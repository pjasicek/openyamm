#!/usr/bin/env python3
"""Review-viewer GLBs: LOD0 with the halberd in the hand (the runtime body has it as an attachment), one tier's images, the final clips of export/mm9_guard.glb by joint name. Writes review/viewer/guard_{a,b,c}.glb."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor'); sys.path.insert(0, '../claude_shared')
from glb_pose import Glb
import region_variants as RV
SETS = {'a': dict(Guard=('guard_a_final', 'guard_a_normal_1k', 'guard_a_metal_rough_1k'), GuardHead=('guard_heada_final', 'guard_heada_normal_1k', 'guard_heada_metal_rough_1k'), Halberd=('halberd_a_basecolor', 'halberd_a_normal', 'halberd_a_orm')),
        'b': dict(Guard=('guard_b_final', 'guard_b_normal_1k', 'guard_b_metal_rough_1k'), GuardHead=('guard_headc_final', 'guard_headc_normal_1k', 'guard_headc_metal_rough_1k'), Halberd=('halberd_a_basecolor', 'halberd_a_normal', 'halberd_a_orm')),
        'c': dict(Guard=('guard_c_final', 'guard_c_normal_1k', 'guard_c_metal_rough_1k'), GuardHead=('guard_headc_final', 'guard_headc_normal_1k', 'guard_headc_metal_rough_1k'), Halberd=('halberd_c_basecolor', 'halberd_c_normal', 'halberd_c_orm'))}
from PIL import Image
# three.js has no region ramps: the mantle's ramp is baked into the viewer's tier B colours by the shader's rule
Rp = json.load(open('textures/guard_b_ramp.json'))
bb = np.asarray(Image.open('textures/guard_b_final.png').convert('RGB'), np.float64) / 255
mk = np.asarray(Image.open('textures/guard_b_region_mask.png').getchannel('R').resize((bb.shape[1], bb.shape[0]), Image.BILINEAR), np.float64)[..., None] / 255
ln = RV.srgb_to_linear(bb); t_ = np.clip(((ln @ RV.LUMA) - Rp['range'][0]) / (Rp['range'][1] - Rp['range'][0]), 0, 1) * 15
i0 = np.minimum(t_.astype(int), 14); fr = (t_ - i0)[..., None]; cs = np.array(Rp['colors'])
rc = cs[i0] * (1 - fr) + cs[i0 + 1] * fr
out_l = ln * (1 - mk) + rc * mk
out = np.where(out_l <= 0.0031308, out_l * 12.92, 1.055 * np.power(out_l, 1 / 2.4) - 0.055)
Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save('work/guard_b_viewer.png')
src = Glb(Path('export/mm9_guard.glb'))
sn = [n.get('name') for n in src.json['nodes']]
for t, sets in SETS.items():
    g = Glb(Path('work/guard_final_clips.glb')); d = g.json
    dn = {n.get('name'): i for i, n in enumerate(d['nodes'])}
    anims = []
    for an in src.json['animations']:
        samplers, channels = [], []
        for ch in an['channels']:
            nm = sn[ch['target']['node']]
            if nm not in dn: continue
            sm = an['samplers'][ch['sampler']]
            ti = np.asarray(src.accessor(sm['input'])); va = np.asarray(src.accessor(sm['output']))
            ia = g.append_accessor(ti, 'SCALAR'); oa = g.append_accessor(va, 'VEC4' if va.shape[1] == 4 else 'VEC3')
            samplers.append(dict(input=ia, output=oa, interpolation=sm.get('interpolation', 'LINEAR')))
            channels.append(dict(sampler=len(samplers) - 1, target=dict(node=dn[nm], path=ch['target']['path'])))
        anims.append(dict(name=an['name'], samplers=samplers, channels=channels))
    d['animations'] = anims
    binary = bytearray(g.bin)
    for m in d['materials']:
        c, n, o = sets[m['name']]
        pairs = ((m['pbrMetallicRoughness']['baseColorTexture']['index'], c), (m['pbrMetallicRoughness']['metallicRoughnessTexture']['index'], o), (m['normalTexture']['index'], n))
        for ti, fn in pairs:
            data = Path('work/guard_b_viewer.png').read_bytes() if fn == 'guard_b_final' else Path('textures', fn + '.png').read_bytes()
            binary += b'\0' * (-len(binary) % 4)
            d['bufferViews'].append(dict(buffer=0, byteOffset=len(binary), byteLength=len(data)))
            binary += data
            d['images'].append(dict(name=fn, mimeType='image/png', bufferView=len(d['bufferViews']) - 1))
            d['textures'].append(dict(source=len(d['images']) - 1, sampler=d['textures'][ti].get('sampler', 0)))
            if ti == pairs[0][0]: m['pbrMetallicRoughness']['baseColorTexture']['index'] = len(d['textures']) - 1
            elif ti == pairs[1][0]: m['pbrMetallicRoughness']['metallicRoughnessTexture']['index'] = len(d['textures']) - 1
            else: m['normalTexture']['index'] = len(d['textures']) - 1
        m['pbrMetallicRoughness']['metallicFactor'] = 0.0
        m.setdefault('extensions', {})['KHR_materials_specular'] = dict(specularFactor=0.0 if m['name'] != 'Halberd' else 0.25)
    # the helmet's front plate, an attachment in the game: here a child of Bip01 Head
    pg = Glb(Path(f"export/mm9_guard_plate_{'a' if t == 'a' else 'c'}.glb")); pj = pg.json; pm = pj['meshes'][0]['primitives'][0]
    def put(a, ctype, typ):
        global binary
        data = np.ascontiguousarray(a).tobytes(); binary += b'\0' * (-len(binary) % 4)
        d['bufferViews'].append(dict(buffer=0, byteOffset=len(binary), byteLength=len(data))); binary += data
        ac = dict(bufferView=len(d['bufferViews']) - 1, componentType=ctype, count=len(a), type=typ)
        if typ == 'VEC3': ac['min'] = a.min(0).tolist(); ac['max'] = a.max(0).tolist()
        d['accessors'].append(ac); return len(d['accessors']) - 1
    pa = {k: put(np.asarray(pg.accessor(v), np.float32), 5126, {'POSITION': 'VEC3', 'NORMAL': 'VEC3', 'TEXCOORD_0': 'VEC2'}[k]) for k, v in pm['attributes'].items()}
    pi = put(np.asarray(pg.accessor(pm['indices']), np.uint32).ravel(), 5125, 'SCALAR')
    tex = []
    for im_ in pj['images']:
        v_ = pj['bufferViews'][im_['bufferView']]; data = bytes(pg.bin[v_.get('byteOffset', 0):v_.get('byteOffset', 0) + v_['byteLength']])
        binary += b'\0' * (-len(binary) % 4); d['bufferViews'].append(dict(buffer=0, byteOffset=len(binary), byteLength=len(data))); binary += data
        d['images'].append(dict(name=im_['name'], mimeType='image/png', bufferView=len(d['bufferViews']) - 1))
        d['textures'].append(dict(source=len(d['images']) - 1, sampler=0)); tex.append(len(d['textures']) - 1)
    mt = json.loads(json.dumps(pj['materials'][0]))
    mt['pbrMetallicRoughness']['baseColorTexture']['index'] = tex[0]; mt['pbrMetallicRoughness']['metallicRoughnessTexture']['index'] = tex[1]; mt['normalTexture']['index'] = tex[2]
    mt['pbrMetallicRoughness']['metallicFactor'] = 0.0; mt.setdefault('extensions', {})['KHR_materials_specular'] = dict(specularFactor=0.25)
    d['materials'].append(mt)
    d['meshes'].append(dict(name='Plate', primitives=[dict(attributes=pa, indices=pi, material=len(d['materials']) - 1)]))
    d['nodes'].append(dict(name='Plate', mesh=len(d['meshes']) - 1))
    d['nodes'][dn['Bip01 Head']].setdefault('children', []).append(len(d['nodes']) - 1)
    d.setdefault('extensionsUsed', [])
    if 'KHR_materials_specular' not in d['extensionsUsed']: d['extensionsUsed'].append('KHR_materials_specular')
    d2, b2 = RV._compact(d, bytes(binary))
    RV.write_glb(f'review/viewer/guard_{t}.glb', d2, b2)
    print('VIEWER', t, round(len(b2) / 1e6, 1), 'MB', len(d2['images']), 'images')
