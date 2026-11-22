"""In-game check of the Xeen ground items on X1 Vertigo Meadows: one quest item (items.txt content_flags Quest, and
12400) of every icon the quest items use, dropped in a grid on the open meadow east of the town.

Writes review/ingame/drop.yml (a headless scenario: new game, the arrival errand closed, the party moved to the meadow,
every item dropped with `item drop <id> x y z` and left to fall, saved as drop.oysav) and review/ingame/tour.yml
(engine-native screenshots of the grid). Then:

    python3 -I scripts/ingame_check.py [x y z]                  # base of the grid (default below)
    (cd <scratch run dir> && OPENYAMM_SCENARIO_SAVE_DIR=<dir> <repo>/build-xeen/game/openyamm --world xeen \\
        --headless-run-scenario <repo>/level_generation/props/items_xeen_claude/review/ingame/drop.yml)
    ./tools/run_game.sh --isolated xeen_items_tour --binary build-xeen/game/openyamm --world xeen \\
        --save <dir>/drop.oysav --warmup 4 --seconds 40 \\
        --set debug.screenshot_tour_path=<repo>/level_generation/props/items_xeen_claude/review/ingame/tour.yml
    grep 'has no 3D model' <run dir>/game.log"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ITEMS = os.path.join(REPO, 'assets_dev', 'worlds', 'xeen', 'data_tables', 'items.txt')
OUT = os.path.join(HERE, 'review', 'ingame')
COLUMNS, SMALL, LONG = 9, 90, 150


def items():
    """(item id, icon, long) for the first quest item of every icon."""
    lengths = json.load(open(os.path.join(HERE, 'classification.json')))
    by_icon = {entry['icon']: entry['length'] for entry in lengths.values()}
    seen, result = set(), []
    with open(ITEMS) as stream:
        for line in stream.readlines()[2:]:
            fields = line.split('\t')
            quest = len(fields) > 20 and ('Quest' in fields[20] or fields[0] == '12400')
            if quest and fields[1] not in seen:
                seen.add(fields[1])
                result.append((int(fields[0]), fields[1], by_icon.get(fields[1], 0) > 100))
    return result


def main():
    base = [float(v) for v in sys.argv[1:4]] if len(sys.argv) >= 4 else [8192.0, 4096.0, 640.0]
    bx, by, bz = base
    small = [i for i in items() if not i[2]]
    long = [i for i in items() if i[2]]
    drops = []
    for index, (item, icon, _) in enumerate(small):
        drops.append((item, bx + (index % COLUMNS) * SMALL, by + (index // COLUMNS) * SMALL))
    rows = math.ceil(len(small) / COLUMNS)
    for index, (item, icon, _) in enumerate(long):
        drops.append((item, bx + (index % 6) * LONG, by + rows * SMALL + 200 + (index // 6) * 300))
    steps = [{'new_game_flow': {'start_map': 'xeen_x1.odm'}},
             {'setup_shortcut': {'kind': 'immortal', 'value': True}},
             {'advance_runtime': {'seconds': 3.0}},
             {'press_action': {'action': 'cancel_dialog'}},
             {'set_pose': {'map': 'xeen_x1.odm', 'x': bx + 360, 'y': by - 400, 'z': bz + 200,
                           'yaw': 1.5708, 'pitch': 0.0}},
             {'advance_runtime': {'seconds': 2.0}}]
    steps += [{'console': {'line': f'item drop {item} {x:.0f} {y:.0f} {bz + 150:.0f}'}} for item, x, y in drops]
    steps += [{'advance_runtime': {'seconds': 4.0}}, {'save_game': 'drop'}]
    os.makedirs(OUT, exist_ok=True)
    scenario = {'id': 'xeen_ground_items', 'world': 'xeen', 'mode': 'faithful', 'steps': steps}
    with open(os.path.join(OUT, 'drop.yml'), 'w') as handle:
        json.dump(scenario, handle, indent=1)
    shots = [
        ('small_all', [bx + 360, by - 330, bz + 330], 1.5708, -0.62),
        ('small_near_west', [bx + 130, by - 120, bz + 150], 1.5708, -0.55),
        ('small_near_east', [bx + 590, by - 120, bz + 150], 1.5708, -0.55),
        ('small_far_west', [bx + 130, by + 160, bz + 150], 1.5708, -0.55),
        ('small_far_east', [bx + 590, by + 160, bz + 150], 1.5708, -0.55),
    ]
    tour = {'output_dir': OUT, 'settle_seconds': 2.5, 'exit': True,
            'shots': [{'name': name, 'position': position, 'yaw': yaw, 'pitch': pitch, 'time': '12:00'}
                      for name, position, yaw, pitch in shots]}
    with open(os.path.join(OUT, 'tour.yml'), 'w') as handle:
        json.dump(tour, handle, indent=1)
    print(len(drops), 'drops;', len(small), 'small,', len(long), 'long')


if __name__ == '__main__':
    main()
