"""Scenario probes on the final map: a hostile monster goes for the party, in and out of sight, against a plain-floor
control. Writes probe_<name>.yml; run them with run_probes.sh."""
import yaml
MAP = 'drangheimprison.blv'
ACTOR = 80      # the first spawned actor (the map places 80)
LOW = -3582     # lower level floor + 2

def base(name, steps):
    return yaml.safe_dump({'id': f'mm9r.dp_probe_{name}', 'title': name, 'world': 'mm9', 'mode': 'faithful',
                           'tags': ['mm9', 'draft'], 'steps': steps}, open(f'probe_{name}.yml', 'w'), sort_keys=False)

def pose(p):
    return {'set_pose': {'map': MAP, 'x': p[0], 'y': p[1], 'z': p[2], 'yaw': 0, 'pitch': 0}}

def report():
    return {'assert': {'actor_visible': {'actor_index': ACTOR, 'report_state': True}}}

def seen(name, monster, party, spawn, seconds=16, tick=2, first=()):
    """The party stands in sight of the monster."""
    steps = [{'load_map': {'map': MAP}}, *first, pose(party),
             {'spawn_actor': {'monster_id': monster, 'count': 1, 'x': spawn[0], 'y': spawn[1], 'z': spawn[2], 'group': 77}},
             report()]
    for _ in range(0, seconds, tick):
        steps += [{'advance_runtime': {'seconds': tick}}, pose(party), report()]
    base(name, steps)

def chase(name, monster, party, hide, spawn, seconds=20, tick=2, first=()):
    """The monster sees the party, which then stands out of its sight."""
    steps = [{'load_map': {'map': MAP}}, *first, pose(party),
             {'spawn_actor': {'monster_id': monster, 'count': 1, 'x': spawn[0], 'y': spawn[1], 'z': spawn[2], 'group': 77}},
             {'advance_runtime': {'seconds': 1.5}}, report()]
    for _ in range(0, seconds, tick):
        steps += [pose(hide), {'advance_runtime': {'seconds': tick}}, report()]
    base(name, steps)


def track(name, index, party, seconds=16, tick=2, hide=None):
    """A placed actor (index) and the party in a pose; with `hide`, the party moves there after a look."""
    r = {'assert': {'actor_visible': {'actor_index': index, 'report_state': True}}}
    steps = [{'load_map': {'map': MAP}}, pose(party), r, {'advance_runtime': {'seconds': 2}}, r]
    for _ in range(0, seconds, tick):
        steps += [{'advance_runtime': {'seconds': tick}}, pose(hide or party), r]
    base(name, steps)

MOUTH = (1450, -4150, LOW)
track('h3_out_seen', 3, MOUTH, seconds=20)
track('h1_out_seen', 1, MOUTH, seconds=20)
track('h3_out_hidden', 3, MOUTH, seconds=24, hide=(1300, -3000, LOW))
track('h3_in_room', 3, (2150, -4300, LOW), seconds=10)

seen('gate_door_open2', 9081, (-940, -3400, -2228), (-940, -4300, -2230), seconds=14,
     first=[{'execute_event': {'id': 116}}, {'advance_runtime': {'seconds': 3}}])
seen('gate_door_shut2', 9081, (-940, -3400, -2228), (-940, -4300, -2230), seconds=14)

chase('gate_door_open3', 9081, (-940, -3800, -2228), (-940, -3400, -2228), (-940, -4300, -2230), seconds=12,
      first=[{'execute_event': {'id': 116}}, {'advance_runtime': {'seconds': 3}}])
