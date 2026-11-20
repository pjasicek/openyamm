"""Deepwell's authoritative plan, arrivals and checks, without regenerating design files."""
import importlib.util
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
spec = importlib.util.spec_from_file_location('zone4', ROOT/'design/kreegan_world/zone4/dungeons/plans_zone4.py')
zone = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zone)
PLAN = zone.d13
ROOMS = {r['id']: r for r in PLAN.rooms}
# R5 wildlife occupies the deep vein beyond the sealed machinery route.
ROOMS['vein'] = dict(id='vein', name='Deep Vein', x=8192, y=2900, w=2600, h=1500, z=0,
                     floor=zone.TAP, ceiling=640, sectors=1, role='combat')
ARRIVALS = {'shaft_bottom': {'position': [400,1000,0], 'direction_degrees': 0},
            'tap_ring': {'position': [5228,1000,0], 'direction_degrees': 0}}


def checks(level):
    overlap, where = zone.plans.max_light_overlap(PLAN)
    ceilings = zone.plans.ceiling_problems(PLAN)
    stacking = zone.plans.stacking_problems(PLAN)
    assert overlap <= 4 and not ceilings and not stacking, (overlap,ceilings,stacking)
    report = dict(completed_through=level,max_lights=overlap,worst_point=where,
                  ceiling_problems=ceilings,stacking_problems=stacking,budget=zone.plans.budget(PLAN))
    (PROJECT/'review'/f'checks_{level}.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__': print(checks('preflight'))
