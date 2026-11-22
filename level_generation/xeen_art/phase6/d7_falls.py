#!/usr/bin/env python3
"""D7's proposed fall landings on the six Darkside maps, checked against their installed scenes (A6 sub-agent,
2026-11-21). Read-only: it reads assets_dev/worlds/xeen/maps/xeen_dN.scene.yml and writes d7/falls.json.

For each landing: the nearest monster actor (and its row), spawn marker and decoration, and the nearest named arrival.
The ground height, the whole cell and water/lava are the map owner's checks at install (requests).
"""
import json
import math
import re
from pathlib import Path

import d7_design as D

ROOT = Path(__file__).resolve().parents[3]
MAPS = ROOT / 'assets_dev/worlds/xeen/maps'
OUT = Path(__file__).resolve().parent / 'd7' / 'falls.json'
POS = re.compile(r'position:\s*\n\s*x: (-?\d+)\s*\n\s*y: (-?\d+)\s*\n\s*z: (-?\d+)')


def section(text, start, end):
    a = text.find(start)
    if a < 0:
        return ''
    b = text.find(end, a + len(start)) if end else -1
    return text[a:b if b > 0 else len(text)]


def main():
    out = []
    for f in D.FALLS:
        stem = f['map'].replace('.odm', '')
        text = (MAPS / f'{stem}.scene.yml').read_text()
        lx, ly, lz = f['landing']
        actors_txt = section(text, '\n  actors:', '\n  chests:')
        actors = []
        for block in actors_txt.split('\n    - actor_index:')[1:]:
            m = POS.search(block)
            mid = re.search(r'monster_id: (\d+)', block)
            hos = re.search(r'hostility_type: (\d+)', block)
            if m:
                actors.append((int(m.group(1)), int(m.group(2)), int(mid.group(1)) if mid else 0))
        ents = [(int(a), int(b)) for a, b, c in POS.findall(section(text, '\nentities:', '\nspawns:'))]
        spawns = [(int(a), int(b)) for a, b, c in POS.findall(section(text, '\nspawns:', '\ninitial_state:'))]
        arr = []
        studio = (MAPS / f'{stem}.studio.yml').read_text()
        for m in re.finditer(r'\{name: "([^"]+)", at: \[(-?\d+), (-?\d+), (-?\d+)\]', studio):
            arr.append((m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))))

        def near(items):
            if not items:
                return None
            d, it = min((math.hypot(i[0] - lx, i[1] - ly), i) for i in items)
            return round(d), it
        a = near(actors)
        out.append(dict(zone=f['id'], map=f['map'], owner=f['owner'], landing=f['landing'], facing=f['facing'],
                        near=f['near'],
                        nearest_actor=dict(distance=a[0], monster=a[1][2]) if a else None,
                        actors_within_3072=sum(1 for x in actors if math.hypot(x[0] - lx, x[1] - ly) <= 3072),
                        nearest_spawn=near(spawns)[0] if spawns else None,
                        nearest_decoration=near(ents)[0] if ents else None,
                        nearest_arrival=(lambda r: dict(name=r[1][0], distance=r[0], z=r[1][3]))(
                            min((math.hypot(x[1] - lx, x[2] - ly), x) for x in arr))))
    OUT.write_text(json.dumps(out, indent=1))
    for o in out:
        print(o['zone'], o['landing'], 'actor', o['nearest_actor'], 'n3072', o['actors_within_3072'], 'spawn',
              o['nearest_spawn'], 'deco', o['nearest_decoration'], 'arr', o['nearest_arrival'])


if __name__ == '__main__':
    main()
