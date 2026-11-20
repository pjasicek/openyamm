"""Starport Reach's hostile monsters: the encounter spawn points and the placed squads of `spawns.yml`, placed on free
ground, and the map's load event that makes them hostile (README, "Hostile monsters").

build_out1.py calls `populate` once its buildings, decorations and Landfall's people are placed; it appends the
squads to the scene's actors and returns the spawn points and the load event. It also writes `work/spawns_plan.json`
(what was placed, where it moved, and the map's features) for spawn_density.py and make_tour.py.
"""
import json
import math
from pathlib import Path

import numpy as np
import yaml
from scipy import ndimage

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
STAGE_DATA = ROOT / 'level_generation/projects/hesper_stage'
GRID_STEP = 64                          # the occupancy grid's cell (world units)
SEARCH_STEP, SEARCH_RINGS = 80, 30      # a taken spot moves outward in rings of 80 units, up to 2 400
GROUND_MAX_Z = 4200                     # above this the ground is the Ash Sea's dune wall or Landfall's cliffs
SPAWN_RADIUS = 128                      # the spawn point's radius (MM: 32-256; the engine rings its actors round it)


def encounter_index(slot, tier):
    """The ODM spawn index: 1-3 a slot at a random tier, 4-12 a slot at a fixed tier (4 + 3 x tier + slot - 1)."""
    return slot if not tier else 4 + 3 * 'ABC'.index(tier) + slot - 1


def segment_distance(p, a, b):
    ax, ay = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / (ax * ax + ay * ay or 1.0)))
    return math.hypot(p[0] - a[0] - t * ax, p[1] - a[1] - t * ay)


class Ground:
    """Where an actor may stand: off the buildings' walls and out of their closed insides (an occupancy grid of the
    BModels' upright faces; a cell the open ground cannot reach is inside a building), off the decorations'
    collision, on level walkable ground, out of the brine (walkers), off the roads (spawn points)."""

    def __init__(self, models, entities, height_at, road_masks, on_brine, bound):
        self.height_at, self.road_masks, self.on_brine, self.bound = height_at, road_masks, on_brine, bound
        size = int(2 * bound / GRID_STEP)
        walls = np.zeros((size, size), bool)
        for model in models:
            for points, _, _ in model.faces:
                zs = [p[2] for p in points]
                if max(zs) - min(zs) < 120:                    # floors, roofs, plates, steps
                    continue
                for a, b in zip(points, points[1:] + points[:1]):
                    steps = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / (GRID_STEP / 2)))
                    for k in range(steps + 1):
                        x, y = a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps
                        i, j = self.cell(x, y)
                        if 0 <= i < size and 0 <= j < size:
                            walls[j, i] = True
        labels, _ = ndimage.label(~walls)
        counts = np.bincount(labels.ravel())
        counts[0] = 0
        self.blocked = labels != int(np.argmax(counts))     # walls and every closed inside
        radii = {d['name']: d.get('radius', 0) for d in yaml.safe_load(
            (STAGE_DATA / 'decorations.yml').read_text())['decorations']}
        self.obstacles = [(e['position']['x'], e['position']['y'], radii.get(e['name'], 0)) for e in entities
                          if radii.get(e['name'], 0) > 0]

    def cell(self, x, y):
        return int((x + self.bound) // GRID_STEP), int((self.bound - y) // GRID_STEP)

    def free(self, x, y, radius, walker=True, off_road=0.0):
        if abs(x) > self.bound - 800 or abs(y) > self.bound - 800:
            return False
        reach = int(math.ceil((radius + 48) / GRID_STEP))
        i, j = self.cell(x, y)
        if self.blocked[max(j - reach, 0):j + reach + 1, max(i - reach, 0):i + reach + 1].any():
            return False
        if any(math.hypot(x - ox, y - oy) < radius + r + 30 for ox, oy, r in self.obstacles):
            return False
        z = self.height_at(x, y)
        if z > GROUND_MAX_Z:
            return False
        if walker:
            d = radius + 100
            if any(abs(self.height_at(x + dx, y + dy) - z) > 0.6 * d for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d))):
                return False
            if self.on_brine({'x': x, 'y': y}):
                return False
        if off_road:
            ring = [(x + off_road * math.cos(a), y + off_road * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 8,
                                                                                                    endpoint=False)]
            xs, ys = np.array([x] + [p[0] for p in ring]), np.array([y] + [p[1] for p in ring])
            road, ruts, _ = self.road_masks(xs, ys)
            if road.any() or ruts.any():
                return False
        return True


def populate(*, place, height_at, models, entities, actors, road_masks, on_brine, bound, crew_door, wall_line,
             town_box, features):
    """Place the spawn points and squads of spawns.yml. `actors` gets the squads (the scene's initial actors);
    returns {'spawns': scene spawn records, 'load_event': (title, Lua body)}. `features` (chests, dungeons, items,
    houses, start, roads: world points) go to the plan file for spawn_density.py."""
    data = yaml.safe_load((PROJECT / 'spawns.yml').read_text())
    stage_maps = yaml.safe_load((STAGE_DATA / 'maps.yml').read_text())['maps']
    slots = next(m for m in stage_maps if m['file'] == 'hes_out1.odm')['slots']
    stage_monsters = {m['id']: m for m in yaml.safe_load((STAGE_DATA / 'monsters.yml').read_text())['monsters']}
    rows = {int(r[0]): r for r in (line.split('\t') for line in (ROOT / 'design/kreegan_world/data/monster_data.txt')
                                   .read_text().splitlines()) if r[0].isdigit()}
    pictures = {}
    for monster in stage_monsters.values():
        if 'picture' in monster:
            pictures[monster['picture'].lower()] = monster['id']
    ground = Ground(models, entities, height_at, road_masks, on_brine, bound)
    taken = [(a['position']['x'], a['position']['y'], a['radius']) for a in actors]
    moved, plan_spawns, plan_squads = [], [], []

    def quiet(x, y):
        if math.hypot(x - crew_door[0], y - crew_door[1]) < data['quiet']['crew_door']:
            return False
        if town_box[0] < x < town_box[2] and town_box[1] < y < town_box[3]:
            return False
        return all(segment_distance((x, y), a, b) >= data['quiet']['landfall_wall']
                   for a, b in zip(wall_line, wall_line[1:]))

    def find(name, x, y, radius, walker, off_road=0.0, gap=0.0):
        """The nearest free spot to (x, y): rings of SEARCH_STEP outward."""
        def ok(px, py):
            return quiet(px, py) and ground.free(px, py, radius, walker, off_road) and \
                all(math.hypot(px - tx, py - ty) >= radius + tr + gap for tx, ty, tr in taken)
        if ok(x, y):
            return x, y
        for ring in range(1, SEARCH_RINGS + 1):
            r = ring * SEARCH_STEP
            for a in np.linspace(0, 2 * math.pi, 8 + 4 * ring, endpoint=False):
                px, py = x + r * math.cos(a), y + r * math.sin(a)
                if ok(px, py):
                    moved.append((name, round(r)))
                    return px, py
        raise SystemExit(f'spawns.py: no room for {name} near {x:.0f}, {y:.0f}')

    # --- Spawn points -------------------------------------------------------------------------------------------
    spawns, placed_points = [], {}
    for entry in data['spawns']:
        slot = entry['slot']
        tiers = [entry['tier']] if entry.get('tier') else ['A', 'B', 'C']
        family = slots[slot]['picture'].lower()
        tier_ids = [pictures[f'{family} {t.lower()}'] for t in tiers if f'{family} {t.lower()}' in pictures]
        actor_radius = max(stage_monsters[i]['radius'] for i in tier_ids)
        ring = max(SPAWN_RADIUS, 96, 2 * actor_radius + 16)
        flier = all(rows[i][9] == 'Y' for i in tier_ids)
        if 'near' in entry:                             # a cluster's next point: an offset from an earlier one
            nx, ny = placed_points[entry['near']]
            x, y = nx + entry['offset'][0], ny + entry['offset'][1]
        else:
            x, y = place(*entry['at'])
        x, y = find(entry['name'], x, y, ring + actor_radius, walker=not flier, off_road=500)
        placed_points[entry['name']] = (x, y)
        z = height_at(x, y)
        spawns.append({'spawn_index': len(spawns), 'position': {'x': round(x), 'y': round(y), 'z': round(z)},
                       'radius': SPAWN_RADIUS, 'type_id': 3, 'index': encounter_index(slot, entry.get('tier')),
                       'attributes': 0, 'group': entry['group']})
        taken.append((x, y, ring + actor_radius))
        plan_spawns.append({'name': entry['name'], 'position': [round(x), round(y), round(z)], 'slot': slot,
                            'tier': entry.get('tier'), 'group': entry['group']})

    # --- Placed squads ------------------------------------------------------------------------------------------
    for entry in data['squads']:
        members = [int(monster) for monster, count in entry['monsters'].items() for _ in range(count)]
        ax, ay = place(*entry['at'])
        formation = entry.get('formation', 'cluster')
        face = entry.get('face')
        target = place(*face) if isinstance(face, list) else None
        heading = math.atan2(target[1] - ay, target[0] - ax) if target else 0.0
        spots = []
        for k, monster in enumerate(members):
            radius = stage_monsters[monster]['radius']
            if formation == 'line':                     # a staggered line across the heading
                across = (k - (len(members) - 1) / 2) * 260
                back = 120 * (k % 2)
                ox, oy = -math.sin(heading) * across - math.cos(heading) * back, \
                    math.cos(heading) * across - math.sin(heading) * back
            elif formation in ('ring', 'camp'):          # round the anchor, facing out
                r = 650 if formation == 'ring' else 900
                a = 2 * math.pi * k / len(members) + 0.3
                ox, oy = r * math.cos(a), r * math.sin(a)
            else:                                        # a loose cluster
                a = 2.4 * k
                r = 0 if k == 0 else 200 + 60 * k
                ox, oy = r * math.cos(a), r * math.sin(a)
            flier = rows[monster][9] == 'Y'
            x, y = find(f"{entry['name']} {k + 1}", ax + ox, ay + oy, radius, walker=not flier, gap=60)
            taken.append((x, y, radius))
            if face == 'out':
                facing = math.degrees(math.atan2(y - ay, x - ax))
            elif target:
                facing = math.degrees(heading)
            else:
                facing = (137.5 * k) % 360
            row = rows[monster]
            z = height_at(x, y)
            actors.append({'actor_index': len(actors), 'name': '', 'npc_id': 0, 'attributes': 0, 'hp': int(row[4]),
                           'hostility_type': int(row[12]), 'monster_info_id': monster, 'monster_id': monster,
                           'radius': radius, 'height': stage_monsters[monster]['height'], 'move_speed': int(row[13]),
                           'position': {'x': round(x), 'y': round(y), 'z': round(z)},
                           'initial_yaw_units': int(round((facing % 360) / 360 * 2048)) % 2048, 'immobile': False,
                           'sprite_ids': [0, 0, 0, 0], 'sector_id': 0, 'current_action_animation': 0,
                           'carried_item_id': 0, 'group': entry['group'], 'ally': 0, 'unique_name_index': 0})
            spots.append([round(x), round(y), round(z), monster])
        plan_squads.append({'name': entry['name'], 'group': entry['group'], 'actors': spots})

    # --- The load event: the quest gates (relations are the world's relations.yml, hesper_stage) -----------------
    body = []
    for gate in data['hide_after_qbit']:
        body.append(f'if IsQBitSet(QBit({gate["qbit"]})) then '
                    f'evt.SetMonGroupBit({gate["group"]}, ActorAttribute.Invisible, 1) end')

    # The staged monsters whose faction (the stage's relations.yml) is hostile to the party, as the plan reports them.
    relations = yaml.safe_load((STAGE_DATA / 'relations.yml').read_text())
    hostile_factions = {name for rule in relations['relations']
                        if rule['to'] == 'party' and rule['relation'] != 'friendly'
                        for name in ([rule['from']] if isinstance(rule['from'], str) else rule['from'])}

    def faction_ids(name):
        for item in relations['factions'][name]['monsters']:
            first, _, last = str(item).partition('-')
            yield from range(int(first), int(last or first) + 1)
    hostile_ids = sorted(m for m in stage_monsters if any(m in faction_ids(f) for f in hostile_factions))
    expected = sum((slots[s['slot']]['count'][0] + slots[s['slot']]['count'][1]) / 2 for s in plan_spawns)
    placed = sum(len(s['actors']) for s in plan_squads)
    plan = {'slots': {str(k): v for k, v in slots.items()}, 'refill_days': next(
                m for m in stage_maps if m['file'] == 'hes_out1.odm').get('refill_days', 672),
            'hostile_monsters': hostile_ids, 'spawns': plan_spawns, 'squads': plan_squads, 'moved': moved,
            'expected_first_visit': round(expected + placed), 'placed': placed, 'features': features}
    (PROJECT / 'work').mkdir(exist_ok=True)
    (PROJECT / 'work/spawns_plan.json').write_text(json.dumps(plan, indent=1) + '\n')
    return {'spawns': spawns, 'load_event': ('Starport Reach monsters on load', ' '.join(body)),
            'summary': {'spawn_points': len(spawns), 'placed': placed, 'expected_first_visit': plan[
                'expected_first_visit'], 'moved': moved}}
