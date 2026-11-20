"""Check both zone-1 populations, native floor clearance and saved spawn visibility after their scenarios."""
import json
import struct
import sys
from pathlib import Path

import yaml

PROJECTS = Path(__file__).resolve().parents[3] / "projects"
ROOT = PROJECTS.parent.parent
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file


def population(name):
    project = PROJECTS / ('hesper_' + name)
    actors = json.loads((project / f'{name}_build.json').read_text())['actor_records']
    native = parse_blv_file(project / f'runtime/hes_{name}.blv')['payload']
    for actor in actors:
        x, y, z = actor['position'].values()
        surfaces = []
        for face in native['faces']:
            if face['room_number'] != actor['sector_id'] or face['is_portal'] or face['texture_name'] == 'hibrine':
                continue
            vertices = [native['vertices'][i] for i in face['vertex_indices']]
            if len({v['z'] for v in vertices}) != 1:
                continue
            signs = [(vertices[(i+1) % len(vertices)]['x']-v['x'])*(y-v['y'])
                     - (vertices[(i+1) % len(vertices)]['y']-v['y'])*(x-v['x']) for i, v in enumerate(vertices)]
            if all(s >= 0 for s in signs) or all(s <= 0 for s in signs):
                surfaces.append((vertices[0]['z'], face['facet_type']))
        floors = [height for height, kind in surfaces if kind == 3]
        ceilings = [height for height, kind in surfaces if kind == 5 and height > z]
        assert floors and ceilings, (name, actor)
        assert max(floors) <= z and z + actor['height'] <= min(ceilings), (name, actor, surfaces)
        if actor['monster_id'] != 10050:
            assert max(floors) == z, (name, actor, surfaces)
    print('PASS native floor/ceiling clearance', name, len(actors))
    return actors


def saved_groups(name, scenario, save, actors, expected):
    raw = (Path('/tmp/openyamm_scenario_saves') / f'hesper_{name}_{scenario}' / (save + '.oysav')).read_bytes()
    # shortcut: the version-133 MapDeltaActor prefix; update this fixture check when the save codec changes.
    assert raw[:8] == b'OYSAVE1\0' and struct.unpack_from('<I', raw, 8)[0] == 133
    for group, hidden in expected.items():
        members = [a for a in actors if a['group'] == group]
        found = []
        for label, monster in {(a['name'], a['monster_id']) for a in members}:
            text = label.encode()
            needle = struct.pack('<Q', len(text)) + text
            start = 0
            while (start := raw.find(needle, start)) >= 0:
                offset = start + len(needle)
                start += 1
                if struct.unpack_from('<h', raw, offset)[0] != 0:
                    continue
                if struct.unpack_from('<hh', raw, offset+11) != (monster, monster):
                    continue
                if struct.unpack_from('<I', raw, offset+49)[0] != group:
                    continue
                found.append(bool(struct.unpack_from('<I', raw, offset+2)[0] & 0x10000))
        assert found and len(found) % len(members) == 0, (save, group, len(found))
        assert all(value == hidden for value in found), (save, group, found)
    print('PASS native saved visibility', save, expected)


d2 = population('d02')
assert len(d2)==25 and sum(a['monster_id']==10320 for a in d2)==5
saved_groups('d02','gloamers','gloamers_d02_hidden',d2,{8:True})
saved_groups('d02','gloamers','gloamers_d02_drained',d2,{8:False})
print('D2 GLOAMER DRAIN GATE PASS')
