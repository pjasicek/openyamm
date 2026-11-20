#!/usr/bin/env python3
"""Validate a linked rock GLB against the static decoration contract: one material and one mesh node, three linked
LODs within the rocks.json targets (LOD0 <= 1500), POSITION/NORMAL/TEXCOORD_0/COLOR_0 on every primitive, base at
y = 0, opaque PNG base / metal-roughness / normal textures. Usage: validate_glb.py file.glb [rock]"""
import json, os, struct, sys
import scans

path = sys.argv[1]
rock = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(path).split('_')[0]
budget = json.load(open(os.path.join(scans.HERE, 'rocks.json')))[rock]['targets']
raw = open(path, 'rb').read(); n = struct.unpack_from('<I', raw, 12)[0]; d = json.loads(raw[20:20 + n])
problems = []
mats, meshes, nodes = d.get('materials', []), d['meshes'], d['nodes']
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
if counts[0] > 1500: problems.append('LOD0 over 1500')
for m in [base] + [meshes[i] for i in lods]:
    for p in m['primitives']:
        if p.get('material') != 0: problems.append('primitive material')
        for attr in ('POSITION', 'NORMAL', 'TEXCOORD_0', 'COLOR_0'):
            if attr not in p['attributes']: problems.append(f'missing {attr}')
        pos = d['accessors'][p['attributes']['POSITION']]
        if abs(pos['min'][1]) > 0.02: problems.append(f'base y min {pos["min"][1]:.4f}')
m = mats[0]; pbr = m.get('pbrMetallicRoughness', {})
for k, t in {'base': pbr.get('baseColorTexture'), 'mr': pbr.get('metallicRoughnessTexture'),
             'normal': m.get('normalTexture')}.items():
    if t is None: problems.append(f'no {k} texture')
imgs = [(i.get('mimeType'), d['bufferViews'][i['bufferView']]['byteLength']) for i in d.get('images', [])]
if any(mt != 'image/png' for mt, _ in imgs): problems.append('non-PNG image')
if m.get('alphaMode', 'OPAQUE') != 'OPAQUE': problems.append('alpha')
pos0 = d['accessors'][base['primitives'][0]['attributes']['POSITION']]
print('VALID' if not problems else 'INVALID', os.path.basename(path), 'tris', counts, 'size', len(raw),
      'bounds', [round(v, 3) for v in pos0['min']], [round(v, 3) for v in pos0['max']], problems)
