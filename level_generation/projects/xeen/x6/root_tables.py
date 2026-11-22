#!/usr/bin/env python3
"""X6's scratch root tables (A5, 2026-11-20): map_stats.txt with X6's stand-in row 9104 from project.yml (until A2's
row exists) and edge_spans.yml with X6's two edges both ways (until the orchestrator's maps.yml and X4/X5 open them).
Each file is unlinked and written new, so assets_dev's hard-linked inode is never written. Usage: root_tables.py <root>"""
import os
import sys

import yaml

R = sys.argv[1]
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
d = os.path.join(R, 'worlds/xeen/data_tables')
assert os.path.realpath(R).startswith(os.path.join(ROOT, 'output/studio_cal/x6/'))
pr = yaml.safe_load(open(os.path.join(ROOT, 'devdocs/xeen/briefs/x6/L4/project.yml')))
ms = pr['map_stats']
sl = ms['slots']
ROW = '\t'.join(str(v) for v in [
    ms['id'], pr['name'], 'xeen_x6.odm', 0, 0, ms['treasure_level'], ms['refill_days'], 0, 0, ms['lock_difficulty'],
    ms['trap_dice'], ms['perception_difficulty'], ms['encounter_chance'], sl[0]['weight'], sl[1]['weight'],
    sl[2]['weight'],
    sl[0]['monster'], sl[0]['monster'], sl[0]['tier'], ' %d-%d' % tuple(sl[0]['per_marker']),
    sl[1]['monster'], sl[1]['monster'], sl[1]['tier'], ' %d-%d' % tuple(sl[1]['per_marker']),
    sl[2]['monster'], sl[2]['monster'], sl[2]['tier'], ' %d-%d' % tuple(sl[2]['per_marker']),
    ms['music'], 'DESERT', 'map_studio', 0, 0, '-', ''])


def rewrite(name, fix):
    path = os.path.join(d, name)
    text = open(path, encoding='latin-1').read()
    new = fix(text)
    if new == text:
        return
    os.remove(path)
    with open(path, 'w', encoding='latin-1') as f:
        f.write(new)


rewrite('map_stats.txt', lambda t: t if '\txeen_x6.odm\t' in t else t.rstrip('\n') + '\n' + ROW + '\n')
n = {x['id']: x for x in pr['neighbours']}
e, s = n['edge:east'], n['edge:south']
F = {0: 0, 90: 512, 180: 1024, 270: 1536}
SPANS = [
    "  - {map: xeen_x6.odm, edge: east, from: -32768, to: 32768, to_map: xeen_x4.odm, side: right, days: 5, "
    "at: %s, facing: %d}" % (e['arrival'], F[e['direction']]),
    "  - {map: xeen_x6.odm, edge: south, from: -32768, to: 32768, to_map: xeen_x5.odm, side: up, days: 5, "
    "at: %s, facing: %d}" % (s['arrival'], F[s['direction']]),
    "  - {map: xeen_x4.odm, edge: west, from: -32768, to: 32768, to_map: xeen_x6.odm, side: left, days: 5, "
    "at: [22016, 2048, %d], facing: 1024}" % int(sys.argv[2] if len(sys.argv) > 2 else 1216),
    "  - {map: xeen_x5.odm, edge: north, from: -32768, to: 32768, to_map: xeen_x6.odm, side: down, days: 5, "
    "at: [-7168, -22016, %d], facing: 512}" % int(sys.argv[3] if len(sys.argv) > 3 else 1472),
]
rewrite('edge_spans.yml', lambda t: t if 'map: xeen_x6.odm' in t else t.rstrip('\n') + '\n' + '\n'.join(SPANS) + '\n')


def travel(t):
    out = []
    for line in t.rstrip('\n').split('\n'):
        c = line.split('\t')
        if c[0] == 'xeen_x4.odm' and len(c) > 9 and not c[7]:
            c[7:10] = ['xeen_x6.odm', 'left', '5']
            line = '\t'.join(c)
        if c[0] == 'xeen_x5.odm' and len(c) > 3 and not c[1]:
            c[1:4] = ['xeen_x6.odm', 'down', '5']
            line = '\t'.join(c)
        out.append(line)
    if not any(l.startswith('xeen_x6.odm\t') for l in out):
        out.append('\t'.join(['xeen_x6.odm', '', '', '', 'xeen_x5.odm', 'up', '5', '', '', '', 'xeen_x4.odm', 'right',
                              '5', '', pr['name'], '', '', '', '', '']))
    return '\n'.join(out) + '\n'


rewrite('outdoor_travels.txt', travel)
print('root tables: map_stats row 9104, edge_spans X6<->X4, X6<->X5')
