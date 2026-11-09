#!/usr/bin/env python3
"""Crest attachments for actors.yml: work/crest_raw/*.glb (rest space) -> export/hes_glassback_crest_<size>_<bone>.glb.
1. tools/link_static_model_lods.py links Crest_*_LOD1..3 into the base mesh's openyamm_lods;
2. positions and normals go into the carrying joint's space with its inverse bind matrix from export/hes_glassback.glb
   (the engine draws an attachment with the joint node's world matrix);
3. materials: Glass (metallic 0, specular 1, its roughness map; glossy black glass) with a region mask = the painted
   cracks (textures/hgb_glass_cracks.png) and per-tier crack ramps; Glow (KHR_materials_unlit, black base, emissive
   tier colour: the glow strips and root seams bloom once creature/attachment bloom is used) with one material per tier.
   Variants hgb_a/b/c, the body's names, so an attachment without its own skin follows the carrier's tier.
Writes export/crest_info.json (triangles per level)."""
import copy, json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as R

GLOW = {'hgb_a': [0.55, 0.95, 0.88], 'hgb_b': [0.12, 1.0, 0.78], 'hgb_c': [0.82, 1.0, 0.86]}
CRACK = {'hgb_a': [(20, 60, 56), (95, 190, 178), (165, 242, 228)], 'hgb_b': [(8, 62, 52), (30, 200, 158), (75, 255, 210)],
         'hgb_c': [(30, 70, 42), (150, 235, 165), (225, 255, 232)]}
SIZE = {'vec3': 3}


def ramp(stops):
    s = R.srgb_to_linear(np.array(stops, np.float64) / 255); t = np.linspace(0, 1, 16)
    return np.stack([np.interp(t, [0, 0.5, 1], s[:, c]) for c in range(3)], 1).round(5).tolist()


def accessor(doc, binary, i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    assert a['componentType'] == 5126 and v.get('byteStride', 4 * n) == 4 * n
    return off, np.frombuffer(bytes(binary[off:off + a['count'] * 4 * n]), np.float32).reshape(a['count'], n).copy()


def joint_ibm(body_path, bone):
    doc, binary = R.read_glb(body_path)
    skin = doc['skins'][0]
    names = [doc['nodes'][j]['name'] for j in skin['joints']]
    _, ibm = accessor(doc, binary, skin['inverseBindMatrices'])
    return ibm[[n.lower() for n in names].index(bone.lower())].reshape(4, 4).T          # column-major in glTF


def main():
    body = ROOT / 'export/hes_glassback.glb'
    mask_png = ROOT / 'textures/hgb_glass_mask.png'
    cracks = np.asarray(Image.open(ROOT / 'textures/hgb_glass_cracks_256.png'), np.float32) / 255
    Image.fromarray(np.stack([(cracks * 255).astype(np.uint8)] + [np.zeros_like(cracks, np.uint8)] * 3, -1),
                        'RGBA').save(mask_png)
    lum = R.luminance(np.asarray(Image.open(ROOT / 'textures/hgb_glass_basecolor_512.png').convert('RGB').resize(cracks.shape[::-1], Image.LANCZOS), np.float64) / 255)
    core = cracks > 0.6
    lo, hi = float(np.percentile(lum[core], 2)), float(np.percentile(lum[core], 99))
    cfg = {'variants': list(GLOW), 'materials': [{'base': 'Glass', 'prefix': 'Glass', 'mask': mask_png.name,
           'ramps': {t: [{'range': [round(lo, 4), round(hi, 4)], 'colors': ramp(CRACK[t])}] for t in GLOW}}]}
    cfg_path = ROOT / 'textures/hgb_crest_ramps.json'
    json.dump(cfg, open(cfg_path, 'w'), indent=1)
    info = {}
    for raw in sorted((ROOT / 'work/crest_raw').glob('*.glb')):
        size, bone = raw.stem.split('_')[3], raw.stem.split('_')[4]
        out = ROOT / 'export' / raw.name
        tmp = ROOT / 'work/crest_raw' / (raw.stem + '.linked.glb')
        subprocess.run([sys.executable, str(REPO / 'tools/link_static_model_lods.py'), str(raw), str(tmp)], check=True,
                       stdout=subprocess.DEVNULL)
        doc, binary = R.read_glb(tmp)
        binary = bytearray(binary)
        M = joint_ibm(body, bone)
        done = set()
        for mesh in doc['meshes']:
            for pr in mesh['primitives']:
                for key in ('POSITION', 'NORMAL'):
                    i = pr['attributes'][key]
                    if i in done:
                        continue
                    done.add(i)
                    off, a = accessor(doc, binary, i)
                    if key == 'POSITION':
                        a = (np.c_[a, np.ones(len(a))] @ M.T)[:, :3]
                        doc['accessors'][i]['min'] = a.min(0).tolist(); doc['accessors'][i]['max'] = a.max(0).tolist()
                    else:
                        a = a @ M[:3, :3].T
                        a /= np.linalg.norm(a, axis=1, keepdims=True)
                    binary[off:off + a.size * 4] = a.astype(np.float32).tobytes()
        for m in doc['materials']:
            if m['name'] == 'Glass':
                m['pbrMetallicRoughness']['metallicFactor'] = 0.0
                m.setdefault('extras', {})['openyamm_specular'] = 1.0
                m.pop('emissiveFactor', None)
            elif m['name'] == 'Glow':
                m['pbrMetallicRoughness'] = {'baseColorFactor': [0, 0, 0, 1], 'metallicFactor': 0.0, 'roughnessFactor': 1.0}
                m['emissiveFactor'] = GLOW['hgb_b']
                m['extensions'] = {'KHR_materials_unlit': {}}
                m.pop('emissiveTexture', None)
                m['extras'] = {'openyamm_specular': 0.0}
        doc.setdefault('extensionsUsed', [])
        if 'KHR_materials_unlit' not in doc['extensionsUsed']:
            doc['extensionsUsed'].append('KHR_materials_unlit')
        R.write_glb(tmp, doc, binary)
        R.apply_variants(str(tmp), str(out), str(cfg_path))
        # per-tier glow materials (emission differs, so not a ramp)
        doc, binary = R.read_glb(out)
        binary = bytearray(binary)
        glow_i = next(i for i, m in enumerate(doc['materials']) if m['name'] == 'Glow')
        variants = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']]
        per = {}
        for t in variants:
            m = copy.deepcopy(doc['materials'][glow_i]); m['name'] = f'Glow_{t}'; m['emissiveFactor'] = GLOW[t]
            doc['materials'].append(m); per[t] = len(doc['materials']) - 1
        for mesh in doc['meshes']:
            for pr in mesh['primitives']:
                if pr.get('material') == glow_i:
                    pr['material'] = per['hgb_b']
                    pr.setdefault('extensions', {})['KHR_materials_variants'] = {'mappings': [
                        {'material': per[t], 'variants': [variants.index(t)]} for t in variants]}
        # the original Glow is now unreferenced: keep it (index stability is not needed, but harmless)
        R.write_glb(out, doc, binary)
        tris = []
        base = next(m for m in doc['meshes'] if 'openyamm_lods' in m.get('extras', {})) if any(
            'openyamm_lods' in m.get('extras', {}) for m in doc['meshes']) else doc['meshes'][0]
        chain = [doc['meshes'].index(base)] + base.get('extras', {}).get('openyamm_lods', [])
        for mi in chain:
            tris.append(sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][mi]['primitives']))
        bone = next(n['name'] for n in R.read_glb(body)[0]['nodes'] if n.get('name', '').lower() == bone)
        info[out.name] = {'size': size, 'node': bone, 'triangles_per_lod': tris}
        print('CREST', out.name, bone, tris)
        tmp.unlink()
    json.dump(info, open(ROOT / 'export/crest_info.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
