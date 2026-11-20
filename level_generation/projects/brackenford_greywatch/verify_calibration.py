"""Check the actual Blender-exported GLB -> native BLV calibration result."""
import base64
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file

data = parse_blv_file(PROJECT / 'calibration/calibration.blv')['payload']
expected = json.loads((PROJECT / 'calibration/expectations.json').read_text())
bounds = [[min(v[a] for v in data['vertices']) for a in 'xyz'],
          [max(v[a] for v in data['vertices']) for a in 'xyz']]
assert bounds == expected['bounds_game'], bounds
assert len(data['sectors']) == expected['occupied_sectors'] + 1
sector_zero = base64.b64decode(data['sectors'][0]['raw_record_base64'])
assert struct.unpack_from('<H', sector_zero, 48)[0] == 0
portals = [f for f in data['faces'] if f['is_portal']]
assert len(portals) == 1
assert [portals[0]['room_number'], portals[0]['room_behind_number']] == expected['portal_sector_pair']
targets = [f for f in data['faces'] if f['face_param']['cog_triggered'] == expected['surface_event']]
assert len(targets) == 1
panel = targets[0]
assert panel['texture_name'] == 'gt002b'
assert max(panel['texture_us']) - min(panel['texture_us']) == 64
assert max(panel['texture_vs']) - min(panel['texture_vs']) == 64
assert all(f['room_number'] > 0 for f in data['faces'])
assert len(data['bsp_nodes']) > 0
assert len(data['outlines']) > 0
divider_segments = []
for outline in data['outlines']:
    assert outline['vertex1_id'] < len(data['vertices'])
    assert outline['vertex2_id'] < len(data['vertices'])
    a = data['vertices'][outline['vertex1_id']]
    b = data['vertices'][outline['vertex2_id']]
    if a['x'] == b['x'] == 1024:
        divider_segments.append(sorted((a['y'], b['y'])))
assert sorted(divider_segments) == [[0, 384], [640, 1024]], divider_segments
report = {'result': 'passed', 'scope': 'Blender/native compiler calibration, not gameplay',
          'bounds': bounds, 'faces': len(data['faces']), 'vertices': len(data['vertices']),
          'occupied_sectors': 2, 'portal_pair': expected['portal_sector_pair'],
          'event': panel['face_param']['cog_triggered'], 'panel_uv_span_pixels': [64, 64],
          'bsp_nodes': len(data['bsp_nodes']), 'outlines': len(data['outlines'])}
(PROJECT / 'calibration/validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
