#!/usr/bin/env python3
"""Check the Brood Mother handoff files; this does not certify a model or reference gate."""
import hashlib
import json
import math
from pathlib import Path

from PIL import Image
import yaml

PROJECT = Path(__file__).resolve().parents[1]
state = json.loads((PROJECT / 'creature_3d_progress.json').read_text())
runs = json.loads((PROJECT / 'references_hd/generation_runs.json').read_text())
for artifact in state['selected_artifacts']:
    assert hashlib.sha256((PROJECT / artifact['path']).read_bytes()).hexdigest() == artifact['sha256']
for run in runs:
    if not run.get('file'):
        assert run['status'] == 'rejected' and run['output'] is None
        continue
    path = PROJECT / run['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == run['sha256'], path
    with Image.open(path) as image:
        assert image.mode == 'RGBA' and image.size == (1536, 1024), path
        low, high = image.getchannel('A').getextrema()
        assert low == 0 and high >= 240, path
    for source in run.get('inputs', []):
        assert hashlib.sha256((PROJECT / source['file']).read_bytes()).hexdigest() == source['sha256']
geometry = json.loads((PROJECT / 'requests/brood_mother_geometry_v2.json').read_text())
assert geometry['image_url'] == '@file:references_hd/cradle_only/00_three_quarter.png'
assert geometry['ai_model'] == 'meshy-t2' and geometry['model_type'] == 'smart-topology'
assert geometry['target_polycount'] == 15000 and geometry['should_texture'] is False
assert 'pose_mode' not in geometry
texture = json.loads((PROJECT / 'requests/brood_mother_texture_v2.json').read_text())
assert texture['ai_model'] == 'meshy-7' and texture['enable_original_uv'] is False
assert texture['multiview_image_urls'] == [
    '@file:references_hd/cradle_only/01_front.png', '@file:references_hd/cradle_only/03_left.png',
    '@file:references_hd/cradle_only/02_back.png', '@file:references_hd/cradle_only/04_right.png']
layout = json.loads((PROJECT / 'socket_layout.json').read_text())
clearance = json.loads((PROJECT / layout['sac_measurements']).read_text())
assert layout['status'] == 'measured_export_and_all_clip_clearance_pass'
assert layout['separate_actor_id'] == 10130
assert layout['intended_binding_scale'] == layout['separate_actor_binding_scale'] == 100
assert layout['queen_standing_height_m'] * layout['intended_binding_scale'] == 450
assert layout['flat_top_clear_radius_m'] >= clearance['flat_top_radius_minimum_m']
assert {socket['name'] for socket in layout['sockets']} == {'left', 'right', 'rear'}
for socket in layout['sockets']:
    x, y, z = socket['top_centre_blender_m']
    assert socket['top_centre_gltf_m'] == [x, z, -y]
    assert all(math.isclose(actual, expected * 100, abs_tol=1e-6)
               for actual, expected in zip(socket['local_offset_game_units_left_back_up'], (x, y, z)))
assert len([run for run in runs if run['selected']]) == 5
assert all('/cradle_only/' in run['file'] for run in runs if run['selected'])
assert all(part['id'] != 'three_static_orange_egg_sacs' for part in state['required_components'])
assert not (PROJECT / 'requests/brood_mother_geometry_v1.json').exists()
assert not (PROJECT / 'requests/brood_mother_texture_v1.json').exists()
assert state['meshy']['credit_limit'] == 60
assert sum(job['estimated_credits'] for job in state['planned_meshy_jobs']) <= 60
assert yaml.safe_load((PROJECT / 'integration/actors.yml').read_text()) == []
manifest = json.loads((PROJECT / 'review/upload_manifest.json').read_text())
assert manifest['status'] == 'pass' and manifest['triangles'] <= 15000
for role in ('rig', 'upload'):
    assert hashlib.sha256((PROJECT / manifest[role]).read_bytes()).hexdigest() == manifest[role + '_sha256']
for filename in ('texture_ready_gates.json', 'texture_ready_sockets.json'):
    report = json.loads((PROJECT / 'review' / filename).read_text())
    assert report['status'] == 'pass' and report['sha256'] == manifest['rig_sha256']
assert texture['model_url'] == '@file:' + manifest['upload']
assert all((PROJECT / name[6:]).is_file() for name in [texture['model_url'], *texture['multiview_image_urls']])
viewer = json.loads((PROJECT / 'review/viewer/manifest.json').read_text())
assert viewer['models'][0]['sha256'] == manifest['rig_sha256']
assert {name: value['duration'] for name, value in viewer['clips'].items()} == manifest['clips']
assert set(manifest['clips']) == {'Standing', 'Fidget', 'Attack', 'Hit', 'Death', 'Dead'}
assert state['budget_summary']['spent'] == 5 and state['budget_summary']['reserved'] == 0
assert 'brood_mother_texture_v2' not in state['meshy']['jobs'], 'Do not call an already submitted job ready'
print(json.dumps({
    'handoff_files': 'pass', 'selected_generated_views': sum(bool(run['selected']) for run in runs),
    'reference_gate': state['stages']['references']['status'],
    'model_and_rig_gates': 'pass_60_hz', 'upload_parity_and_winding': 'pass', 'triangles': manifest['triangles'], 'staged_rows': [],
    'socket_positions': layout['status'],
    'texture_inputs_pending': [name[6:] for name in [texture['model_url'], *texture['multiview_image_urls']]
                               if not (PROJECT / name[6:]).is_file()],
}, indent=2))
