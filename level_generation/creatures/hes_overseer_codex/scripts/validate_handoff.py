"""Verify exported review assets, receipts and gate provenance without launching a browser."""
import ast, hashlib, importlib.util, json, subprocess, sys
from pathlib import Path
import numpy as np
P = Path(__file__).resolve().parents[1]
REPO = P.parents[2]
sys.path.insert(0, str(P.parent / 'claude_shared'))
import region_variants as rv
spec = importlib.util.spec_from_file_location('glb_accessors', REPO / 'tools/merge_head_material.py')
gt = importlib.util.module_from_spec(spec); spec.loader.exec_module(gt)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((P / 'review/viewer/manifest.json').read_text())
gates = json.loads((P / 'review/gates_candidate/gates.json').read_text())
assert gates['status'] == 'PASS', gates['counts']
for asset in gates['assets']:
    path = Path(asset['path'])
    assert path.is_file() and sha(path) == asset['sha256'], path
assert gates['runner_sha256'] == sha(P.parent / 'claude_shared/gates/run_gates.py')
assert gates['config'] == json.loads((P / 'gates_overseer.json').read_text())
motion = json.loads((P / 'review/feedback_motion.json').read_text())['ranged_export_check']
assert motion['glb_sha256'] == sha(P / 'work/overseer_body_lod0.glb')
source = P / 'source/mm6_wdm_source.glb'
assert sha(source) == '42c618d88c460fbfce951a3795838c416cf7a1a1928eae267ec1b3d21a00059d'
assets = {}; models = []
paths = [P / 'review/viewer' / m['url'].split('?')[0] for m in manifest['models']]
paths += sorted((P / 'work/attachments').glob('*.glb'))
paths += [P / 'work' / (name + '.glb') for name in ['overseer_body_lod0', 'overseer_assembled_lod0', 'overseer_variants_lod0']]
for path in paths:
    doc, binary = rv.read_glb(path)
    triangles = sum(doc['accessors'][pr['indices']]['count'] // 3 for m in doc['meshes'] for pr in m['primitives'])
    assert all('emissiveTexture' not in mat for mat in doc.get('materials', []))
    for mesh in doc['meshes']:
        for pr in mesh['primitives']:
            for key in ['POSITION', 'NORMAL', 'TEXCOORD_0']:
                values = gt.accessor_array(doc, binary, pr['attributes'][key])
                assert np.isfinite(values).all(), (path, key)
            if 'WEIGHTS_0' in pr['attributes']:
                weights = gt.accessor_array(doc, binary, pr['attributes']['WEIGHTS_0'])
                assert np.max(np.abs(weights.sum(1) - 1)) < 1e-5, path
    assets[str(path.relative_to(P))] = {'sha256': sha(path), 'triangles': triangles, 'clips': len(doc.get('animations', [])), 'bytes': path.stat().st_size}
for model in manifest['models']:
    path = P / 'review/viewer' / model['url'].split('?')[0]
    assert sha(path) == model['sha256'] and model['sha256'][:12] in model['url']
    doc, binary = rv.read_glb(path)
    assert {a['name'] for a in doc['animations']} == set(manifest['clips']) and len(doc['animations']) == 7
    triangles = assets[str(path.relative_to(P))]['triangles']; assert triangles <= 15000
    assert {'OV_Weapon_pulse_pistol', 'OV_Grip_pulse_pistol'} <= {m['name'].split('.')[0] for m in doc['materials']}
    durations = {}
    for action in doc['animations']:
        duration = max(float(gt.accessor_array(doc, binary, s['input']).max()) for s in action['samplers'])
        info = manifest['clips'][action['name']]; assert abs(duration - info['duration']) < 1e-5
        durations[action['name']] = duration
        for anchor in info['anchors']:
            assert 0 <= anchor['time'] <= duration + 1e-5
            assert all((path.parent / image).is_file() for image in anchor['source_images'])
    models.append({'model': model['id'], 'sha256': sha(path), 'triangles': triangles, 'durations': durations})
progress = json.loads((P / 'creature_3d_progress.json').read_text())
jobs = json.loads((P / 'meshy/job_manifest.json').read_text()); weapons = []
for job in jobs['jobs']:
    receipt = progress['meshy']['jobs'][job['id']]
    assert receipt['status'] == 'SUCCEEDED' and receipt['consumed_credits'] == 5
    returned = receipt['downloads']['model_urls_glb']
    assert sha(P / returned['path']) == returned['sha256']
    assert sha(P / job['input_image']) == job['input_sha256']
    assert job['ready_to_submit'] is False
    weapons.append({'job': job['id'], 'returned_sha256': returned['sha256'], 'processed': job['post_return_status']})
assert sum(j['consumed_credits'] for j in progress['meshy']['jobs'].values()) == jobs['credits_spent'] == 15
for path in (P / 'scripts').glob('*.py'): ast.parse(path.read_text(), filename=str(path))
subprocess.run(['node', '--check', str(P / 'review/viewer/review.js')], check=True)
checker = REPO / 'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py'
run = subprocess.run([sys.executable, str(checker), *map(str, paths)], capture_output=True, text=True)
(P / 'review/winding_candidate.txt').write_text(run.stdout + run.stderr)
assert run.returncode == 0, run.stdout + run.stderr
(P / 'review/candidate_assets.json').write_text(json.dumps(assets, indent=2) + '\n')
result = {'status': 'PASS: exported LOD0 handoff checks; integrator visual acceptance pending', 'viewer_models': models, 'weapons': weapons, 'ranged_export_metrics': motion, 'production_gate_counts': gates['counts'], 'source_sha256': sha(source), 'inverted_closed_parts': 0, 'winding_glbs': len(paths), 'browser_game_checks': 'not_run; integrator rule 9', 'python_syntax': 'pass', 'viewer_javascript_syntax': 'pass', 'viewer_links_and_clip_durations': 'pass'}
(P / 'review/feedback_validation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'status': 'PASS', 'models': len(models), 'gates': gates['counts'], 'winding_glbs': len(paths), 'credits_spent': 15}))
