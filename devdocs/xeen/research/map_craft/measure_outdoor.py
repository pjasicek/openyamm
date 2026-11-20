#!/usr/bin/env python3
"""Read-only POI/encounter census of all MM6-MM8 outdoor maps (scratch analysis)."""
import json, re, sys, math, csv
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file

DT = ROOT / 'assets_dev/engine/data_tables'
SUMMARY = {(r['world'], r['map']): r for r in csv.DictReader(open(ROOT / 'level_generation/catalogues/outdoor_decorations/map_summary.csv'))}

def table(name, skip):
    rows = [l.split('\t') for l in (DT / name).read_text(encoding='latin-1').splitlines()[skip:]]
    return rows

MONSTERS = {}
for r in table('monster_data.txt', 3):
    if r and r[0].strip().isdigit():
        MONSTERS[int(r[0])] = r[1]
HOUSES = {}
for r in table('house_data.txt', 2):
    if r and r[0].strip().isdigit():
        HOUSES[int(r[0])] = (r[2], r[5])

def mapStats(filename):
    for line in (DT / 'map_stats.txt').read_text(encoding='latin-1').splitlines():
        row = line.split('\t')
        if len(row) > 28 and row[2].lower() == filename.lower():
            enc = []
            for i in range(3):
                cnt = row[19 + 4 * i].strip()
                m = re.match(r'(\d+)\s*-\s*(\d+)', cnt)
                lo, hi = (int(m[1]), int(m[2])) if m else ((int(cnt), int(cnt)) if cnt.isdigit() else (0, 0))
                enc.append({'name': row[17 + 4 * i], 'lo': lo, 'hi': hi, 'diff': row[18 + 4 * i]})
            return {'name': row[1], 'enc': enc, 'chance': row[12], 'treasure': row[11]}
    return None

def terrainRows(world):
    fn = {'mm6': 'terrain_tile_data_3.txt', 'mm7': 'terrain_tile_data_2.txt', 'mm8': 'terrain_tile_data.txt'}[world]
    return [l.split('\t') for l in (DT / fn).read_text().splitlines()[1:]]

def tileInfo(p, world, rows, tile):
    if tile >= 234:
        return ('pending', 0)
    if tile >= 90:
        idx = p['tile_set_lookup_indices'][(tile - 90) // 36] + (tile - 90) % 36
    else:
        idx = tile + ([0, 450, 630][p['master_tile']] if world == 'mm8' and tile else 0)
    r = rows[idx]
    return (r[1].lower(), int(r[6], 0))

def luaEvents(path):
    text = path.read_text(encoding='latin-1')
    kinds = {int(m[1]): m[2] for m in re.finditer(r'\[(\d+)\] = \{ kind = "(\w+)"', text)}
    ev = {}
    regs = list(re.finditer(r'^Register(?:NoOp)?Event\((\d+),\s*(?:"([^"]*)"|nil)', text, re.M))
    names = {int(m[1]): m[2] for m in re.finditer(r'\[(\d+)\] = \{ kind = "\w+",[^\n]*?targetName = "([^"]*)"', text)}
    for i, m in enumerate(regs):
        block = text[m.start(): regs[i + 1].start() if i + 1 < len(regs) else len(text)]
        eid = int(m[1])
        e = ev.setdefault(eid, {'hint': m[2] or names.get(int(m[1]), ''), 'calls': set(), 'houses': set(), 'dest': set(), 'block': ''})
        if (m[2] or names.get(eid)) and not e['hint']:
            e['hint'] = m[2] or names.get(eid)
        e['calls'] |= set(re.findall(r'evt\.(\w+)\(', block))
        e['houses'] |= set(map(int, re.findall(r'evt\.EnterHouse\((\d+)', block)))
        e['dest'] |= set(x.lower() for x in re.findall(r'"([^"\n]+\.(?:blv|odm))"', block))
        e['block'] += block
        e['kind'] = kinds.get(eid, '')
    return ev

HINT_RULES = [
    ('fountain', r'fountain'), ('well', r'\bwell\b'), ('shrine', r'shrine|altar'), ('obelisk', r'obelisk'),
    ('pedestal', r'pedestal'), ('barrel', r'barrel|keg'), ('cauldron', r'cauldron'), ('campfire', r'campfire|fire\b'),
    ('sign', r'\bsign|signpost|post\b'), ('statue', r'statue'), ('tree', r'\btree'), ('stone', r'stone|rock|boulder|menhir'),
    ('boat/ship', r'boat|ship|wreck'), ('grave', r'grave|tomb|crypt|coffin|sarcophag'), ('chest', r'chest|crate|box|cask'),
    ('door/gate', r'\bdoor|gate|portcullis'), ('teleporter', r'teleport|portal|pad\b'), ('lever', r'lever|switch|button'),
    ('trough/cart', r'trough|cart|wagon'), ('hut/tent', r'tent|hut\b'), ('library/book', r'book|library|tome'),
]

def classify(e, binder):
    hint = (e.get('hint') or '').lower()
    kind = e.get('kind', '')
    calls = e.get('calls', set())
    if e.get('houses'):
        hid = sorted(e['houses'])[0]
        htype = HOUSES.get(hid, ('?', ''))[0]
        if htype == 'House':
            return 'residence'
        if htype in ('Dungeon Ent', 'Castle Entrance'):
            return 'dungeon_entrance'
        return 'service:' + htype
    if 'OpenChest' in calls:
        return 'chest'
    if e.get('dest'):
        dest = sorted(e['dest'])[0]
        return 'dungeon_entrance' if dest.endswith('.blv') else 'map_exit'
    if kind == 'enter_dungeon':
        return 'dungeon_entrance'
    if kind in ('fountain', 'well', 'shrine', 'obelisk'):
        return kind
    if kind == 'travel':
        return 'map_exit'
    for name, rx in HINT_RULES:
        if re.search(rx, hint):
            return name
    if 'SetSprite' in calls and binder.startswith('deco'):
        return 'deco_interactive'
    return 'other' if hint else 'unnamed'

def components(pts, radius):
    n = len(pts)
    parent = list(range(n))
    def f(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if np.hypot(*(pts[i][:2] - pts[j][:2])) <= radius:
                parent[f(i)] = f(j)
    groups = defaultdict(list)
    for i in range(n):
        groups[f(i)].append(i)
    return list(groups.values())

def nnDist(pts):
    if len(pts) < 2:
        return []
    a = np.asarray(pts)[:, :2]
    d = np.hypot(a[:, None, 0] - a[None, :, 0], a[:, None, 1] - a[None, :, 1])
    np.fill_diagonal(d, np.inf)
    return d.min(axis=1)

TOWNFOLK = re.compile(r'peasant|guard|villager|farmer|merchant|noble|citizen|townsfolk|child|man\b|woman|apprentice|'
                      r'priest|monk|cleric|soldier|archer|knight|sailor|pirate|fisher|crier|beggar|servant|elder', re.I)

def quart(v):
    if len(v) == 0:
        return None
    return [int(np.percentile(v, q)) for q in (25, 50, 75)]

out = []
for (world, mapname), summ in sorted(SUMMARY.items()):
    stem = mapname[:-4]
    mp = ROOT / 'assets_dev/worlds' / world / 'maps' / mapname
    sp = mp.with_suffix('.scene.yml')
    lp = ROOT / 'assets_dev/worlds' / world / 'events/maps' / (stem + '.lua')
    p = parse_odm_file(mp)['payload']
    scene = yaml.load(sp.read_text(), Loader=yaml.CSafeLoader)
    ev = luaEvents(lp) if lp.exists() else {}
    for ov in sorted(lp.parent.glob(stem + '_*.lua')):
        for k, v in luaEvents(ov).items():
            ev.setdefault(k, v)
    rows = terrainRows(world)
    tiles = Counter(p['tile_map'])
    info = {t: tileInfo(p, world, rows, t) for t in tiles}
    water = sum(c for t, c in tiles.items() if info[t][1] & 2 and not info[t][1] & 0x100)
    shore = sum(c for t, c in tiles.items() if info[t][1] & 0x100)
    burn = sum(c for t, c in tiles.items() if info[t][1] & 1)
    road = sum(c for t, c in tiles.items() if 198 <= t < 234)
    total = 128 * 128
    land = total - water
    families = [rows[i][1].lower() if i < len(rows) else '?' for i in p['tile_set_lookup_indices']]
    hm = np.array(p['height_map']).reshape(128, 128) * 32
    # bound events and positions
    binds = defaultdict(list)
    for m in p['bmodels']:
        for f in m['faces']:
            eid = f['cog_triggered_number']
            if eid:
                v = np.array([[m['vertices'][i][a] for a in 'xyz'] for i in f['vertex_indices']]).mean(axis=0)
                binds[eid].append(('face:' + m['name'], v))
    for e in p['entities']:
        pos = np.array([e['position'][a] for a in 'xyz'], float)
        for eid in (e['event_id_secondary'],):
            if eid:
                binds[eid].append(('deco:' + e['name'], pos))
    pois = []
    for eid, lst in binds.items():
        e = ev.get(eid, {})
        binder = lst[0][0]
        c = classify(e, binder)
        pos = np.mean([x[1] for x in lst], axis=0)
        pois.append({'id': eid, 'class': c, 'hint': e.get('hint', ''), 'binder': binder, 'pos': pos})
    def norm(h):
        return re.sub(r'^(enter|enter the|to|exit to|leave)\s+', '', (h or '').lower()).strip()
    known = {}
    for x in pois:
        if x['class'] not in ('other', 'unnamed') and x['hint']:
            known.setdefault(norm(x['hint']), x['class'])
    for x in pois:
        if x['class'] in ('other', 'unnamed') and norm(x['hint']) in known:
            x['class'] = known[norm(x['hint'])]
    # dedupe same class+hint within 600 units (hover/click event pairs, multi-face doors)
    ded = []
    for x in pois:
        if any(y['class'] == x['class'] and norm(y['hint']) == norm(x['hint']) and np.hypot(*(y['pos'][:2]-x['pos'][:2])) < 600 for y in ded):
            continue
        ded.append(x)
    pois = ded
    # interactive decorations without events (native rules): pedestals/barrels/challenges/food trees
    decoNames = Counter(e['name'].lower() for e in p['entities'])
    nativeInteractive = {}
    for e in p['entities']:
        n = e['name'].lower()
        tag = None
        if re.match(r'dec(4[4-9]|5[0-5])$', n): tag = 'buff_pedestal'
        elif re.match(r'dec4[0-3]$', n): tag = 'stat_challenge'
        elif n == 'dec03' or 'barel' in n or n in ('7dec01', '7dec03'): tag = 'barrel'
        elif n in ('dec26',): tag = 'cauldron'
        elif n.startswith('ped'): tag = 'pedestal'
        elif n in ('swrdstn',): tag = 'sword_in_stone'
        elif n in ('6tree06', 'tree06a', 'plant34'): tag = 'food_tree'
        elif n in ('ckfyr00', 'cmpfyr00', 'dec24', 'dec25', 'dec24x', '7dec02', 'dec06', 'dec04'): tag = 'campfire'
        elif n in ('shp',): tag = 'ship'
        elif n in ('dec30', '7dec33'): tag = 'signpost'
        if tag:
            nativeInteractive.setdefault(tag, []).append(np.array([e['position'][a] for a in 'xyz'], float))
    starts = [np.array([e['position'][a] for a in 'xyz'], float) for e in p['entities']
              if e['name'].lower() in ('party start', 'north start', 'south start', 'east start', 'west start')]
    ms = mapStats(mapname)
    spawnPts = []
    spawnSlots = Counter()
    exp = 0.0
    for s in p['spawns']:
        if s['type_id'] != 3:
            continue
        idx = s['spawn_index']
        slot = idx if 1 <= idx <= 3 else ((idx - 4) % 3 + 1 if 4 <= idx <= 12 else 0)
        if slot == 0:
            continue
        spawnSlots[slot] += 1
        enc = ms['enc'][slot - 1] if ms else None
        if enc and enc['hi'] > 0:
            exp += (enc['lo'] + enc['hi']) / 2
        spawnPts.append(np.array([s['position'][a] for a in 'xyz'], float))
    itemSpawns = sum(1 for s in p['spawns'] if s['type_id'] == 2)
    actors = scene['initial_state']['actors']
    hostileActs, townActs, hiddenActs = [], [], 0
    for a in actors:
        nm = MONSTERS.get(a['monster_info_id'], '?')
        pos = np.array([a['position'][k] for k in 'xyz'], float)
        if a['attributes'] & 0x10000 or a['attributes'] & 0x8:  # rough hidden/invisible guess
            hiddenActs += 1
        if TOWNFOLK.search(nm) or a.get('npc_id'):
            townActs.append(pos)
        else:
            hostileActs.append(pos)
    hostilePts = spawnPts + hostileActs
    groups = components(hostilePts, 1600) if hostilePts else []
    gcent = [np.mean([hostilePts[i] for i in g], axis=0) for g in groups]
    servicePts = [x['pos'] for x in pois if x['class'].startswith('service:')]
    def distTo(pt, pts):
        return min((float(np.hypot(*(pt[:2] - q[:2]))) for q in pts), default=None)
    startFight = [distTo(s, hostilePts) for s in starts] if hostilePts else []
    startTown = [distTo(s, servicePts) for s in starts] if servicePts else []
    cls = Counter(x['class'] for x in pois)
    # unique-POI set for spacing: everything except residences and map exits; collapse same-class within 300
    poiPts = [x['pos'] for x in pois if x['class'] not in ('residence', 'map_exit', 'unnamed', 'other')]
    for tag in ('buff_pedestal', 'stat_challenge', 'pedestal', 'sword_in_stone', 'campfire', 'ship', 'cauldron'):
        poiPts += nativeInteractive.get(tag, [])
    merged = [np.mean([poiPts[i] for i in g], axis=0) for g in components(poiPts, 400)] if poiPts else []
    landBlocks = land / 64.0  # 4096x4096 blocks of land
    out.append({
        'world': world, 'map': stem, 'name': summ['name'], 'biome': summ['biome'],
        'tilesets': families, 'water_pct': round(100 * water / total, 1), 'shore_pct': round(100 * shore / total, 1),
        'burn_pct': round(100 * burn / total, 1), 'road_pct_land': round(100 * road / max(1, land), 1),
        'height_max': int(hm.max()), 'height_p90_land': int(np.percentile(hm, 90)),
        'land_blocks4096': round(landBlocks, 1),
        'deco_visible': int(summ['visible']), 'deco_per_block': summ['per_4096_square'],
        'trees': int(summ['trees']), 'rocks': int(summ['rocks']), 'flowers_plants': int(summ['flowers']) + int(summ['plants']),
        'dry': int(summ['dry_plants']), 'deadwood': int(summ['deadwood']), 'remains': int(summ['remains']),
        'ritual': int(summ['ritual']), 'working': int(summ['working_props']), 'fires': int(summ['fire_lights']),
        'bmodels': len(p['bmodels']),
        'poi_classes': dict(cls), 'native_interactive': {k: len(v) for k, v in nativeInteractive.items()},
        'pois_merged': len(merged), 'poi_nn': quart(nnDist(merged)),
        'pois_per_block': round(len(merged) / max(1, landBlocks), 2),
        'chests_scene': len(scene['initial_state']['chests']), 'loose_items': len(scene['initial_state']['sprite_objects']),
        'item_spawns': itemSpawns,
        'spawn_markers': len(spawnPts), 'spawn_slots': dict(spawnSlots), 'expected_spawned': round(exp, 1),
        'enc': [f"{e['name']} {e['lo']}-{e['hi']}" for e in ms['enc']] if ms else [],
        'hostile_fixed': len(hostileActs), 'town_actors': len(townActs),
        'hostile_groups_1600': len(groups), 'group_marker_sizes': quart([len(g) for g in groups]),
        'group_center_nn': quart(nnDist(gcent)),
        'start_to_fight': quart([d for d in startFight if d is not None]),
        'start_to_service': quart([d for d in startTown if d is not None]),
        'starts': len(starts),
        'hints_other': sorted(set(x['hint'] for x in pois if x['class'] in ('other',)))[:40],
    })
    print(stem, file=sys.stderr)

json.dump(out, open(Path(__file__).with_name('outdoor_census.json'), 'w'), indent=1, default=str)
