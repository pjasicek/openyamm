#!/usr/bin/env python3
"""Review-viewer GLBs per tier (three.js has neither KHR_materials_variants nor region ramps): from a runtime GLB, LOD0 only (LOD and shadow
meshes dropped from their nodes), each primitive on its tier material with the ramps baked into the base colour by the engine rule
(mm7_m274_texpass_claude/scripts/viewer_variants.py). After mm6_gua_rebuild_claude/scripts/viewer_gua.py without the attachment.
Usage: viewer.py <runtime glb> <tag> -> review/viewer/<variant>_<tag>.glb"""
import copy, io, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
sys.path.insert(0, '../mm7_m274_texpass_claude/scripts')
from viewer_variants import bake, image  # noqa: E402
HERE = Path(__file__).resolve().parents[1]
body, tag = Path(sys.argv[1]), sys.argv[2]
bdoc, bbin = read_glb(body)
variants = [v['name'] for v in bdoc['extensions']['KHR_materials_variants']['variants']]
for vi, variant in enumerate(variants):
    doc = copy.deepcopy(bdoc); binary = bytearray(bbin)
    for node in doc['nodes']:
        if 'mesh' in node and any(k in doc['meshes'][node['mesh']].get('name', '') for k in ('LOD', 'Shadow')): node.pop('mesh')
    for m in doc['meshes']:
        for p in m['primitives']:
            ext = p.pop('extensions', {}).get('KHR_materials_variants')
            if ext: p['material'] = next((x['material'] for x in ext['mappings'] if vi in x['variants']), p.get('material'))
    doc.pop('extensions'); doc['extensionsUsed'] = [e for e in doc['extensionsUsed'] if e != 'KHR_materials_variants']
    for mi, mat in enumerate(doc['materials']):
        extras = mat.get('extras', {})
        used = any(p.get('material') == mi for nd in doc['nodes'] if 'mesh' in nd for p in doc['meshes'][nd['mesh']]['primitives'])
        if 'openyamm_region_ramps' not in extras or not used: continue
        tex = mat['pbrMetallicRoughness']['baseColorTexture']['index']
        out = bake(image(doc, binary, tex).convert('RGB'), image(doc, binary, extras['openyamm_region_mask']['index']), extras['openyamm_region_ramps'])
        buf = io.BytesIO(); Image.fromarray(out).save(buf, 'PNG'); binary.extend(b'\0' * (-len(binary) % 4))
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())}); binary.extend(buf.getvalue())
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'{variant}_baked'})
        doc['textures'].append({'source': len(doc['images']) - 1}); mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    doc['buffers'][0]['byteLength'] = len(binary)
    out = HERE / 'review/viewer' / f'{variant}_{tag}.glb'; write_glb(out, doc, bytes(binary)); print('VIEWER', out.name)
