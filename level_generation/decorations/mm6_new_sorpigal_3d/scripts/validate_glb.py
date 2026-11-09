#!/usr/bin/env python3
"""Validate an installed static decoration GLB against the asset contract. Usage: validate_glb.py file.glb b0 b1 b2 b3"""
import json, struct, sys
path, *budget = sys.argv[1:]; budget = [int(b) for b in budget]
raw = open(path, 'rb').read(); n = struct.unpack_from('<I', raw, 12)[0]; d = json.loads(raw[20:20 + n])
problems = []
mats = d.get('materials', []); meshes = d['meshes']; nodes = d['nodes']
if len(mats) != 1: problems.append(f'{len(mats)} materials')
if d.get('skins') or d.get('animations'): problems.append('skins/animations present')
mesh_nodes = [x for x in nodes if 'mesh' in x]
if len(mesh_nodes) != 1: problems.append(f'{len(mesh_nodes)} mesh nodes')
base = meshes[mesh_nodes[0]['mesh']]; lods = base.get('extras', {}).get('openyamm_lods', [])
if len(lods) != 3: problems.append(f'openyamm_lods {lods}')
tri = lambda m: sum(d['accessors'][p['indices']]['count'] // 3 for p in m['primitives'])
counts = [tri(base)] + [tri(meshes[i]) for i in lods]
for c, b in zip(counts, budget):
    if c > b: problems.append(f'{c} tris over {b}')
for m in [base] + [meshes[i] for i in lods]:
    for p in m['primitives']:
        if p.get('material') != 0: problems.append('primitive material')
        if 'TEXCOORD_0' not in p['attributes'] or 'NORMAL' not in p['attributes']: problems.append('missing attributes')
        pos = d['accessors'][p['attributes']['POSITION']]
        if abs(pos['min'][1]) > 0.02: problems.append(f'base y min {pos["min"][1]:.4f}')
m = mats[0]; pbr = m.get('pbrMetallicRoughness', {})
tex = {'base': pbr.get('baseColorTexture'), 'mr': pbr.get('metallicRoughnessTexture'), 'normal': m.get('normalTexture')}
for k, t in tex.items():
    if t is None: problems.append(f'no {k} texture')
imgs = [(i.get('mimeType'), d['bufferViews'][i['bufferView']]['byteLength']) for i in d.get('images', [])]
if any(mt != 'image/png' for mt, _ in imgs): problems.append('non-PNG image')
if m.get('alphaMode', 'OPAQUE') != 'OPAQUE': problems.append('alpha')
pos0 = d['accessors'][base['primitives'][0]['attributes']['POSITION']]
print('VALID' if not problems else 'INVALID', path, 'tris', counts, 'nodes', len(nodes), 'images', imgs,
      'bounds', [round(v, 3) for v in pos0['min']], [round(v, 3) for v in pos0['max']], 'size', len(raw), problems)
