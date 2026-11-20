"""Author Brackenford's population, rewards and small reusable MM8 landmarks.

Coordinates are original design data. Monster/item definitions and landmark geometry are existing MM8 assets.
This module emits semantic source; the native writer and scene loader own runtime serialization.
"""
import csv
import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from configure_rewards import apply_reward_policy

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
SOURCE = PROJECT/'source'


def table(name):
    with (ROOT/'assets_dev/engine/data_tables'/name).open(encoding='cp1252', newline='') as stream:
        return {int(row[0]): row for row in csv.reader(stream, delimiter='\t') if row and row[0].isdigit()}


def terrain_height(x, y, samples):
    """Native rendered triangle split, matching sampleOutdoorRenderedTerrainHeight."""
    gx = x/512+64
    gy = 64-y/512
    c, r = math.floor(gx), math.floor(gy)
    assert 0 <= c < 127 and 0 <= r < 127
    u, v = gx-c, gy-r
    a, b, d, e = [samples[rr*128+cc]*32 for rr, cc in [(r,c), (r,c+1), (r+1,c), (r+1,c+1)]]
    return round(a+(b-a)*u+(d-a)*v if u+v <= 1 else e+(d-e)*(1-u)+(b-e)*(1-v))


def build(samples=None, semantics=None):
    if samples is None:
        samples = bytes.fromhex(json.loads((SOURCE/'lg01.terrain.yml').read_text())['height_map_hex'])
    if semantics is None:
        semantics = json.loads((SOURCE/'lg01.semantic.json').read_text())
    stats = table('monster_data.txt')
    descriptors = table('monster_descriptors.txt')
    items = table('items.txt')
    actors = []
    markers = []

    def point(x, y):
        return [x, y, terrain_height(x, y, samples)]

    def actor(identity, monster_id, xy, role, group, ally, hostile):
        entry, descriptor = stats[monster_id], descriptors[monster_id]
        position = point(*xy)
        index = len(actors)
        actors.append({'actor_index': index, 'name': entry[1].strip(), 'npc_id': 0,
            'attributes': 0x80000 if hostile else 0, 'hp': int(entry[4]),
            'hostility_type': int(entry[12]) if hostile else 0,
            'monster_info_id': monster_id, 'monster_id': monster_id,
            'radius': int(descriptor[3]), 'height': int(descriptor[2]), 'move_speed': int(entry[13]),
            'position': dict(zip('xyz', position)), 'sprite_ids': [0,0,0,0], 'sector_id': 0,
            'current_action_animation': 0, 'carried_item_id': 0, 'group': group, 'ally': ally,
            'unique_name_index': 0})
        markers.append({'id': identity, 'kind': 'fixed_actor', 'actor_index': index,
            'position': position, 'role': role, 'monster_id': monster_id, 'group': group, 'ally': ally})

    # Occupy the new shared streets, using geometry rather than the previous grid's fixed coordinates.
    plan=json.loads((PROJECT/'outdoor_plan.json').read_text())
    candidates=sorted({((c-64)*512+256,(64-r)*512-256) for route in semantics['roads']
        for r,c in route['cells'] if -19200<(c-64)*512+256<-5000 and -5600<(64-r)*512-256<6500})
    candidates=[xy for xy in candidates if not any(all(abs(xy[k]-b['xy'][k])<b['target_footprint'][k]/2+192
        for k in [0,1]) for b in semantics['buildings']) and not any(math.dist(xy,v['xy'])<900 for v in plan['landmarks'])]
    selected=[]
    for i in range(29):
        anchor=candidates[(i*17)%len(candidates)] if not selected else max(candidates,key=lambda xy:min(math.dist(xy,q) for q in selected))
        selected.append(anchor);candidates.remove(anchor)
    guard_points=selected[:9]
    for i, xy in enumerate(guard_points):
        # Same local ally type as Ravenshore's native guard records: Dark Elf Peasant Female, neutral to party.
        actor(f'guard_{i+1:02}', 27 if i in [2,5,8] else 26, xy, 'guard', 38, 8, False)
    villager_points = selected[9:]
    for i, xy in enumerate(villager_points):
        actor(f'villager_{i+1:02}', [22,23,19,20,166][i%5], xy, 'villager', 38, 8, False)
    # Regions come from the composition plan; variation fills each region, never the whole map.
    road_centers=[((c-64)*512+256,(64-r)*512-256) for route in semantics['roads'] for r,c in route['cells']]
    for pack_index, pack in enumerate(plan['encounters']):
        rng=random.Random(89107+pack_index*193)
        placed=[]
        for i, monster_id in enumerate(pack['monster_ids']):
            for attempt in range(300):
                if 'offsets' in pack:
                    dx,dy=pack['offsets'][i]
                else:
                    dx,dy=[rng.uniform(-1,1)*extent for extent in pack['extent']]
                    if (dx/pack['extent'][0])**2+(dy/pack['extent'][1])**2>1:continue
                x,y=[round(v/16)*16 for v in [pack['xy'][0]+dx,pack['xy'][1]+dy]]
                grade=math.hypot(terrain_height(x+32,y,samples)-terrain_height(x-32,y,samples),
                                 terrain_height(x,y+32,samples)-terrain_height(x,y-32,samples))/64
                if grade>.55:continue
                if any(math.dist((x,y),other)<224 for other in placed):continue
                if 'offsets' not in pack and any(math.dist((x,y),q)<480 for q in road_centers):continue
                placed.append((x,y))
                actor(f"{pack['id']}_{i+1:02}",monster_id,(x,y),pack['id'],10+pack_index,pack['ally'],True)
                break
            else:
                raise AssertionError(('No valid encounter placement',pack['id'],i))
    # Every town member is mutually neutral. Do not edit global relations to achieve local placement requirements.
    with (ROOT/'assets_dev/engine/data_tables/hostile.txt').open(encoding='cp1252', newline='') as stream:
        relations = list(csv.reader(stream, delimiter='\t'))
    assert relations[1][9] == '0' and relations[9][9] == '0'
    town_positions = [a['position'] for a in markers if a['role'] in ['guard','villager']]
    town_positions += [h['door_position'] for h in semantics['buildings']]
    # Include occupied perimeter corners, beyond individual residents/doors.
    town_positions += [[x,y,0] for x in [-19456,-1536] for y in [-9216,9728]]
    minimum = min(math.dist(a['position'][:2], p[:2]) for a in markers
                  if a['role'] not in ['guard','villager'] for p in town_positions)
    assert minimum >= 8192, minimum
    for marker, runtime in zip(markers[:29], actors[:29]):
        x,y,_ = marker['position']
        for house in semantics['buildings']:
            hx,hy = house['xy']; w,d = house['target_footprint']
            radius = runtime['radius']+32
            assert abs(x-hx)>w/2+radius or abs(y-hy)>d/2+radius, (marker['id'],house['id'])

    containers = []
    world_items = []
    landmarks = []
    for site, cx, cy, item_ids in [('east_cache',21504,3584,[5,95,145]),
                                  ('south_cache',10240,-22528,[15,65])]:
        for side in [-1,1]:
            index = len(containers)
            # Retain event 204/container 3 identity while moving the former second southern chest to the den.
            position = point(14848,-18432) if index==3 else point(cx+side*256,cy)
            identity = f'{site}_chest_{1 if side<0 else 2}'
            containers.append({'source_id': 'mm8:brackenford:'+identity, 'source_object_index': index,
                'source_name': identity, 'position': dict(zip('xyz',position)), 'container_id': index,
                'kind': 'chest', 'presentation': 'wooden chest', 'random_treasure_level': 6,
                'treasure_type': 0, 'gold': 1500+index*250, 'gold_only': False, 'random': True,
                'ai_drop': False, 'trap_level': 1, 'should_repopulate': True,
                'fixed_items': [], 'remove_when_empty': False})
            landmarks.append({'id': identity, 'kind': 'chest_target', 'position': position,
                'event_id': 201+index, 'container_id': index,
                'reuse_map': 'out02.odm', 'reuse_bmodel': 1})
        for i, item_id in enumerate(item_ids):
            assert (ROOT/'assets_dev/engine/icons'/(items[item_id][1]+'.bmp')).is_file()
            position = point(cx+(i-1)*160,cy-224)
            index = len(world_items)
            item = {'source_id': f'mm8:brackenford:{site}:loose_{i+1}', 'source_object_index': index,
                'source_name': items[item_id][2], 'position': dict(zip('xyz',position)),
                'item_id': item_id, 'pickup_event': 0}
            for key in ['random_item_pool','required_qbits','forbidden_qbits','pickup_qbits','set_qbits']:
                item[key] = []
            world_items.append(item)
    landmarks += [
        {'id': 'obelisk', 'kind': 'obelisk', 'position': point(-18432,15360), 'event_id': 301,
         'reuse_map': 'out02.odm', 'reuse_bmodel': 65},
        {'id': 'town_well', 'kind': 'well', 'position': point(*next(p['xy'] for p in json.loads((PROJECT/'outdoor_plan.json').read_text())['landmarks'] if p['id']=='well')), 'event_id': 302,
         'reuse_map': 'out02.odm', 'reuse_bmodel': 6},
    ]
    for identity,event_id,kind,models in [('well_south',303,'well',[6]),('fountain',304,'fountain',[83,84])]:
        xy=next(v['xy'] for v in plan['landmarks'] if v['id']==identity)
        landmarks.append(dict(id=identity,kind=kind,position=point(*xy),event_id=event_id,reuse_map='out02.odm',reuse_bmodels=models))
    # Reserve a clear road corridor around the complete native 256x256 well plus 128 units.
    road_centers={((c-64)*512+256,(64-r)*512-256)
                  for road in semantics['roads'] for r,c in road['cells']}
    well=next(p for p in landmarks if p['kind']=='well')
    wx,wy=well['position'][:2]
    assert not any(abs(wx-rx)<512 and abs(wy-ry)<512 for rx,ry in road_centers), 'Well obstructs road clearance'
    for runtime in actors:
        for prop in landmarks:
            distance = math.dist([runtime['position'][k] for k in 'xy'], prop['position'][:2])
            prop_radius = 160 if prop['kind'] == 'well' else 80
            assert distance >= runtime['radius']+prop_radius, (runtime['actor_index'],prop['id'])
    apply_reward_policy('lg01.odm', containers)
    result = {'format_version': 1, 'actors': actors, 'markers': markers,
        'loot_containers': containers, 'world_items': world_items, 'landmarks': landmarks,
        'provenance': {
            'monsters': {str(i): stats[i][1:3] for i in sorted({a['monster_id'] for a in actors})},
            'items': {str(i): items[i][1:4] for i in sorted({a['item_id'] for a in world_items})},
            'original_landmark_map_sha256': hashlib.sha256(
                (ROOT/'assets_dev/worlds/mm8/maps/out02.odm').read_bytes()).hexdigest()},
        'town_wilderness_initial_minimum_xy': round(minimum,2),
        'spawn_policy': f'{len(actors)} fixed actors in town and {len(plan["encounters"])} authored wilderness areas; zero encounter spawns; rest encounter chance zero',
        'encounter_areas': plan['encounters'],
        'well_policy': 'Existing MM8 +25 temporary Might on selected character when bonus <25; no stacking. '
                       'Available again after normal temporary-bonus reset; no campaign autonote or QBit.',
        'obelisk_policy': 'Existing ethesunsh inscription; local MapVar(11) discovery only; repeat readable.',
        'validation_status': 'Existing behavior retained; native wiring and visual placement review required'}
    (SOURCE/'lg01.content.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'actors':len(actors),'town':29,'hostiles':len(actors)-29,'encounter_areas':len(plan['encounters']),'chests':4,'loose_items':5,
                      'minimum_town_distance':minimum}))
    return result


def apply_to_scene(scene):
    content = json.loads((SOURCE/'lg01.content.json').read_text())
    scene['initial_state']['actors'] = content['actors']
    scene['loot_containers'] = content['loot_containers']
    scene['world_items'] = content['world_items']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh-scene', action='store_true',
                        help='Regenerate gameplay companion after a content-only edit; leaves native geometry intact')
    args = parser.parse_args()
    build()
    if args.refresh_scene:
        scene = json.loads((SOURCE/'lg01.scene.yml').read_text())
        apply_to_scene(scene)
        data = json.dumps(scene,indent=2)+'\n'
        (SOURCE/'lg01.scene.yml').write_text(data)
        (PROJECT/'runtime/worlds/mm8/maps/lg01.scene.yml').write_text(data)
        semantics = json.loads((SOURCE/'lg01.semantic.json').read_text())
        content = json.loads((SOURCE/'lg01.content.json').read_text())
        semantics['loose_items'] = content['world_items']
        semantics['fixed_actors'] = content['markers']
        (SOURCE/'lg01.semantic.json').write_text(json.dumps(semantics,indent=2)+'\n')
