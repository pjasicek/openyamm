"""Monster reach probes (playbook: a "cut off" audit finding is tested in game against a plain-floor control, in and
out of sight). Writes probe_<name>.yml here; run_probes.sh runs them and prints each actor's last reported position."""
import json
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
MAP = 'verhoffinruins.blv'
FLOOR = -327
movers = json.loads((HERE.parent / 'work/doors.json').read_text())
EV = {m['group']: m['event'] for m in movers if m['event']}


def lt(x, z):
    return [int(round(x * 2.56)), int(round(z * 2.56)), FLOOR]


def base(name, steps):
    yaml.safe_dump({'id': f'mm9r.vr_probe_{name}', 'title': name, 'world': 'mm9', 'mode': 'faithful',
                    'tags': ['mm9', 'draft'], 'steps': steps}, open(HERE / f'probe_{name}.yml', 'w'), sort_keys=False)


def pose(p):
    return {'set_pose': {'map': MAP, 'x': p[0], 'y': p[1], 'z': p[2], 'yaw': 0, 'pitch': 0}}


def report(index):
    return {'assert': {'actor_visible': {'actor_index': index, 'report_state': True}}}


def track(name, index, party, seconds=20, tick=2, hide=None, first=()):
    """A placed actor and the party in a pose; with `hide`, the party moves there after a look."""
    steps = [{'load_map': {'map': MAP}}, *first, pose(party), report(index), {'advance_runtime': {'seconds': 2}},
             report(index)]
    for _ in range(0, seconds, tick):
        steps += [{'advance_runtime': {'seconds': tick}}, pose(hide or party), report(index)]
    base(name, steps)


def spawn(name, monster, party, at, seconds=20, tick=2, first=()):
    index = 30                       # the map places 30 actors
    steps = [{'load_map': {'map': MAP}}, *first, pose(party),
             {'spawn_actor': {'monster_id': monster, 'count': 1, 'x': at[0], 'y': at[1], 'z': at[2], 'group': 77}},
             report(index)]
    for _ in range(0, seconds, tick):
        steps += [{'advance_runtime': {'seconds': tick}}, pose(party), report(index)]
    base(name, steps)


OPEN_DD14 = [{'execute_event': {'id': EV['DD14']}}, {'advance_runtime': {'seconds': 3}}]
# Room 4 (behind DD14): Terror0 (actor 11) and Terror4 (27); the audit says they cannot walk to the start.
track('room4_seen', 11, lt(1000, -2160), first=OPEN_DD14)
track('room4_hidden', 11, lt(1000, -2160), hide=lt(500, -2100), seconds=24, first=OPEN_DD14)
track('room4_far', 11, lt(-300, -2100), seconds=30, first=OPEN_DD14)
# Control: the same monster row on the plain corridor floor.
spawn('control_corridor', 9164, lt(500, -2100), lt(950, -2100))
# Control in sight range: the same row 700 units from the party on the corridor floor.
spawn('control_near', 9164, lt(600, -2100), lt(880, -2100))
