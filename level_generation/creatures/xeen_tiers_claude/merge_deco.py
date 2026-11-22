#!/usr/bin/env python3
"""Lane S: merge a project's indoor decoration binding fragment into the Xeen world's indoor_decorations.yml and set
the rows' radius/height in decoration_data.txt (temp file + rename: scratch roots hard-link these files).
Usage: merge_deco.py <fragment.yml> [<name>=<radius>/<height> ...]
The fragment is appended as text (its comments kept); a name already bound is refused."""
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
W = REPO / 'assets_dev/worlds/xeen/models'


def write(path, text):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(text)
    os.replace(tmp, path)


frag = Path(sys.argv[1]).read_text()
ind_path = W / 'indoor_decorations.yml'
ind = ind_path.read_text()
names = re.findall(r'^\s*- name: (\S+)', frag, re.M)
for name in names:
    if re.search(rf'^\s*- name: {re.escape(name)}\s*$', ind, re.M):
        sys.exit(f'already bound: {name}')
body = '\n'.join(('  ' + l if l.startswith('#') else l) for l in frag.splitlines()
                 if 'lane S merges' not in l and 'do not mount' not in l)
write(ind_path, ind.rstrip('\n') + '\n' + body.rstrip('\n') + '\n')
rows_path = W / 'decoration_data.txt'
rows = rows_path.read_text().splitlines(keepends=True)
for arg in sys.argv[2:]:
    name, dims = arg.split('=')
    radius, height = dims.split('/')
    hits = [i for i, l in enumerate(rows) if l.split('\t')[1:2] == [name]]
    if len(hits) != 1:
        sys.exit(f'row not found once: {name}')
    cols = rows[hits[0]].rstrip('\n').split('\t')
    cols[4], cols[5] = radius, height
    rows[hits[0]] = '\t'.join(cols) + '\n'
write(rows_path, ''.join(rows))
print('bound', ', '.join(names))
