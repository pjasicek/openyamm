"""Chest loot: MM7 by stage, MM9 by chapter (BALANCE_PLAN.md section 3.7). Run from the repository root.

Both sides go through the engine's chest rules (game/gameplay/ChestRuntime.cpp): a random record of level L on a map of
treasure level T (map_stats column 11, plus one) remaps to a level range (remapTreasureLevelRange); a level-7 record is
an artifact and skips the remap. Any other record rolls 1-5 times: 20% nothing, 40% gold, 40% an item of the remapped
level. MM7's chests come from its scenes' raw chest records; MM9's from the rebuilt scenes' loot containers (one random
record of random_treasure_level each, random_records of them). Usage: chests.py [--planned]
  --planned  MM9 with tools/mm9_import_discovery/mm9_chest_balance.py applied (BALANCE_PLAN.md 3.7)
"""
import csv, glob, os, runpy, struct, sys
from collections import defaultdict

import yaml

sys.path.insert(0, 'tools/mm9_import_discovery')
from mm9_density_targets import CHAPTER_MAPS  # noqa: E402
import mm9_chest_balance  # noqa: E402

ARGS = dict(zip(sys.argv[1::2], sys.argv[2::2]))
PLANNED = '--planned' in sys.argv

MAPPING = [
    [(1, 1), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1)],
    [(1, 1), (1, 2), (2, 2), (2, 2), (2, 2), (2, 2), (2, 2)],
    [(1, 2), (2, 2), (2, 3), (3, 3), (3, 3), (3, 3), (3, 3)],
    [(2, 2), (2, 2), (3, 3), (3, 4), (4, 4), (4, 4), (4, 4)],
    [(2, 2), (2, 2), (3, 4), (4, 4), (4, 5), (5, 5), (5, 5)],
    [(2, 2), (2, 2), (4, 4), (4, 5), (5, 5), (5, 6), (6, 6)],
    [(2, 2), (2, 2), (7, 7), (7, 7), (7, 7), (7, 7), (7, 7)],
]


def map_levels() -> dict:
    out = {}
    rows = list(csv.reader(open('assets_dev/engine/data_tables/map_stats.txt', encoding='utf-8', errors='replace'),
                           delimiter='\t'))[3:]
    for r in rows:
        if len(r) > 11 and r[11].strip().isdigit():
            out.setdefault(r[2].strip().lower(), int(r[11]))
    return out


def record_outcome(level: int, map_level: int) -> tuple[float, float, float, float]:
    """Expected (items, item level x items, gold rolls, artifacts) of one random record."""
    if level >= 7:
        return 0.0, 0.0, 0.0, 1.0
    lo, hi = MAPPING[min(max(level, 1), 7) - 1][min(max(map_level + 1, 1), 7) - 1]
    artifacts = 0.0
    if hi == 7:
        return 0.0, 0.0, 0.0, 1.0
    mean_level = (lo + hi) / 2
    items = 3 * 0.4
    return items, items * mean_level, 3 * 0.4, artifacts


def totals(records_by_group: dict) -> dict:
    out = {}
    for group, records in records_by_group.items():
        items = levelsum = gold = arts = 0.0
        for level, map_level in records:
            a, b, c, d = record_outcome(level, map_level)
            items += a; levelsum += b; gold += c; arts += d
        out[group] = (len(records), items, levelsum / items if items else 0, gold, arts)
    return out


levels = map_levels()

# MM7: stages as fit_check.py sets them (median monster level per map).
argv = sys.argv
sys.argv = ['fit_check']
fit = runpy.run_path('devdocs/mm9_rework/balance_prototypes/fit_check.py', run_name='fit')
sys.argv = argv
stage_of = fit['mm7_stage_of_map']
mm7 = defaultdict(list)
mm7_chests = defaultdict(int)
for path in sorted(glob.glob('assets_dev/worlds/mm7/maps/*.scene.yml')):
    stem = os.path.basename(path).replace('.scene.yml', '')
    if stem not in stage_of:
        continue
    ext = '.odm' if os.path.exists(path.replace('.scene.yml', '.odm')) else '.blv'
    map_level = levels.get(stem + ext, 0)
    scene = yaml.load(open(path), Loader=yaml.CSafeLoader)
    for chest in (scene.get('initial_state') or {}).get('chests') or []:
        raw = bytes.fromhex(chest.get('raw_items_hex', ''))
        ids = [struct.unpack_from('<i', raw, i * 36)[0] for i in range(len(raw) // 36)]
        randoms = [-i for i in ids if -7 <= i < 0]
        if ids and any(ids):
            mm7_chests[stage_of[stem]] += 1
        mm7[stage_of[stem]] += [(level, map_level) for level in randoms]

mm9 = defaultdict(list)
mm9_chests = defaultdict(int)
for chapter, stems in CHAPTER_MAPS.items():
    for stem in stems.split():
        path = f'assets_dev/worlds/mm9/maps/{stem}.scene.yml'
        if not os.path.exists(path):
            continue
        map_level = levels.get(stem + '.blv', 0)
        scene = yaml.load(open(path), Loader=yaml.CSafeLoader)
        containers = scene.get('loot_containers') or []
        for container in containers:
            mm9_chests[chapter] += 1
            if container.get('gold_only') or not (container.get('random') or container.get('ai_drop')):
                continue
            level = int(container.get('random_treasure_level') or 0)
            records = int(container.get('random_records') or 1)
            if PLANNED:
                planned = mm9_chest_balance.balance_loot_containers(stem, [dict(c) for c in containers])
                container = planned[containers.index(container)]
                level = int(container['random_treasure_level'])
                records = int(container.get('random_records') or 1)
            if level > 0:
                mm9[chapter] += [(level, map_level)] * records

t7, t9 = totals(mm7), totals(mm9)
print('stage | MM7 chests, random records, items, mean item level, artifacts | MM9 same')
for s in range(1, 6):
    a, b = t7.get(s, (0, 0, 0, 0, 0)), t9.get(s, (0, 0, 0, 0, 0))
    print(f'{s} | {mm7_chests[s]:4} {a[0]:4} {a[1]:6.1f} {a[2]:4.2f} {a[4]:4.1f} | '
          f'{mm9_chests[s]:4} {b[0]:4} {b[1]:6.1f} {b[2]:4.2f} {b[4]:4.1f}')
print('all |', sum(mm7_chests.values()), round(sum(v[1] for v in t7.values()), 1), '|',
      sum(mm9_chests.values()), round(sum(v[1] for v in t9.values()), 1))
