#!/usr/bin/env python3
"""Insert (or replace) this creature's marked block in assets_dev/worlds/mm9/models/actors.yml. Run under
`flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock`; writes a temp file and os.replace()s it
(assets_dev is hard-linked into output/ mirrors: never write in place). Usage: install_binding.py <block.yml> <marker>"""
import os, sys, tempfile
from pathlib import Path
import yaml
block, marker = Path(sys.argv[1]).read_text(), sys.argv[2]
target = Path(__file__).resolve().parents[4] / 'assets_dev' / 'worlds' / 'mm9' / 'models' / 'actors.yml'
text = target.read_text()
start, end = f'# >>> {marker}\n', f'# <<< {marker}\n'
if start in text:
    a = text.index(start); b = text.index(end) + len(end)
    text = text[:a] + block + text[b:]
else:
    text = text.rstrip('\n') + '\n' + block
names = [a['descriptor'] for a in yaml.safe_load(text)['actors']]
dups = {n for n in names if names.count(n) > 1}
assert not dups, dups
fd, tmp = tempfile.mkstemp(dir=target.parent, prefix='.actors.', suffix='.yml')
with os.fdopen(fd, 'w') as f:
    f.write(text)
os.chmod(tmp, os.stat(target).st_mode & 0o777)
os.replace(tmp, target)
print('bound', marker, len(names), 'descriptors in', target)
