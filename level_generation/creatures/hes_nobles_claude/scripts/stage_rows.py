#!/usr/bin/env python3
"""Put the Nobles' rows into level_generation/projects/hesper_stage/monsters.yml (re-read right before writing; only
these rows and this project's `models:` lines change; the result is parse-checked). Each row keeps its picture, tactics
and comments; its reference becomes the flying demon (sounds, hit material, sprite fallback), its height and radius
the model's at the row's scale, its binding this project's integration/actors.yml entry.
Args: <row id> [<row id> ...] (default: every row in ROWS)"""
import re, sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[4]
STAGE = ROOT / 'level_generation/projects/hesper_stage/monsters.yml'
FROM = 'level_generation/creatures/hes_nobles_claude/integration/actors.yml'
EXPORT = 'level_generation/creatures/hes_nobles_claude/export'
MODELS = ['hes_noble.glb', 'hes_noble_fang.glb', 'hes_noble_sidearm.glb', 'hes_ssekh_fang_r.glb', 'hes_ssekh_fang_l.glb',
          'hes_mraal_cleaver.glb', 'hes_xith_storm_rifle.glb', 'hes_gate_carbine.glb', 'hes_gate_emitter.glb',
          'hes_gate_gorget.glb']
# id: (entry, reference, height, radius)
# height/radius stay the rows' earlier 218/60: the built maps froze those sizes into their placements (check_actor_sizes;
# 220-264 made 34 placed Nobles stale, batch C walkability report 2026-10-24); the model scale is separate
ROWS = {10040: ('Noble A', 'DemonFly A', 218, 60), 10041: ('Noble B', 'DemonFly B', 218, 60),
        10042: ('Noble C', 'DemonFly C', 218, 60), 10112: ('The Gatekeeper', 'DemonFly C', 218, 60),
        10113: ('Lady Ssekh', 'DemonFly C', 218, 60), 10114: ('Lord Mraal', 'DemonFly C', 218, 60),
        10115: ('Lord Xith', 'DemonFly C', 218, 60)}
ids = [int(x) for x in sys.argv[1:]] or list(ROWS)
text = STAGE.read_text()
lines = text.split('\n')
# models: one line per installed file, after the last existing hes_noble line or before the first blank after models:
start = lines.index('models:')
end = next(i for i in range(start + 1, len(lines)) if not lines[i].startswith('  '))
for m in MODELS:
    line = f'  {m}: {EXPORT}/{m}'
    if not any(l.startswith(f'  {m}:') for l in lines[start:end]):
        lines.insert(end, line); end += 1
for rid in ids:
    entry, ref, h, r = ROWS[rid]
    i = next(k for k, l in enumerate(lines) if re.match(rf'\s+- \{{id: {rid},', l) or re.match(rf'\s+- \{{.*\bid: {rid}\b', l))
    j = i + 1
    while j < len(lines) and lines[j].startswith('     ') and not lines[j].lstrip().startswith('- '):
        j += 1
    old = next(m for m in yaml.safe_load(text)['monsters'] if m['id'] == rid)
    row = {'id': rid}
    if old.get('picture'): row['picture'] = old['picture']
    row.update({'reference': ref, 'height': h, 'radius': r, 'binding': {'from': FROM, 'entry': entry}})
    if old.get('tactics'): row['tactics'] = old['tactics']
    for k in old:
        if k not in row and k != 'binding': row[k] = old[k]
    flow = yaml.safe_dump(row, default_flow_style=True, sort_keys=False, width=110).strip()
    new = ['  - ' + flow.split('\n')[0]] + ['      ' + x.strip() for x in flow.split('\n')[1:]]
    lines[i:j] = new
    print('ROW', rid, '->', entry)
out = '\n'.join(lines)
yaml.safe_load(out)
STAGE.write_text(out)
print('STAGED rows', ids)
PLAN = None
