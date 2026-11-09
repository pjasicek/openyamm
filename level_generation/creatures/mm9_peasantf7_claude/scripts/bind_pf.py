#!/usr/bin/env python3
"""Bind a PeasantF body project: add its rows to mm9_npc_actor_rows.tsv (re-read; only if missing), regenerate the MM9 tables, write its actors.yml
block (replaced if present). Temp + rename. Run ONLY under the flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, repo root.
Args: <config json>  {"project": .., "model": .., "intro": [lines], "rows": [[row, legacy, role, skin, label, tsv note], ...]}"""
import json, os, subprocess, sys, tempfile
C = json.load(open(sys.argv[1]))
t = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
text = open(t).read(); have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
add = [f'{r[0]}\t{r[1]}\t{r[5]}' for r in C['rows'] if str(r[0]) not in have]
if add:
    if not text.endswith('\n'): text += '\n'
    text += '\n'.join(add) + '\n'
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(t), prefix='.npc_rows.', suffix='.tsv')
    with os.fdopen(fd, 'w') as f: f.write(text)
    os.chmod(tmp, 0o644); os.replace(tmp, t)
print('rows added', len(add))
print(subprocess.run([sys.executable, 'tools/mm9_import_discovery/generate_mm9_monster_tables.py'], capture_output=True, text=True).stdout[-400:])
p = 'assets_dev/worlds/mm9/models/actors.yml'; s = open(p).read()
BEGIN = f"# >>> {C['project']}"; END = f"# <<< {C['project']}"
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + '\n' + ''.join('# ' + l + '\n' for l in C['intro'])
for row, legacy, role, skin, label, note in C['rows']:
    BLOCK += f"""# {label}
- descriptor: MM9 {row} {role}
  model: worlds/mm9/models/{C['model']}
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.0
    run_stride_length: 1.6
    look: {{nodes: [FHP Neck, FHP Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    events:
      attack_melee: {{impact: 1.0}}
      attack_ranged: {{impact: 1.0}}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Fidget
    attack_ranged: Fidget
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  script_clips:
    talk: Talk
    cower: Cower
    conv1: Conv1
    conv2: Talk
    conv3: Conv3
    stand: Standing
  skin: {skin}
"""
BLOCK += END + '\n'
tmp = p + '.tmp_' + C['project']; open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.chmod(tmp, os.stat(p).st_mode & 0o777); os.replace(tmp, p)
print('BOUND', [f"MM9 {r[0]} {r[2]}" for r in C['rows']])
