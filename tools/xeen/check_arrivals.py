#!/usr/bin/env python3
"""Indoor arrival check (F45 of reviews/PLAYER_FEEDBACK_20261124.md, "arrivals in the thick of it"): every point the
party lands on in a Xeen indoor map against the map's hostile monsters and its way out.

  tools/xeen/check_arrivals.py [--all] [--maps xeen_xd24 xeen_dd01 ...] [--json] [--assets ROOT]
      (default --all: every xeen_*.blv with a scene; run whole-world checks through tools/heavy.sh 4)

Arrival points, deduplicated within 128 (labels merged):
- the scene's party start (`party_start_points`, written from the L4 `objects.yml` `start:`);
- every evt.MoveToMap into the map in any installed Xeen map Lua or events/common Lua (another map's exit, a fall, a
  teleport), and the map's own moves inside itself; a move to (0, 0, 0) is the party start;
- Lua table rows {x, y, z, yaw, "<map>"} (sky falls and similar), coaches/docks (transport_locations), mirrors,
  Town Portal points and edge spans that name the map.

Hostile monsters: the scene's placed actors that are not talking NPCs and not hidden (EvtActorAttribute Invisible
0x10000), and that are hostile on a first visit: the Aggressor bit 0x80000, or a relation to the party > 0 in
worlds/xeen/relations.yml (rules without a qbit condition) or, for MM monster ids, the party row of engine hostile.txt.
Monster spawn markers count as well (D-133, 2026-11-24): the BLV's own markers (type 3, the L4's `spawns`, as the
export lists them) and the scene's `spawns`, each spread over its radius; a marker counts by any monster row its slot
can roll (slots 1-3 any tier, 4-12 a fixed tier), with the widest notice range of those rows.

Their notice range is the engine's (game/indoor/IndoorWorldRuntime.cpp): an unaware monster notices the party when it is
within IndoorActorDetectRange 5,120 (3D) AND it has a clear line through the portals to the party (its eye at 0.9 of
its height to the party's eye at +160, or its chest at 0.75 to the party's body at +96); a non-aggressor's range is cut
to its relation's (close 1,024, short 2,560, medium 5,120, long = the 10,240 engagement range, so 5,120). 5,120 is also
D-85's monster missile range (GameplayActorAiSystem): a monster that notices the party at that range fires at once.
Line of sight here: the straight segment against every solid face of the built BLV (oymap export; portals, Invisible
faces skipped; door leaves where the scene's initial state puts them), the same faces the engine's portal trace and
indoorSegmentBlockedByCombatFace test.

Rules:
- `arrival.hot` (error): a hostile monster within its notice range of the arrival with a clear line to it: it notices
  the party on the first AI steps after the load (eight sight checks a second), and wakes its own group (128).
- `arrival.hot_within` (warning): the same for a landing only the map's own moves reach (a teleport or trap inside
  the dungeon, where a fight may be meant).
- `arrival.near` (warning): a hostile within 1,024 (HostilityCloseRange, one plan cell pair) with no line: it is round
  the first corner or behind the first door.
- `arrival.deep` (warning): an arrival from another map lands more than 768 (3D) from the nearest face of this map's
  exit back to that map, or cannot see it: the party lands inside instead of at the stairs it came down. Moves within
  the map and table arrivals are not measured. The party start is measured against the nearest exit of any kind.
  A door leaf (a rock fall, a gate) between the arrival and its exit does not count against sight of it.

Open-air maps (D-122, 2026-11-24: D7, P1-P4 and X8, BLVs under the sky) take the outdoor rules instead of
`arrival.hot`, as the outdoor maps' D-15 and D-87 (level_generation/projects/xeen/common/d85.py):
- `arrival.open_hot` (error): an aggressive monster that can move or shoot (not `immobile`, or a row with a missile
  or a spell) within 2,000 (2D) of the arrival with a clear line (D-15's first-fight buffer).
- `arrival.disabler` (error): a ranged disabler (d85.py's kinds: Stone, Curse, Paralyze, Asleep, Insane, Afraid,
  Uncon, Dead or Errad on an attack with a missile, or a Paralyze / Finger of Death spell; a spawn marker counts if
  any row its slot can roll is one) within 5,888 (2D) of the arrival, line or not (D-87).
- `arrival.open_seen` (warning): what `arrival.hot` would have said (seen within the notice range), for the record.
Moving the landing out of sight (behind a wall) is not a fix on these maps: the monsters move.

Each flagged arrival names where it is defined (the source Lua event; and every brief/generator file that spells its
x, y). Exit 1 on an error.
"""
import argparse
import glob
import json
import math
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
Loader = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
OYMAP = os.path.join(ROOT, 'openyamm-studio', 'build-xeen', 'oymap')

DETECT = 5120.0
# D-122: open-air maps take the outdoor arrival rules (D-15's 2,000 buffer, D-87's 5,888 for ranged disablers).
OPEN_AIR = {'xeen_d7', 'xeen_p1', 'xeen_p2', 'xeen_p3', 'xeen_p4', 'xeen_x8'}
OPEN_BUFFER = 2000.0
DISABLER_RANGE = 5888.0
DIS_BONUS = {'stone', 'curse', 'paralyze', 'asleep', 'insane', 'afraid', 'uncon', 'dead', 'errad'}
DIS_SPELL = {'paralyze', 'finger of death'}
RELATION_RANGE = {0: 0.0, 1: 1024.0, 2: 2560.0, 3: 5120.0, 4: DETECT}
RELATION_NAMES = {'friendly': 0, 'close': 1, 'short': 2, 'medium': 3, 'long': 4}
NEAR = 1024.0
DEEP = 768.0
MERGE = 128.0
PARTY_EYE, PARTY_BODY = 160.0, 96.0
AGGRESSOR, INVISIBLE_ACTOR = 0x80000, 0x10000
FACE_PORTAL, FACE_INVISIBLE = 0x1, 0x2000

MOVE = re.compile(r'evt\.MoveToMap\(\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,[^()"]*?'
                  r'(?:"([^"]*)")?\s*(?:,\s*\{[^}]*\})?\s*\)')
TABLE_ROW = re.compile(r'\{\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*"(xeen_\w+\.(?:blv|odm))"\s*\}')
EVENT = re.compile(r'RegisterEvent\(\s*(\d+)\s*,')


def load_yaml(path):
    try:
        with open(path) as f:
            return yaml.load(f, Loader=Loader) or {}
    except FileNotFoundError:
        return {}


def tsv(path):
    for line in open(path, encoding='utf-8', errors='replace'):
        if not line.startswith('#'):
            yield line.rstrip('\n').split('\t')


class World:
    def __init__(self, assets):
        self.assets = assets
        self.xeen = os.path.join(assets, 'worlds', 'xeen')
        self.tables = os.path.join(self.xeen, 'data_tables')
        self.names = {}
        self.rows = {}
        for f in list(tsv(os.path.join(assets, 'engine', 'data_tables', 'monster_data.txt'))) + \
                list(tsv(os.path.join(self.tables, 'monster_data.txt'))):
            if len(f) > 2 and f[0].strip().isdigit():
                self.names[int(f[0])] = f[1]
                self.rows[int(f[0])] = f
        self.by_picture = {}
        for mid, f in sorted(self.rows.items()):
            self.by_picture.setdefault(f[2], mid)
        self.slots = {}   # map file -> [picture of slots 1-3]
        for f in tsv(os.path.join(self.tables, 'map_stats.txt')):
            if len(f) > 28 and f[0].strip().isdigit():
                self.slots[f[2].strip()] = [f[16 + 4 * k] for k in range(3)]
        self.relation = self._relations()
        self.party_row = []
        rows = list(tsv(os.path.join(assets, 'engine', 'data_tables', 'hostile.txt')))
        if len(rows) > 1:
            self.party_row = rows[1][1:]
        self.map_ids = {}
        for f in tsv(os.path.join(self.tables, 'map_stats.txt')):
            if len(f) > 2 and f[0].strip().isdigit():
                self.map_ids[f[2].strip()] = int(f[0])
        self.luas = {}
        for path in sorted(glob.glob(os.path.join(self.xeen, 'events', 'maps', '*.lua'))) + \
                sorted(glob.glob(os.path.join(self.xeen, 'events', 'common', '*.lua'))):
            self.luas[path] = open(path, encoding='utf-8', errors='replace').read()
        self.sources = {}
        patterns = ['devdocs/xeen/briefs/*/L4/*.yml', 'devdocs/xeen/briefs/*/*.md', 'devdocs/xeen/briefs/*/*.yml',
                    'level_generation/projects/xeen/**/*.py', 'output/studio_cal/*/tools/gen.py']
        for pattern in patterns:
            for path in glob.glob(os.path.join(ROOT, pattern), recursive=True):
                try:
                    self.sources[os.path.relpath(path, ROOT)] = open(path, encoding='utf-8', errors='replace').read()
                except OSError:
                    pass

    def _relations(self):
        data = load_yaml(os.path.join(self.xeen, 'relations.yml'))
        faction_of = {}
        for name, entry in (data.get('factions') or {}).items():
            for item in entry.get('monsters') or []:
                lo, _, hi = str(item).partition('-')
                for mid in range(int(lo), int(hi or lo) + 1):
                    faction_of[mid] = name
        to_party = {}
        for rule in data.get('relations') or []:
            if rule.get('to') != 'party' or 'after_qbit' in rule or 'until_qbit' in rule:
                continue
            value = rule.get('relation')
            to_party[rule['from']] = RELATION_NAMES.get(value, value if isinstance(value, int) else 0)
        return {mid: to_party[f] for mid, f in faction_of.items() if f in to_party}

    def relation_to_party(self, mid):
        if mid in self.relation:
            return self.relation[mid]
        index = (mid - 1) // 3 + 1 if mid > 0 else 0
        if 0 <= index < len(self.party_row):   # hostile.txt: the Party row, its column 1 is relation index 0
            try:
                return int(self.party_row[index] or 0)
            except ValueError:
                return 0
        return 0

    def map_friendly(self, fname):
        """The rows the map's own Lua makes friendly to the party on every load (a sketch's `relations` toward the
        party, the studio's `evt:studio_relations`: `evt.SetMonsterRelation(row, 0, 0)` in an onLoad event), e.g. a
        town's villager rows that are hostile by the world tables (D4's Lakeside Druids, 2026-11-24)."""
        cache = self.__dict__.setdefault('_map_friendly', {})
        if fname not in cache:
            text = self.luas.get(os.path.join(self.xeen, 'events', 'maps', os.path.splitext(fname or '')[0] + '.lua'),
                                 '')
            on_load = re.search(r'onLoad = \{([^}]*)\}', text)
            ids = {int(x) for x in re.findall(r'\d+', on_load.group(1))} if on_load else set()
            blocks = events_of(text)
            cache[fname] = {int(m.group(1)) for eid in ids for m in
                            re.finditer(r'evt\.SetMonsterRelation\((\d+), 0, 0\)', blocks.get(eid, ''))}
        return cache[fname]

    def cell(self, mid, col):
        f = self.rows.get(mid)
        return f[col].strip().strip('"') if f and len(f) > col else ''

    def shoots(self, mid):
        """A row with a missile (either attack) or a spell."""
        return any(self.cell(mid, c) not in ('', '0') for c in (19, 23)) or \
            any(self.cell(mid, c).split(',')[0] not in ('', '0') for c in (25, 27))

    def disabler(self, mid):
        """D-87's ranged disabler: the reason, or ''."""
        bonus = re.sub(r'x\d+$', '', self.cell(mid, 16).lower())
        if bonus in DIS_BONUS and self.cell(mid, 19) not in ('', '0'):
            return '%s by %s missile' % (self.cell(mid, 16), self.cell(mid, 19))
        for col in (25, 27):
            spell = self.cell(mid, col).split(',')[0]
            if spell.lower() in DIS_SPELL:
                return '%s spell' % spell
        return ''

    def slot_rows(self, fname, index):
        """The rows a spawn marker of this index can roll (slots 1-3 any tier, 4-12 a fixed tier)."""
        if not 1 <= index <= 12 or fname not in self.slots:
            return []
        if index <= 3:
            slot, tiers = index, 'ABC'
        else:
            slot, tiers = (index - 4) % 3 + 1, 'ABC'[(index - 4) // 3]
        picture = self.slots[fname][slot - 1]
        if picture in ('', '0'):
            return []
        return [self.by_picture[picture + ' ' + t] for t in tiers if picture + ' ' + t in self.by_picture]

    def find_sources(self, x, y, stems):
        """The brief and generator lines of these maps that spell x, y."""
        pat = re.compile(r'(?<![\d.])%d\s*,\s*%d(?![\d.])' % (x, y))
        keys = [s[5:] if s.startswith('xeen_') else s for s in stems]
        out = []
        for rel, text in self.sources.items():
            if not any('/%s/' % k in rel for k in keys):
                continue
            for m in pat.finditer(text):
                line = text.count('\n', 0, m.start()) + 1
                out.append('%s:%d' % (rel, line))
        return out


def events_of(text):
    """event id -> its block of Lua text."""
    marks = [(0, 0)] + [(m.start(), int(m.group(1))) for m in EVENT.finditer(text)]
    blocks = {}
    for k, (start, eid) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(text)
        blocks[eid] = blocks.get(eid, '') + text[start:end]
    return blocks


def arrivals(world, stem, scene):
    fname = stem + '.blv'
    start = (scene.get('party_start_points') or [{}])[0]
    sp = start.get('position')
    pts = []
    if sp:
        pts.append({'label': 'party start', 'at': [float(v) for v in sp], 'facing_deg': start.get('direction_degrees'),
                    'from': None})
    own = os.path.join(world.xeen, 'events', 'maps', stem + '.lua')
    for path, text in world.luas.items():
        lstem = os.path.splitext(os.path.basename(path))[0]
        for eid, block in events_of(text).items():
            for m in MOVE.finditer(block):
                target = m.group(5)
                inside = path == own and (not target or target in ('0', fname))
                if target != fname and not inside:
                    continue
                x, y, z, d = (int(m.group(k)) for k in range(1, 5))
                if (x, y, z) == (0, 0, 0) and sp:
                    x, y, z = sp
                pts.append({'label': '%s %s event %d' % ('move within' if inside else 'MoveToMap in', lstem, eid),
                            'at': [float(x), float(y), float(z)], 'facing_deg': d * 360.0 / 2048.0,
                            'from': None if inside or 'common' in path else lstem})
        for m in TABLE_ROW.finditer(text):
            if m.group(5) == fname:
                pts.append({'label': 'Lua table row in %s' % lstem, 'at': [float(m.group(k)) for k in (1, 2, 3)],
                            'facing_deg': int(m.group(4)) * 360.0 / 2048.0, 'from': None})
    for f in tsv(os.path.join(world.tables, 'transport_locations.txt')):
        if len(f) > 12 and f[1].strip() == fname:
            pts.append({'label': 'transport %s' % f[0], 'at': [float(f[10]), float(f[11]), float(f[12])],
                        'facing_deg': None, 'from': None})
    for side in (load_yaml(os.path.join(world.tables, 'mirrors.yml')) or {}).values():
        for m in side or []:
            if isinstance(m, dict) and m.get('map') == fname and m.get('at'):
                at = list(m['at']) + [0] * (3 - len(m['at']))
                pts.append({'label': 'mirror %s' % m.get('town'), 'at': [float(v) for v in at[:3]],
                            'facing_deg': None, 'from': None})
    map_id = world.map_ids.get(fname)
    for f in tsv(os.path.join(world.tables, 'town_portal_switch.txt')):
        if len(f) > 5 and f[0].strip().isdigit() and f[1].strip().isdigit() and int(f[1]) == map_id:
            pts.append({'label': 'town portal row %s' % f[0], 'at': [float(f[2]), float(f[3]), float(f[4])],
                        'facing_deg': None, 'from': None})
    spans = load_yaml(os.path.join(world.tables, 'edge_spans.yml'))
    for s in spans.get('edge_spans') or []:
        if s.get('to_map') == fname and s.get('at'):
            at = list(s['at']) + [0] * (3 - len(s['at']))
            pts.append({'label': 'edge span from %s %s' % (s['map'], s['edge']), 'at': [float(v) for v in at[:3]],
                        'facing_deg': None, 'from': None})
    merged = []
    for p in pts:
        for e in merged:
            if math.dist(e['at'][:2], p['at'][:2]) < MERGE and abs(e['at'][2] - p['at'][2]) < 256:
                if p['label'] not in e['labels']:
                    e['labels'].append(p['label'])
                if p['from'] and p['from'] not in e['from']:
                    e['from'].append(p['from'])
                if e['facing_deg'] is None:
                    e['facing_deg'] = p['facing_deg']
                break
        else:
            merged.append({'labels': [p['label']], 'at': p['at'], 'facing_deg': p['facing_deg'],
                           'from': [p['from']] if p['from'] else []})
    return merged


class Geometry:
    def __init__(self, data):
        m = data['map']
        self.vertices = np.array(m['vertices'], float)
        self.faces = m['faces']
        polys, normals, ds, ids = [], [], [], []
        for i, f in enumerate(self.faces):
            if f.get('is_portal') or f['attributes'] & (FACE_PORTAL | FACE_INVISIBLE) or len(f['vertices']) < 3:
                continue
            p = self.vertices[f['vertices']]
            n = np.zeros(3)
            for a in range(len(p)):   # Newell's normal
                b = p[(a + 1) % len(p)]
                n += [(p[a][1] - b[1]) * (p[a][2] + b[2]), (p[a][2] - b[2]) * (p[a][0] + b[0]),
                      (p[a][0] - b[0]) * (p[a][1] + b[1])]
            ln = np.linalg.norm(n)
            if ln < 1e-6:
                continue
            n /= ln
            polys.append(p)
            normals.append(n)
            ds.append(float(n @ p.mean(0)))
            ids.append(i)
        self.polys, self.normals, self.ds, self.ids = polys, np.array(normals), np.array(ds), ids
        self.lo = np.array([p.min(0) for p in polys]) - 1
        self.hi = np.array([p.max(0) for p in polys]) + 1

    def blocked(self, a, b, skip=()):
        a, b = np.asarray(a, float), np.asarray(b, float)
        seg = b - a
        lo, hi = np.minimum(a, b), np.maximum(a, b)
        cand = np.nonzero(((self.hi >= lo) & (self.lo <= hi)).all(1))[0]
        if not len(cand):
            return False
        n = self.normals[cand]
        den = n @ seg
        num = self.ds[cand] - n @ a
        with np.errstate(divide='ignore', invalid='ignore'):
            t = num / den
        ok = (np.abs(den) > 1e-9) & (t > 1e-3) & (t < 1 - 1e-3)
        for k in np.nonzero(ok)[0]:
            fi = cand[k]
            if self.ids[fi] in skip:
                continue
            pt = a + seg * t[k]
            axis = int(np.argmax(np.abs(self.normals[fi])))
            i, j = [q for q in range(3) if q != axis]
            poly = self.polys[fi]
            x, y = pt[i], pt[j]
            inside = False
            for e in range(len(poly)):
                x1, y1, x2, y2 = poly[e][i], poly[e][j], poly[(e + 1) % len(poly)][i], poly[(e + 1) % len(poly)][j]
                if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                    inside = not inside
            if inside:
                return True
        return False

    def floor_below(self, p):
        """The highest floor-like face under p within 512 (z), or None."""
        best = None
        for fi, (poly, n) in enumerate(zip(self.polys, self.normals)):
            if n[2] < 0.5:
                continue
            if not (self.lo[fi][0] <= p[0] <= self.hi[fi][0] and self.lo[fi][1] <= p[1] <= self.hi[fi][1]):
                continue
            x, y = p[0], p[1]
            inside = False
            for e in range(len(poly)):
                x1, y1, x2, y2 = poly[e][0], poly[e][1], poly[(e + 1) % len(poly)][0], poly[(e + 1) % len(poly)][1]
                if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                    inside = not inside
            if not inside:
                continue
            z = (self.ds[fi] - n[0] * x - n[1] * y) / n[2]
            if z <= p[2] + 64 and (best is None or z > best) and z > p[2] - 2048:
                best = z
        return best


def export(stem, assets, cache):
    path = os.path.join(assets, 'worlds', 'xeen', 'maps', stem + '.blv')
    if cache:
        os.makedirs(cache, exist_ok=True)
        out = os.path.join(cache, stem + '.json')
        if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(path):
            subprocess.run([OYMAP, 'export', path, '--world', 'xeen', '--assets', assets, '--out', out], check=True,
                           capture_output=True)
        return json.load(open(out))
    with tempfile.NamedTemporaryFile(suffix='.json') as t:
        subprocess.run([OYMAP, 'export', path, '--world', 'xeen', '--assets', assets, '--out', t.name], check=True,
                       capture_output=True)
        return json.load(open(t.name))


def marker_range(world, rows):
    """The notice range of a spawn marker: the widest of the rows its slot can roll (D-133: a slot counts by any of
    them); DETECT when the slot's rows are unknown."""
    if not rows:
        return DETECT, 'spawn'
    rng = max(RELATION_RANGE.get(world.relation_to_party(m), DETECT) for m in rows)
    return rng, 'spawn'


def hostiles(world, scene, fname=None, blv_spawns=()):
    """Placed actors, the BLV's spawn markers (`blv_spawns`: the export's `spawns`) and the scene's spawns."""
    out = []
    friendly = world.map_friendly(fname) if fname else set()
    for a in scene['initial_state'].get('actors') or []:
        if a.get('npc_id') or a['attributes'] & INVISIBLE_ACTOR or a.get('hp', 1) <= 0:
            continue
        mid = a.get('monster_info_id') or a['monster_id']
        if mid in friendly and not a['attributes'] & AGGRESSOR:   # friendly by the map's own load-time relations
            continue
        if a['attributes'] & AGGRESSOR:
            rng, why = DETECT, 'aggressor'
        else:
            rel = world.relation_to_party(mid)
            rng, why = RELATION_RANGE.get(rel, DETECT), 'relation %d' % rel
        if rng <= 0:
            continue
        p = a['position']
        out.append({'id': 'actor %d' % a['actor_index'], 'monster': mid, 'name': world.names.get(mid, '?'),
                    'group': a.get('group'), 'at': [p['x'], p['y'], p['z']], 'height': a.get('height') or 128,
                    'range': rng, 'why': why, 'count': 1, 'spread': 0, 'rows': [mid],
                    'immobile': bool(a.get('immobile'))})
    for k, s in enumerate(blv_spawns):   # the BLV's own monster markers (the export's `spawns`)
        if s.get('type_id') != 3:
            continue
        x, y, z = s['position']
        rows = world.slot_rows(fname, s.get('index') or 0)
        rng, why = marker_range(world, rows)
        if rng <= 0:
            continue
        out.append({'id': 'marker %d' % k, 'monster': s.get('index'), 'name': 'slot %s' % s.get('index'),
                    'group': s.get('group'), 'at': [x, y, z], 'height': 128, 'range': rng, 'why': why,
                    'count': 1, 'spread': s.get('radius') or 0, 'rows': rows, 'immobile': False})
    for s in scene.get('spawns') or []:
        if s.get('type_id') != 3:
            continue
        p = s['position']
        rows = world.slot_rows(fname, s.get('index') or 0)
        rng, why = marker_range(world, rows)
        if rng <= 0:
            continue
        out.append({'id': 'spawn %d' % s['spawn_index'], 'monster': s.get('index'), 'name': 'slot %s' % s.get('index'),
                    'group': s.get('group'), 'at': [p['x'], p['y'], p['z']], 'height': 128, 'range': rng,
                    'why': why, 'count': s.get('count', 1), 'spread': s.get('radius') or 0, 'rows': rows,
                    'immobile': False})
    return out


FIRST_FIGHT = OPEN_BUFFER


def first_fight(world, scene, fname, at, kept_groups=()):
    """D-15's first-fight buffer on an outdoor map, counting spawn markers (D-133): the hostiles that move or shoot
    (placed actors and the scene's spawns, as hostiles() reads them) within 2,000 (2D, less a marker's radius) of an
    arrival at `at`, nearest first. No line test: the outdoor checkers have no terrain (the open-air rule's clear line
    is left out, the stricter reading). Rows of `kept_groups` come back with kept=True."""
    out = []
    for h in hostiles(world, scene, fname):
        if h['immobile'] and not any(world.shoots(m) for m in h['rows']):
            continue
        d = math.dist(h['at'][:2], at[:2]) - h['spread']
        if d < FIRST_FIGHT:
            out.append(dict(h, distance=round(d), kept=h.get('group') in kept_groups and h['id'].startswith('actor')))
    return sorted(out, key=lambda r: r['distance'])


def sees(geo, h, at):
    """A clear line between monster h and the party at `at` (either of the engine's two rays), or None."""
    offsets = [(0.0, 0.0)]
    if h['spread']:
        r = h['spread'] * 0.7
        offsets += [(r, 0), (-r, 0), (0, r), (0, -r)]
    for dx, dy in offsets:
        base = np.array([h['at'][0] + dx, h['at'][1] + dy, h['at'][2]], float)
        eye = base + [0, 0, max(24.0, h['height'] * 0.9)]
        chest = base + [0, 0, max(24.0, h['height'] * 0.75)]
        if not geo.blocked(eye, [at[0], at[1], at[2] + PARTY_EYE]) or \
                not geo.blocked(chest, [at[0], at[1], at[2] + PARTY_BODY]):
            return True
    return False


def exits_of(world, stem, geo, data):
    """target map -> [(event id, point)]: the faces (and decorations) whose event leaves for that map."""
    text = world.luas.get(os.path.join(world.xeen, 'events', 'maps', stem + '.lua'), '')
    leaving = {}
    for eid, block in events_of(text).items():
        for m in MOVE.finditer(block):
            target = m.group(5)
            if target and target not in ('0', stem + '.blv'):
                leaving.setdefault(eid, set()).add(os.path.splitext(target)[0])
    out = {}
    for i, f in enumerate(geo.faces):
        for target in leaving.get(f.get('cog_triggered'), ()):
            centre = geo.vertices[f['vertices']].mean(0)
            out.setdefault(target, []).append((f['cog_triggered'], centre, i))
    for e in data['map'].get('entities') or []:
        for eid in (e.get('event_id_primary'), e.get('event_id_secondary')):
            for target in leaving.get(eid, ()):
                out.setdefault(target, []).append((eid, np.array(e['position'], float), None))
    return out


def exit_visible(geo, eye, eid, centre, fi):
    """A clear line from the party's eye to the exit's centre or any of its corners pulled a quarter inward (the
    faces of the exit's own event never block)."""
    own = {i for i, f in enumerate(geo.faces) if f.get('cog_triggered') == eid} | geo.door_faces
    points = [np.asarray(centre, float)]
    if fi is not None:
        poly = geo.vertices[geo.faces[fi]['vertices']]
        points += [centre + 0.75 * (v - centre) for v in poly]
    return any(not geo.blocked(eye, q, skip=own) for q in points)


def check_map(world, stem, cache):
    scene = load_yaml(os.path.join(world.xeen, 'maps', stem + '.scene.yml'))
    data = export(stem, world.assets, cache)
    geo = Geometry(data)
    geo.door_faces = {fi for d in scene['initial_state'].get('doors') or [] for fi in d.get('face_ids') or []}
    hs = hostiles(world, scene, stem + '.blv', data['map'].get('spawns') or [])
    open_air = stem in OPEN_AIR
    exits = exits_of(world, stem, geo, data)
    results = []
    for arr in arrivals(world, stem, scene):
        at = arr['at']
        floor = geo.floor_below(at)
        ground = [at[0], at[1], floor if floor is not None else at[2]]
        rows = []
        for h in hs:
            d = math.dist(h['at'], ground)
            if d - h['spread'] > DETECT:
                continue
            seen = d - h['spread'] <= h['range'] and sees(geo, h, ground)
            rows.append(dict(h, distance=round(d), sees=seen))
        rows.sort(key=lambda r: r['distance'])
        flags = []
        hot = [r for r in rows if r['sees']]
        near = [r for r in rows if not r['sees'] and r['distance'] - r['spread'] <= NEAR]
        within = all(label.startswith('move within') for label in arr['labels'])
        open_hot, disablers = [], []
        if open_air:
            for h in hs:
                d2 = math.dist(h['at'][:2], ground[:2]) - h['spread']
                if d2 > DISABLER_RANGE:
                    continue
                why = [world.disabler(m) for m in h['rows']]
                if any(why):
                    disablers.append(dict(h, distance=round(d2), reason='; '.join(
                        '%s %s' % (world.names.get(m, '?'), w) for m, w in zip(h['rows'], why) if w)))
                moves = not h['immobile'] or any(world.shoots(m) for m in h['rows'])
                if d2 <= OPEN_BUFFER and moves and sees(geo, h, ground):
                    open_hot.append(dict(h, distance=round(d2), sees=True))
            if open_hot:
                flags.append('arrival.open_hot')
            if disablers:
                flags.append('arrival.disabler')
            if hot:
                flags.append('arrival.open_seen')
        elif hot:
            flags.append('arrival.hot_within' if within else 'arrival.hot')
        if near:
            flags.append('arrival.near')
        # depth: the exit back to the map the party came from, else (party start) any exit
        depth = None
        targets = arr['from'] if arr['from'] else (list(exits) if arr['labels'][0] == 'party start' else [])
        cands = [(math.dist(c, [ground[0], ground[1], ground[2] + PARTY_BODY]), eid, t, c, fi)
                 for t in targets for eid, c, fi in exits.get(t, [])]
        if cands:
            d, eid, t, c, fi = min(cands, key=lambda q: q[0])
            visible = exit_visible(geo, [ground[0], ground[1], ground[2] + PARTY_EYE], eid, c, fi)
            depth = {'exit_to': t, 'event': eid, 'exit_at': [round(v) for v in c], 'distance': round(d),
                     'visible': visible}
            if d > DEEP or not visible:
                flags.append('arrival.deep')
        elif arr['from']:
            depth = {'exit_to': None, 'note': 'no exit back to %s' % '/'.join(arr['from'])}
        results.append({'map': stem, 'labels': arr['labels'], 'at': [round(v) for v in at],
                        'floor_z': None if floor is None else round(floor), 'facing_deg': arr['facing_deg'],
                        'from': arr['from'], 'flags': flags, 'nearest': rows[0] if rows else None,
                        'hot': hot, 'near': near, 'hostiles_within_5120': len(rows), 'depth': depth,
                        'open_hot': open_hot, 'disablers': disablers, 'open_air': open_air,
                        'defined': world.find_sources(round(at[0]), round(at[1]), [stem] + arr['from']) if flags else []})
    return results


def describe(r):
    lines = []
    head = '%s %s at (%d, %d, %d)%s [%s]' % (
        ','.join(r['flags']) or 'ok', r['map'], *r['at'],
        '' if r['facing_deg'] is None else ' facing %.0f' % r['facing_deg'], '; '.join(r['labels']))
    lines.append(head)
    n = r['nearest']
    if n:
        lines.append('    nearest hostile %s %s (%d) at (%d, %d, %d) %d%s; %d within 5,120, %d notice the party' % (
            n['id'], n['name'], n['monster'], *n['at'], n['distance'], ' seen' if n['sees'] else '',
            r['hostiles_within_5120'], len(r['hot'])))
    for h in r.get('open_hot') or []:
        lines.append('    within %d, seen, moves or shoots: %s %s group %s at (%d, %d, %d) %d (2D)' % (
            OPEN_BUFFER, h['id'], h['name'], h['group'], *h['at'], h['distance']))
    for h in r.get('disablers') or []:
        lines.append('    ranged disabler within %d: %s %s group %s at (%d, %d, %d) %d (2D): %s' % (
            DISABLER_RANGE, h['id'], h['name'], h['group'], *h['at'], h['distance'], h['reason']))
    for h in r['hot']:
        lines.append('    sees: %s %s group %s at (%d, %d, %d) %d (%s, range %d)' % (
            h['id'], h['name'], h['group'], *h['at'], h['distance'], h['why'], h['range']))
    for h in r['near']:
        lines.append('    near, no line: %s %s group %s at (%d, %d, %d) %d' % (
            h['id'], h['name'], h['group'], *h['at'], h['distance']))
    d = r['depth']
    if d and d.get('exit_to'):
        lines.append('    exit to %s (event %d) at (%d, %d, %d): %d%s' % (
            d['exit_to'], d['event'], *d['exit_at'], d['distance'], '' if d['visible'] else ', not in sight'))
    elif d:
        lines.append('    ' + d['note'])
    for s in r['defined'][:8]:
        lines.append('    defined: ' + s)
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--maps', nargs='+')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--assets', default=os.path.join(ROOT, 'assets_dev'))
    ap.add_argument('--cache', help='directory to keep the oymap exports in (reused while newer than the BLV)')
    ap.add_argument('--verbose', action='store_true', help='also print arrivals with no flag')
    args = ap.parse_args()
    world = World(os.path.abspath(args.assets))
    if args.maps:
        stems = [m if m.startswith('xeen_') else 'xeen_' + m for m in args.maps]
    else:
        stems = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(world.xeen, 'maps', 'xeen_*.blv'))
                       if os.path.exists(p[:-4] + '.scene.yml'))
    results = []
    for stem in stems:
        results += check_map(world, stem, args.cache)
    error_flags = {'arrival.hot', 'arrival.open_hot', 'arrival.disabler'}
    errors = sum(bool(set(r['flags']) & error_flags) for r in results)
    warnings = sum(bool(set(r['flags']) - error_flags) for r in results)
    counts = {}
    for r in results:
        for flag in r['flags']:
            counts[flag] = counts.get(flag, 0) + 1
    if args.json:
        print(json.dumps(results, indent=1, default=float))
    else:
        for r in results:
            if r['flags'] or args.verbose:
                print(describe(r))
        print('%d maps, %d arrivals, %d with errors, %d with warnings; %s' % (
            len(stems), len(results), errors, warnings, ', '.join('%s %d' % kv for kv in sorted(counts.items()))))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
