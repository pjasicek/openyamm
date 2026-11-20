#!/usr/bin/env python3
"""README result rows from work/<id>/gate.json. Usage: summary.py <id> [<id> ...]"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

print('| Id | Layers LOD0 | LOD1 | LOD2 | Triangles before | after (shell) | Coverage LOD0/1/2 | Colour LOD0/1/2 |')
print('|---|---|---|---|---|---|---|---|')
for tid in sys.argv[1:]:
    g = json.load(open(os.path.join(common.HERE, 'work', tid, 'gate.json')))
    L = g['layers']; T = g['tris']
    lay = [f"{L['inst'][str(l)]['all']:.2f} ({L['inst'][str(l)]['front']:.2f}) -> {L['new'][str(l)]['all']:.2f} "
           f"({L['new'][str(l)]['front']:.2f})" for l in range(3)]
    tb = ' / '.join(str(sum(t.values())) for t in T['inst'])
    ta = ' / '.join(f"{sum(t.values())}" + (f" ({t['Shell']})" if 'Shell' in t else '') for t in T['new'])
    cov = ' / '.join(f"{g['gates'][f'LOD{l}']['coverage'] * 100:+.1f} %" for l in range(3))
    col = ' / '.join(f"{g['gates'][f'LOD{l}']['colour_max']:.1f}" for l in range(3))
    print(f"| {tid} | {lay[0]} | {lay[1]} | {lay[2]} | {tb} | {ta} | {cov} | {col} |")
