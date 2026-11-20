#!/usr/bin/env python3
"""Read-only census of MM6-MM8 BLV dungeons: loops, secrets, traps, teleports, levers, bosses."""
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file

SECRET, PLATE, CLICK = 2, 0x04000000, 0x02000000
out = []
for world in ('mm6', 'mm7', 'mm8'):
    for mp in sorted((ROOT / 'assets_dev/worlds' / world / 'maps').glob('*.blv')):
        stem = mp.stem
        try:
            p = parse_blv_file(mp)['payload']
        except Exception as ex:
            print('skip', stem, ex, file=sys.stderr)
            continue
        sp = mp.with_suffix('.scene.yml')
        scene = yaml.load(sp.read_text(), Loader=yaml.CSafeLoader) if sp.exists() else {'initial_state': {}}
        lp = ROOT / 'assets_dev/worlds' / world / 'events/maps' / (stem + '.lua')
        text = lp.read_text(encoding='latin-1') if lp.exists() else ''
        regs = list(re.finditer(r'^Register(?:NoOp)?Event\((\d+),', text, re.M))
        blocks = {}
        for i, m in enumerate(regs):
            blocks[int(m[1])] = text[m.start(): regs[i + 1].start() if i + 1 < len(regs) else len(text)]
        faces = p['faces']
        edges = set()
        occupied = set()
        for f in faces:
            if f['room_number']:
                occupied.add(f['room_number'])
            if f['is_portal'] and f['room_number'] and f['room_behind_number']:
                edges.add(tuple(sorted((f['room_number'], f['room_behind_number']))))
        # components
        parent = {s: s for s in occupied}
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]; x = parent[x]
            return x
        for a, b in edges:
            if a in parent and b in parent:
                parent[find(a)] = find(b)
        comps = len({find(s) for s in occupied}) if occupied else 0
        cyclomatic = len(edges) - len(occupied) + comps
        bound = Counter()
        for f in faces:
            ev = (f.get('face_param') or {}).get('cog_triggered', 0)
            if ev:
                bound[ev] += 1
        for e in p['entities']:
            if e.get('event_id_secondary'):
                bound[e['event_id_secondary']] += 1
        trap = tele = lever = summon = msg = 0
        for ev in bound:
            b = blocks.get(ev, '')
            if re.search(r'evt\.(DamagePlayer|CastSpell)\(', b):
                trap += 1
            if re.search(r'evt\.MoveToMap\(', b) and not re.search(r'\.(blv|odm)"', b):
                tele += 1
            elif re.search(r'evt\.MoveToMap\([^)]*"' + re.escape(stem) + r'\.blv"', b, re.I):
                tele += 1
            if 'evt.SetDoorState' in b:
                lever += 1
            if 'SummonMonsters' in b:
                summon += 1
        state = scene.get('initial_state', {})
        actors = state.get('actors', []) or []
        uniques = sum(1 for a in actors if a.get('unique_name_index'))
        spawns = [s for s in p['spawns'] if s.get('type_id', 3) == 3]
        floorz = [v['z'] for v in p['vertices']]
        out.append({'world': world, 'map': stem, 'sectors': len(occupied), 'portal_links': len(edges),
                    'loops': cyclomatic, 'secret_faces': sum(1 for f in faces if f['attributes'] & SECRET),
                    'plates': sum(1 for f in faces if f['attributes'] & PLATE),
                    'clickable': sum(1 for f in faces if f['attributes'] & CLICK),
                    'trap_events': trap, 'local_teleports': tele, 'door_events': lever, 'summon_events': summon,
                    'doors': p.get('door_count', 0), 'lights': p.get('light_count', 0),
                    'decorations': len(p['entities']), 'spawn_markers': len(spawns), 'fixed_actors': len(actors),
                    'unique_actors': uniques, 'chests_bound': len(set(map(int, re.findall(r'evt\.OpenChest\((\d+)', text)))),
                    'z_range': max(floorz) - min(floorz) if floorz else 0})
json.dump(out, open(Path(__file__).with_name('indoor_census.json'), 'w'), indent=1)
print(len(out))
