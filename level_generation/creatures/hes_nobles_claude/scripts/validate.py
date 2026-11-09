#!/usr/bin/env python3
"""Pre-stage validation of the Nobles' exports against integration/actors.yml, mirroring hesper_stage/stage.py's model
rules (LOD/shadow chains, specular masks, burn maps >= 4 px on every skinned variant material) plus: every bound clip and
script clip exists in the model, every socket and attachment node is a joint, every attachment file exists, and each row's
live loadout (body LOD0 + its attachments) is within the 15k-triangle ceiling. Writes review/validation.json. Args: none"""
import json, struct, sys
from pathlib import Path
import yaml
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parents[2] / 'level_generation/projects/hesper_stage'))


def gltf(path):
    data = path.read_bytes(); n = struct.unpack_from('<I', data, 12)[0]
    return json.loads(data[20:20 + n]), data, n


def tris(g, mi):
    return sum(g['accessors'][p['indices']]['count'] // 3 for p in g['meshes'][mi]['primitives'])


rows = yaml.safe_load((HERE / 'integration' / 'actors.yml').read_text())
body, data, n = gltf(HERE / 'export' / 'hes_noble.glb')
names = {a['name'] for a in body['animations']}
joints = {body['nodes'][j]['name'] for j in body['skins'][0]['joints']}
problems, report = [], {}
for i, mesh in enumerate(body['meshes']):
    for key, most in (('openyamm_lods', 3), ('openyamm_shadow_lods', 4)):
        ch = (mesh.get('extras') or {}).get(key)
        if ch is not None and not (0 < len(ch) <= most and len(set(ch)) == len(ch) and all(c != i and c < len(body['meshes']) for c in ch)):
            problems.append(f'mesh {i} {key} {ch}')
for k, m in enumerate(body['materials']):
    if (m.get('extras') or {}).get('openyamm_specular_mask') and 'metallicRoughnessTexture' not in m.get('pbrMetallicRoughness', {}):
        problems.append(f'material {m["name"]} specular mask without MR texture')
skinned = {nd['mesh'] for nd in body['nodes'] if 'skin' in nd and 'mesh' in nd}
for mi in skinned:
    for p in body['meshes'][mi]['primitives']:
        used = {p['material']} | {x['material'] for x in p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])}
        for k in used:
            ex = body['materials'][k].get('extras') or {}
            if 'openyamm_burn_map' not in ex:
                problems.append(f'material {body["materials"][k]["name"]} lacks a burn map'); continue
            img = body['images'][body['textures'][ex['openyamm_burn_map']['index']]['source']]
            v = body['bufferViews'][img['bufferView']]; w, h = struct.unpack_from('>II', data, 28 + n + v.get('byteOffset', 0) + 16)
            if min(w, h) < 4: problems.append(f'burn map {img.get("name")} {w}x{h}')
lod0 = max(skinned, key=lambda mi: tris(body, mi))
for r in rows:
    d = r['descriptor']; clips = list(r['clips'].values()) + list((r.get('script_clips') or {}).values()) + \
        [r['animation'][k] for k in ('cast', 'run') if k in r['animation']]
    for c in clips:
        if c not in names: problems.append(f'{d}: clip {c} missing')
    look = r['animation'].get('look')
    if look and not all(k in look for k in ('nodes', 'max_yaw_degrees', 'max_pitch_degrees')):
        problems.append(f'{d}: look needs nodes, max_yaw_degrees and max_pitch_degrees (WorldFxSystem.cpp)')
    for s in list(r['animation'].get('sockets', {}).values()) + [a['node'] for a in r.get('attachments', [])]:
        if s not in joints: problems.append(f'{d}: node {s} is not a joint')
    total = tris(body, lod0)
    for a in r.get('attachments', []):
        f = HERE / 'export' / Path(a['model']).name
        if not f.exists(): problems.append(f'{d}: {f.name} missing'); continue
        g, _, _ = gltf(f); total += max(tris(g, mi) for mi in range(len(g['meshes'])))
    report[d] = {'lod0_triangles': total}
    if total > 15000: problems.append(f'{d}: {total} triangles at LOD0')
report['problems'] = problems
(HERE / 'review' / 'validation.json').write_text(json.dumps(report, indent=1))
print('VALIDATE', 'PASS' if not problems else 'FAIL', json.dumps(report))
sys.exit(1 if problems else 0)
