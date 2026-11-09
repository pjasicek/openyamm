"""Record final source/runtime checks and coordinator-owned collision/picking bounds proposals."""
import csv
import hashlib
import json
from pathlib import Path
import sys

import yaml

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from item_model_shapes import item_bounds, read_gltf


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    audit = json.loads((P / 'audit.json').read_text())
    checks = {e['icon']: e for e in json.loads((P / 'review/validation.json').read_text())}
    installed = {e['icon']: e for e in json.loads((P / 'receipts/installed.json').read_text())}
    before = json.loads((P / 'receipts/bindings_before.json').read_text())
    bindings = {e['icon']: e for e in yaml.safe_load((ROOT / 'assets_dev/engine/world_items/items.yml').read_text())['items']}
    native = json.loads((P / 'receipts/native_review.json').read_text())
    assert native['status'] == 'passed' and len(native['cases']) == 4
    assert len(audit) == 18 and sum(len(e['items']) for e in audit) == 514
    assert len(installed) == len(checks) == 9
    rows, proposals, ledger = [], [], []
    for entry in audit:
        icon = entry['icon']
        source = ROOT / 'assets_source/engine/world_items/models' / f'item_{icon}.glb'
        runtime = ROOT / 'assets_dev/engine/world_items/models' / source.name
        if entry['status'] != 'rebuild':
            assert sha(source) == entry['source_sha256'], (icon, 'retained source changed')
            ledger.append(entry)
            continue
        check, receipt = checks[icon], installed[icon]
        assert sha(source) == check['sha256'] == receipt['source_sha256']
        assert sha(runtime) == receipt['runtime_sha256']
        assert bindings[icon] == before[icon], (icon, 'binding changed since snapshot')
        doc = read_gltf(runtime)
        lods = {i for m in doc['meshes'] for i in m.get('extras', {}).get('openyamm_lods', [])}
        counts = [sum(doc['accessors'][p['indices']]['count'] // 3 for p in m['primitives']) for m in doc['meshes']]
        assert sum(t for i, t in enumerate(counts) if i not in lods) == check['triangles']
        assert [counts[i] for i in sorted(lods)] == check['lod_triangles']
        assert len(doc['materials']) == 1
        for mat in doc['materials']:
            assert 'normalTexture' in mat and 'baseColorTexture' in mat['pbrMetallicRoughness']
            assert 'metallicRoughnessTexture' in mat['pbrMetallicRoughness']
        length = bindings[icon]['length']
        bounds = item_bounds(runtime, length)
        if any(abs(a - b) > .15 for a, b in zip(bindings[icon]['bounds'], bounds)):
            proposals.append({'icon': icon, 'model': bindings[icon]['model'], 'length': length,
                              'current_bounds': bindings[icon]['bounds'], 'proposed_bounds': bounds,
                              'runtime_sha256': sha(runtime)})
        uv = json.loads((P / 'work' / f'uv_{icon}.json').read_text())
        extent = max(check['gltf_bounds'][1][a] - check['gltf_bounds'][0][a] for a in (0, 2))
        density = round(uv['texels_per_model_unit'] * extent / length, 3) if uv else None
        row = {'icon': icon, 'items_sharing_icon': len(entry['items']), 'triangles': check['triangles'],
               'lod_triangles': check['lod_triangles'], 'materials': 1, 'texture_size': 512,
               'paper_texels_per_world_unit': density, 'length': length,
               'source_sha256': sha(source), 'runtime_sha256': sha(runtime)}
        rows.append(row)
        ledger.append(entry | row | {'status': 'replaced', 'checks': 'passed',
                                    'reason': 'Blender component geometry; Imagegen-painted single-material PBR atlas'})
    (P / 'ledger.json').write_text(json.dumps(ledger, indent=2) + '\n')
    (P / 'review/model_stats.json').write_text(json.dumps(rows, indent=2) + '\n')
    with (P / 'review/model_stats.csv').open('w') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    save_sha = sha(ROOT / 'saves/Ground items test.oysav')
    assert save_sha == '795fffeb87a7d95962e0e4e5af72b166ca9b6986400f43ad96c0d95edbe2fffa'
    handoff = {'status': 'complete', 'examined_icons': 18, 'replaced': 9, 'retained': 9, 'deferred': 0,
               'triangles': sum(e['triangles'] for e in rows), 'models_with_lod': sum(bool(e['lod_triangles']) for e in rows),
               'mesh_route': 'Blender closed curled sheets, separate rollers/fittings, folded envelope and real wax seal',
               'texture_route': 'Built-in Imagegen parchment atlas plus retained Imagegen fitting materials; PBR + normal maps',
               'new_meshy_credits': 0, 'shared_bindings_modified': False, 'length_changes': [],
               'bounds_proposals': proposals, 'native_review': native, 'original_save_sha256': save_sha,
               'release': 'Development WIP only; no Android/release verification or performance benchmark'}
    (P / 'handoff.json').write_text(json.dumps(handoff, indent=2) + '\n')
    print('18 examined, 9 replaced, 9 retained; triangles', handoff['triangles'], '; bounds proposals', len(proposals))


if __name__ == '__main__':
    main()
