"""Read-only D5 design inputs and checks, shared by authoring and validation."""
import importlib.util
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
spec = importlib.util.spec_from_file_location('plans_zone3', ROOT / 'design/kreegan_world/zone3/dungeons/plans_zone3.py')
zone = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zone)
PLAN = zone.d5
ROOMS = {room['id']: room for room in PLAN.rooms}
DOOR_IDS = zone.door_ids(PLAN)


def check():
    assert zone.plans.max_light_overlap(PLAN)[0] <= 4
    assert not zone.plans.ceiling_problems(PLAN)
    overlaps = zone.plans.stacking_problems(PLAN)
    assert len(overlaps) == 1 and overlaps[0].startswith('shaft '), overlaps
    assert sum(mark['count'] for mark in PLAN.marks if mark['kind'] in ('monster', 'boss')) == 69
    assert len(PLAN.lights) == 59
    return zone.plans.budget(PLAN)


if __name__ == '__main__':
    print(check())
