"""Exact owned-layout coverage plus bounded representative construction/material checks."""
import json
from pathlib import Path
import subprocess
import sys

import yaml

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from export_indoor_scene_yml import parse_indoor_blv


def write(name, shots):
    (HERE / f'review/{name}_tour.yml').write_text(yaml.safe_dump({
        'output_dir': str((HERE / f'review/native_{name}').resolve()), 'settle_seconds': 1.5,
        'exit': True, 'shots': shots}, sort_keys=False))


def main():
    owned = json.loads((HERE / 'ownership.json').read_text())
    subprocess.run([sys.executable, str(HERE / 'scripts/extract_save_positions.py')], check=True)
    by_icon = json.loads((HERE / 'receipts/settled_positions.json').read_text())['positions']
    indoor = parse_indoor_blv(ROOT / 'assets_dev/worlds/mm6/maps/6d19.blv')
    floor = [indoor['vertices'][i] for i in indoor['face_vertex_ids'][12]]
    assert {v['z'] for v in floor} == {0}
    assert min(v['x'] for v in floor) == -768 and max(v['x'] for v in floor) == 512
    assert min(v['y'] for v in floor) == -1792 and max(v['y'] for v in floor) == -32
    shots, coverage = [], {}
    for family, group_size in [('bows', 6), ('blasters', 5), ('wands', 5)]:
        rows = [r for r in owned if r['family'] == family]
        for i in range(0, len(rows), group_size):
            group = rows[i:i + group_size]
            positions = [by_icon[r['icon']] for r in group]
            x = sum(p[0] for p in positions) / len(positions)
            y = positions[0][1]
            ground = max(p[2] for p in positions)
            name = f'{family}-{i // group_size + 1}'
            shots.append({'name': name, 'position': [x, y + 640, ground + 240],
                          'yaw': -1.5707963, 'pitch': -.56, 'time': '12:00'})
            coverage[name] = [r['icon'] for r in group]
    write('coverage', shots)
    representatives = ['6bow6', '7item045', '7item046', 'item060', '7item047', '7item049',
                       'item246', '7item064', '7item065', 'blastsg', 'raygun2', '7item138',
                       '7item139', 'item154', 'item155', 'wand2', 'wand3', 'wand4', 'wand5',
                       'raygun1', '7item137', 'item152', 'item153', 'item156', 'bow4']
    shots = []
    for icon in representatives:
        x, y, ground = by_icon[icon]
        shots += [
            {'name': icon + '-normal', 'position': [x, y + 330, ground + 40],
             'yaw': -1.5707963, 'pitch': -.58, 'time': '12:00'},
            {'name': icon + '-low', 'position': [x - 200, y + 200, ground - 70],
             'yaw': -.785398, 'pitch': -.4}]
    # Separate bounded tours leave startup and readback time within each run's limit.
    for index in range(0, len(shots), 12):
        write(f'outdoor_{index // 12 + 1}', shots[index:index + 12])
    bindings = {r['icon']: r['binding'] for r in owned}
    for index in range(0, len(representatives), 6):
        shots = []
        for j, icon in enumerate(representatives[index:index + 6]):
            x, y = 0, -1400
            shots.append({'name': icon + '-dim', 'position': [x, y - 290, 0],
                          'yaw': 1.5707963, 'pitch': -.52,
                          # Reuse an unobstructed spot; the shared model path uses the actual item scale and PBR.
                          'commands': ['model stop all',
                                       f'model spawn {bindings[icon]["model"]} {x} {y} 1 {bindings[icon]["length"]} 0'],
                          'settle_seconds': 2})
            shots.append({'name': icon + '-dim-low', 'position': [x, y - 370, -60],
                          'yaw': 1.5707963, 'pitch': -.30})
        write(f'indoor_{index // 6 + 1}', shots)
    (HERE / 'review/native_coverage.json').write_text(json.dumps({
        'layout': 'Original settled MM7 all-items save; no custom outdoor drops',
        'coverage': coverage, 'representatives': representatives,
        'indoor_floor': '6d19.blv face 12: flat entrance floor Z=0, verified from BLV vertices. Shared-model console instances at actual binding length and one-unit rest offset allow unobstructed material review; outdoor captures use actual ground items.'}, indent=2) + '\n')
    assert {icon for group in coverage.values() for icon in group} == set(by_icon)
    print(f'Prepared native coverage of {len(by_icon)} icons and {len(representatives)} representatives')


if __name__ == '__main__':
    main()
