"""Check batch D's authored pickups against the compiled and staged maps; run under the shared stage lock."""
import base64
from collections import Counter
import importlib.util
import json
import math
from pathlib import Path
import re
import struct
import sys

import yaml

ROOT = Path(__file__).resolve().parents[3]
PROJECTS = ROOT / 'level_generation/projects'
STAGE = ROOT / 'output/hesper_stage/assets_editor_dev/worlds/hesper'
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file


def floor_faces(native):
    return [[native['vertices'][v] for v in f['vertex_indices']] for f in native['faces']
            if not f['is_portal'] and struct.unpack('<3f', base64.b64decode(f['raw_header_base64'])[:12])[2] > .99]


def floor_heights(floors, x, y):
    heights = []
    for vertices in floors:
        crosses = [(b['x'] - a['x']) * (y - a['y']) - (b['y'] - a['y']) * (x - a['x'])
                   for a, b in zip(vertices, vertices[1:] + vertices[:1])]
        if min(crosses) >= -.01 or max(crosses) <= .01:
            heights.append(vertices[0]['z'])
    return heights


if __name__ == '__main__':
    ids = yaml.safe_load((PROJECTS / 'hesper_stage/decoration_ids.yml').read_text())['ids']
    kinds = {'canisters': 'hes_stim_canister', 'vats': 'hes_serum_vat',
             'satchels': 'hes_colony_satchel', 'bundles': 'hes_scrap_bundle'}
    expected = {11: (0, 28, 0, 20), 12: (0, 14, 6, 14), 13: (10, 0, 12, 0), 15: (0, 0, 16, 4)}
    for number, counts in expected.items():
        project = PROJECTS / f'hesper_d{number:02}'
        stem = f'hes_d{number:02}'
        semantic = json.loads((project / f'source/{stem}.semantic.json').read_text())
        pickups = semantic['pickups']
        native = parse_blv_file(project / f'runtime/{stem}.blv')['payload']
        scene = json.loads((project / f'runtime/{stem}.scene.yml').read_text())
        handlers = (project / f'source/{stem}.handlers.lua').read_text().split('HesperPickups.setup', 1)[1]
        assert Counter(p['model'] for p in pickups) == Counter(dict(zip(kinds.values(), counts)))
        assert len({p['event'] for p in pickups}) == len(pickups)
        assert counts[2] + counts[3] == min(20, max(6, round(len(native['faces']) * .008)))
        storage = Counter(p['room'] for p in pickups if p['event'] < 750)
        assert sorted(storage.values()) == {11: [4, 5, 5, 14], 12: [3, 4, 7], 13: [2, 3, 5], 15: []}[number]
        spec = importlib.util.spec_from_file_location('zone', ROOT / 'design/kreegan_world' /
                    f'zone{3 if number == 11 else 4}/dungeons/plans_zone{3 if number == 11 else 4}.py')
        zone = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(zone)
        rooms = {r['id']: r for r in getattr(zone, f'd{number}').rooms}
        floors = floor_faces(native)
        for kind, model in kinds.items():
            match = re.search(r'\b' + kind + r'\s*=\s*\{([^}]*)\}', handlers)
            configured = set(map(int, re.findall(r'\d+', match[1]))) if match else set()
            assert configured == {p['event'] for p in pickups if p['model'] == model}
        for pickup in pickups:
            model, event = pickup['model'], pickup['event']
            x, y, z = pickup['position']
            room = rooms[pickup['room']]
            assert room['role'] != 'boss', pickup
            assert room['x'] < x < room['x'] + room['w'] and room['y'] < y < room['y'] + room['h'], pickup
            entities = [e for e in native['entities'] if e['event_id_primary'] == event]
            assert len(entities) == 1, pickup
            entity = entities[0]
            assert entity['event_id_secondary'] == event and entity['decoration_list_id'] + 1 == ids[model], pickup
            assert [entity['position'][k] for k in ('x', 'y', 'z')] == pickup['position'], pickup
            radius = 55 if model == 'hes_serum_vat' else 30 if model == 'hes_stim_canister' else 18
            for dx, dy in ((0, 0), (radius, 0), (-radius, 0), (0, radius), (0, -radius)):
                heights = floor_heights(floors, x + dx, y + dy)
                assert any(abs(h - z) < 2 for h in heights), ('unsupported', pickup, dx, dy)
                assert not any(z + 2 < h < z + 512 for h in heights), ('buried', pickup, dx, dy)
            for actor in scene['initial_state']['actors']:
                a = actor['position']
                clearance = math.hypot(a['x'] - x, a['y'] - y) - actor['radius'] - radius
                assert abs(a['z'] - z) >= 80 or clearance >= 20, (pickup, actor['actor_index'])
        for obj in scene['initial_state']['sprite_objects']:
            assert int.from_bytes(bytes.fromhex(obj['raw_containing_item_hex'])[:4], 'little') != 189
        assert (STAGE / f'events/maps/{stem}_pickups.lua').exists()
        for name in (f'{stem}.blv', f'{stem}.scene.yml'):
            assert (project / 'runtime' / name).read_bytes() == (STAGE / 'maps' / name).read_bytes(), name
        assert (project / f'runtime/{stem}.lua').read_bytes() == (STAGE / f'events/maps/{stem}.lua').read_bytes()
        assert len(yaml.safe_load((project / 'review_tour_pickups.yml').read_text())['shots']) == 3
        print(f'D{number}: {counts[0]} canisters, {counts[1]} vats, {counts[2]} satchels, {counts[3]} bundles; '
              'placement and stage OK')
