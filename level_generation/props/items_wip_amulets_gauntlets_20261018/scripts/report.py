"""Produce the final per-icon ledger, triangle/material inventory and coordinator-only bounds proposals."""
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import yaml

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from item_model_shapes import item_bounds, read_gltf
from validate_items import winding


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def counts(path):
    doc = read_gltf(path)
    lods = {i for m in doc['meshes'] for i in m.get('extras', {}).get('openyamm_lods', [])}
    tris = [sum(doc['accessors'][p['indices']]['count'] // 3 for p in m['primitives']) for m in doc['meshes']]
    return sum(t for i, t in enumerate(tris) if i not in lods), [tris[i] for i in sorted(lods)]


def texel_density(path, resolution, length, bounds):
    document, binary = winding.read_glb(path)
    omitted = {i for m in document['meshes'] for i in m.get('extras', {}).get('openyamm_lods', [])}
    density = []
    scale = length / max(bounds[1][0] - bounds[0][0], bounds[1][2] - bounds[0][2])
    for index, mesh in enumerate(document['meshes']):
        if index in omitted:
            continue
        for primitive in mesh['primitives']:
            p = winding.array(document, binary, primitive['attributes']['POSITION'])
            uv = winding.array(document, binary, primitive['attributes']['TEXCOORD_0'])
            faces = winding.array(document, binary, primitive['indices']).reshape(-1, 3)
            a, b = p[faces[:, 1]] - p[faces[:, 0]], p[faces[:, 2]] - p[faces[:, 0]]
            u, v = uv[faces[:, 1]] - uv[faces[:, 0]], uv[faces[:, 2]] - uv[faces[:, 0]]
            area = np.linalg.norm(np.cross(a, b), axis=1)
            uv_area = np.abs(u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0])
            density.extend(resolution * np.sqrt(uv_area / area) / scale)
    values = np.asarray(density)
    assert np.isfinite(values).all() and np.median(values) > 0
    return [round(float(v), 3) for v in np.percentile(values, [10, 50, 90])]


owned = json.loads((P / 'ownership.json').read_text())
validated = {e['icon']: e for e in json.loads((P / 'review/validation.json').read_text())}
installed = {e['icon']: e for e in json.loads((P / 'receipts/installed.json').read_text())}
assert len(owned) == len(validated) == len(installed) == 38
assert not json.loads((P / 'review/validation_failures.json').read_text())
native = json.loads((P / 'receipts/native_review.json').read_text())
assert native['status'] == 'passed' and len(native['cases']) == 9
manifest = ROOT / 'assets_dev/engine/world_items/items.yml'
bindings = {e['icon']: e for e in yaml.safe_load(manifest.read_text())['items']}
rows, proposals, ledger = [], [], []
for entry in owned:
    icon = entry['icon']
    receipt, check = installed[icon], validated[icon]
    source, runtime = ROOT / receipt['source'], ROOT / receipt['runtime']
    export = ROOT / receipt['export']
    assert sha(source) == receipt['source_sha256'] == sha(export) == check['sha256']
    assert sha(runtime) == receipt['runtime_sha256']
    assert bindings[icon]['length'] == entry['binding']['length']
    runtime_triangles, runtime_lods = counts(runtime)
    proposed = item_bounds(runtime, bindings[icon]['length'])
    current = bindings[icon].get('bounds')
    if current is None or any(abs(a - b) > .15 for a, b in zip(current, proposed)):
        proposals.append({'icon': icon, 'model': bindings[icon]['model'], 'length': bindings[icon]['length'],
                          'current_bounds': current, 'proposed_bounds': proposed,
                          'source_sha256': receipt['source_sha256'], 'runtime_sha256': receipt['runtime_sha256']})
    record = {'icon': icon, 'name': entry['items'][0]['name'], 'family': entry['family'],
              'triangles': check['triangles'], 'lod_triangles': check['lod_triangles'],
              'runtime_triangles': runtime_triangles, 'runtime_lod_triangles': runtime_lods,
              'materials': check['materials'], 'texture_size': 256 if entry['family'] == 'amulets' else 512,
              'maps': 'basecolor + metallic/roughness + OpenGL tangent normal', 'status': 'replaced',
              'source_sha256': receipt['source_sha256'], 'runtime_sha256': receipt['runtime_sha256']}
    record['texels_per_world_unit_p10_median_p90'] = texel_density(
        source, record['texture_size'], bindings[icon]['length'], check['gltf_bounds'])
    rows.append(record)
    ledger.append(entry | record | {'export': receipt['export'], 'validation': 'passed',
                                    'install': 'standard scoped installer + desktop verify',
                                    'review': [f'review/finished/{icon}_{v}.png'
                                               for v in ['above', 'three_quarter', 'low', 'underside']]})
    assert all((P / path).exists() for path in ledger[-1]['review'])
summary = {}
for family in ['amulets', 'gauntlets']:
    selected = [r for r in rows if r['family'] == family]
    summary[family] = {'models': len(selected), 'triangles': sum(r['triangles'] for r in selected),
                       'minimum': min(r['triangles'] for r in selected), 'maximum': max(r['triangles'] for r in selected),
                       'runtime_triangles': sum(r['runtime_triangles'] for r in selected),
                       'models_with_lod': sum(bool(r['lod_triangles']) for r in selected)}
(P / 'ledger.json').write_text(json.dumps(ledger, indent=2) + '\n')
(P / 'review/model_stats.json').write_text(json.dumps({'families': summary, 'models': rows}, indent=2) + '\n')
with (P / 'review/model_stats.csv').open('w') as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
handoff = {'status': 'complete', 'assigned_icons': 38, 'replaced': 38, 'deferred': 0,
           'families': summary, 'all_materials': 'Imagegen albedo, physical class PBR, tangent normal textures',
           'new_meshy_credits': 0, 'reused_meshy_shapes': 17, 'historical_reused_shape_credits': 85,
           'shared_bindings_modified': False, 'binding_length_changes': [], 'bounds_proposals': proposals,
           'manifest_sha256_at_report': sha(manifest),
           'equipment_scope_followup': [e['icon'] for e in owned if e['family'] == 'gauntlets'],
           'ownership_authority': 'Explicit user follow-up; equipment project and Meshy claim left untouched',
           'original_all_items_save_sha256': sha(ROOT / 'saves/Ground items test.oysav'),
           'checks': ['38 source exports: finite attributes, closed parts, outward winding, UV range, grounding',
                      'All materials have base color, packed metallic/roughness and tangent normal textures',
                      'Albedo channels 30–243; binary metalness; physical roughness values',
                      'Per-icon scoped desktop cooking and verification', 'Four culling-enabled Blender views per icon'],
           'release': 'Development world_items WIP only; release and Android promotion remain separate'}
handoff['native_review'] = native
assert handoff['original_all_items_save_sha256'] == '795fffeb87a7d95962e0e4e5af72b166ca9b6986400f43ad96c0d95edbe2fffa'
(P / 'handoff.json').write_text(json.dumps(handoff, indent=2) + '\n')
print(json.dumps(summary, indent=2))
print('Bounds proposals:', len(proposals))
