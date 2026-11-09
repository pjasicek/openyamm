"""Crownspire's plan, stable arrivals, door ids and floor checks; usable outside Blender."""
import importlib.util
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
spec = importlib.util.spec_from_file_location('zone4', ROOT / 'design/kreegan_world/zone4/dungeons/plans_zone4.py')
zone = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zone)
PLAN = zone.d12
ROOMS = {r['id']: r for r in PLAN.rooms}
LEVELS = ['core', 'palace', 'court', 'crown']
FLOORS = dict(zip(LEVELS, (zone.CORE_L, zone.PALACE, zone.COURT, zone.CROWN)))
ARRIVALS = {
    'spire_gate': {'position': [0, 400, 0], 'direction_degrees': 90},
    'service_lift': {'position': [9064, 2400, -1536], 'direction_degrees': 180},
    'pad_lift': {'position': [8164, 3800, -1536], 'direction_degrees': 270},
    'shaft_head': {'position': [1600, 19300, 2304], 'direction_degrees': 270},
}
DOORS = dict(zip(('spire_gate', 'inner_gate', 'gatehouse', 'barracks', 'court', 'ssekh', 'mraal', 'xith',
                 'corelift_gate', 'graftw', 'grafte', 'trophw', 'trophe', 'noblegal', 'housegal', 'armoury',
                 'throne', 'sanctum', 'shaft', 'crowns_gate', 'crowns_platform', 'core_platform',
                 'service', 'grid', 'coolant', 'padlift'), range(1, 27)))


def checks(level):
    """Run the authoritative checks without main() rewriting design documents and images."""
    overlap, where = zone.plans.max_light_overlap(PLAN)
    ceilings = zone.plans.ceiling_problems(PLAN)
    stacking = zone.plans.stacking_problems(PLAN)
    assert overlap <= 4 and not ceilings and not stacking, (overlap, where, ceilings, stacking)
    report = {'completed_through': level, 'max_lights': overlap, 'worst_point': where,
              'ceiling_problems': ceilings, 'stacking_problems': stacking, 'budget': zone.plans.budget(PLAN)}
    (PROJECT / 'review' / f'checks_{level}.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PLAN CHECKS', json.dumps(report))
    return report


if __name__ == '__main__':
    checks('preflight')
