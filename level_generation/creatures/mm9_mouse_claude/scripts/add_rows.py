#!/usr/bin/env python3
"""Append the mouse rows to mm9_npc_actor_rows.tsv (run under the shared flock; temp + rename, other rows untouched)."""
import os, tempfile
from pathlib import Path
P = Path('tools/mm9_import_discovery/mm9_npc_actor_rows.tsv')
rows = {'299': ('472', 'mouse (mouse.abc, mouse1.dtx is not in the game data; cat.scr, Hostility 2): ambient animal, MM6-MM8 zrat A as the fallback visual; 3D model mm9_mouse, skin mouse_a'),
        '300': ('474', 'evil mouse (mouse.abc, mouse3.dtx is not in the game data; cat.scr, Hostility 2): ambient animal, MM6-MM8 zrat C as the fallback visual; 3D model mm9_mouse, skin mouse_c')}
text = P.read_text()
have = {l.split('\t')[0] for l in text.splitlines()}
add = ''.join(f'{k}\t{a}\t{n}\n' for k, (a, n) in rows.items() if k not in have)
if not text.endswith('\n'):
    text += '\n'
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.rows.', suffix='.tsv')
with os.fdopen(fd, 'w') as f:
    f.write(text + add)
os.chmod(tmp, os.stat(P).st_mode)
os.replace(tmp, P)
print('added', add.count('\n'))
